"""
MQTT Handler

Manages MQTT connectivity, message routing, and publishing for the wine production
monitoring system. Features auto-reconnect, message buffering, and robust error handling.
"""

import paho.mqtt.client as mqtt
import json
import logging
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from collections import deque
from datetime import datetime
from queue import Queue, Empty


class MQTTHandler:
    """
    MQTT client with auto-reconnect and message buffering.

    Features:
    - Automatic reconnection with exponential backoff
    - Message buffering for offline resilience
    - Topic subscription management
    - Message validation and parsing
    - Health monitoring
    - Thread-safe operations
    """

    # Connection states
    STATE_DISCONNECTED = 0
    STATE_CONNECTING = 1
    STATE_CONNECTED = 2
    STATE_RECONNECTING = 3

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MQTT handler.

        Args:
            config: Configuration dictionary with MQTT settings:
                - broker: MQTT broker hostname/IP
                - port: MQTT broker port (default: 1883)
                - username: Optional username
                - password: Optional password
                - client_id: MQTT client ID (default: auto-generated)
                - keepalive: Keep-alive interval in seconds (default: 60)
                - qos: Quality of Service level (default: 1)
                - retain: Retain messages (default: False)
                - buffer_size: Max messages to buffer when offline (default: 1000)
        """
        self.config = config
        self.logger = logging.getLogger("mqtt_handler")

        # MQTT connection settings
        self.broker = config.get('broker', 'localhost')
        self.port = config.get('port', 1883)
        self.username = config.get('username')
        self.password = config.get('password')
        self.client_id = config.get('client_id', f'wine_monitor_{int(time.time())}')
        self.keepalive = config.get('keepalive', 60)
        self.qos = config.get('qos', 1)
        self.retain = config.get('retain', False)

        # Buffering for offline resilience
        self.buffer_size = config.get('buffer_size', 1000)
        self.publish_buffer: deque = deque(maxlen=self.buffer_size)
        self.buffer_lock = threading.Lock()

        # Message processing
        self.message_queue: Queue = Queue()
        self.message_callbacks: List[Callable] = []

        # Subscriptions
        self.subscriptions: Dict[str, int] = {}  # topic -> qos
        self.subscription_callbacks: Dict[str, List[Callable]] = {}  # topic -> callbacks

        # Connection state
        self.state = self.STATE_DISCONNECTED
        self.state_lock = threading.Lock()
        self.connected_event = threading.Event()

        # Reconnection settings
        self.reconnect_delay = config.get('reconnect_delay', 5)  # seconds
        self.reconnect_max_delay = config.get('reconnect_max_delay', 300)  # 5 minutes
        self.reconnect_exponential_backoff = config.get('reconnect_exponential_backoff', True)
        self.current_reconnect_delay = self.reconnect_delay

        # Statistics
        self.messages_received = 0
        self.messages_sent = 0
        self.messages_buffered = 0
        self.connection_attempts = 0
        self.last_connected = None
        self.last_disconnected = None
        self.uptime_start = None

        # Create MQTT client
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe
        self.client.on_publish = self._on_publish

        # Set username/password if provided
        if self.username:
            self.client.username_pw_set(self.username, self.password)

        # Worker threads
        self.message_processor_thread = None
        self.buffer_processor_thread = None
        self.running = False

        self.logger.info(f"Initialized MQTT handler (broker={self.broker}:{self.port}, client_id={self.client_id})")

    def connect(self, blocking: bool = False) -> bool:
        """
        Connect to MQTT broker.

        Args:
            blocking: If True, wait for connection to complete

        Returns:
            True if connection initiated successfully, False otherwise
        """
        with self.state_lock:
            if self.state == self.STATE_CONNECTED:
                self.logger.info("Already connected to MQTT broker")
                return True

            if self.state == self.STATE_CONNECTING:
                self.logger.info("Connection already in progress")
                if blocking:
                    return self.connected_event.wait(timeout=30)
                return True

            self.state = self.STATE_CONNECTING

        try:
            self.logger.info(f"Connecting to MQTT broker {self.broker}:{self.port}...")
            self.connection_attempts += 1

            self.client.connect_async(self.broker, self.port, self.keepalive)
            self.client.loop_start()

            if blocking:
                # Wait for connection with timeout
                if self.connected_event.wait(timeout=30):
                    return True
                else:
                    self.logger.error("Connection timeout")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Error connecting to MQTT broker: {e}", exc_info=True)
            with self.state_lock:
                self.state = self.STATE_DISCONNECTED
            return False

    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.logger.info("Disconnecting from MQTT broker...")
        self.running = False

        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}", exc_info=True)

        with self.state_lock:
            self.state = self.STATE_DISCONNECTED
        self.connected_event.clear()

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker."""
        if rc == 0:
            self.logger.info("Connected to MQTT broker successfully")

            with self.state_lock:
                self.state = self.STATE_CONNECTED
                self.last_connected = datetime.now()
                if self.uptime_start is None:
                    self.uptime_start = datetime.now()

            self.connected_event.set()
            self.current_reconnect_delay = self.reconnect_delay

            # Resubscribe to topics
            self._resubscribe()

            # Start worker threads
            if not self.running:
                self.running = True
                self._start_workers()

            # Process buffered messages
            self._process_buffer()

        else:
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized",
            }
            error_msg = error_messages.get(rc, f"Unknown error code: {rc}")
            self.logger.error(f"Failed to connect to MQTT broker: {error_msg}")

            with self.state_lock:
                self.state = self.STATE_DISCONNECTED
            self.connected_event.clear()

            # Attempt reconnection
            self._schedule_reconnect()

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker."""
        with self.state_lock:
            self.state = self.STATE_DISCONNECTED
            self.last_disconnected = datetime.now()

        self.connected_event.clear()

        if rc == 0:
            self.logger.info("Disconnected from MQTT broker (clean disconnect)")
        else:
            self.logger.warning(f"Unexpected disconnect from MQTT broker (code: {rc})")
            self._schedule_reconnect()

    def _on_message(self, client, userdata, msg):
        """Callback when message received."""
        self.messages_received += 1

        try:
            # Decode payload
            payload_str = msg.payload.decode('utf-8')

            # Parse JSON
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                # If not JSON, treat as plain text
                payload = {'value': payload_str}

            # Add to message queue for processing
            message_data = {
                'topic': msg.topic,
                'payload': payload,
                'qos': msg.qos,
                'retain': msg.retain,
                'timestamp': datetime.now().isoformat(),
            }

            self.message_queue.put(message_data)

            self.logger.debug(f"Received message on topic {msg.topic}")

        except Exception as e:
            self.logger.error(f"Error processing received message: {e}", exc_info=True)

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback when subscription confirmed."""
        self.logger.debug(f"Subscription confirmed (mid={mid}, qos={granted_qos})")

    def _on_publish(self, client, userdata, mid):
        """Callback when message published."""
        self.messages_sent += 1
        self.logger.debug(f"Message published (mid={mid})")

    def subscribe(self, topic: str, qos: Optional[int] = None, callback: Optional[Callable] = None):
        """
        Subscribe to MQTT topic.

        Args:
            topic: Topic pattern to subscribe to
            qos: Quality of Service level (default: from config)
            callback: Optional callback function for messages on this topic
        """
        if qos is None:
            qos = self.qos

        self.subscriptions[topic] = qos

        if callback:
            if topic not in self.subscription_callbacks:
                self.subscription_callbacks[topic] = []
            self.subscription_callbacks[topic].append(callback)

        if self.state == self.STATE_CONNECTED:
            try:
                result, mid = self.client.subscribe(topic, qos)
                if result == mqtt.MQTT_ERR_SUCCESS:
                    self.logger.info(f"Subscribed to topic: {topic} (qos={qos})")
                else:
                    self.logger.error(f"Failed to subscribe to topic {topic}: {result}")
            except Exception as e:
                self.logger.error(f"Error subscribing to topic {topic}: {e}", exc_info=True)
        else:
            self.logger.info(f"Queued subscription for topic: {topic} (will subscribe when connected)")

    def subscribe_multiple(self, topics: List[str], qos: Optional[int] = None):
        """
        Subscribe to multiple topics.

        Args:
            topics: List of topic patterns
            qos: Quality of Service level (default: from config)
        """
        for topic in topics:
            self.subscribe(topic, qos)

    def _resubscribe(self):
        """Resubscribe to all topics after reconnection."""
        if not self.subscriptions:
            return

        self.logger.info(f"Resubscribing to {len(self.subscriptions)} topics...")

        for topic, qos in self.subscriptions.items():
            try:
                self.client.subscribe(topic, qos)
            except Exception as e:
                self.logger.error(f"Error resubscribing to topic {topic}: {e}", exc_info=True)

    def publish(
        self,
        topic: str,
        payload: Any,
        qos: Optional[int] = None,
        retain: Optional[bool] = None,
        force_buffer: bool = False,
    ) -> bool:
        """
        Publish message to MQTT topic.

        Args:
            topic: Topic to publish to
            payload: Message payload (will be JSON encoded if dict/list)
            qos: Quality of Service level (default: from config)
            retain: Retain message (default: from config)
            force_buffer: Force message to buffer even if connected

        Returns:
            True if message sent/buffered successfully, False otherwise
        """
        if qos is None:
            qos = self.qos
        if retain is None:
            retain = self.retain

        # Convert payload to JSON if needed
        if isinstance(payload, (dict, list)):
            try:
                payload_str = json.dumps(payload)
            except Exception as e:
                self.logger.error(f"Error encoding payload to JSON: {e}", exc_info=True)
                return False
        else:
            payload_str = str(payload)

        # Buffer message if not connected or forced
        if self.state != self.STATE_CONNECTED or force_buffer:
            with self.buffer_lock:
                message = {
                    'topic': topic,
                    'payload': payload_str,
                    'qos': qos,
                    'retain': retain,
                    'timestamp': datetime.now().isoformat(),
                }
                self.publish_buffer.append(message)
                self.messages_buffered += 1

            self.logger.debug(f"Buffered message for topic {topic} (buffer size: {len(self.publish_buffer)})")
            return True

        # Publish immediately
        try:
            result = self.client.publish(topic, payload_str, qos, retain)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"Published message to topic: {topic}")
                return True
            else:
                self.logger.warning(f"Failed to publish to {topic}: {result.rc}, buffering message")

                # Buffer failed message
                with self.buffer_lock:
                    message = {
                        'topic': topic,
                        'payload': payload_str,
                        'qos': qos,
                        'retain': retain,
                        'timestamp': datetime.now().isoformat(),
                    }
                    self.publish_buffer.append(message)
                    self.messages_buffered += 1

                return False

        except Exception as e:
            self.logger.error(f"Error publishing message: {e}", exc_info=True)

            # Buffer failed message
            with self.buffer_lock:
                message = {
                    'topic': topic,
                    'payload': payload_str,
                    'qos': qos,
                    'retain': retain,
                    'timestamp': datetime.now().isoformat(),
                }
                self.publish_buffer.append(message)
                self.messages_buffered += 1

            return False

    def publish_sensor_data(self, sensor_id: str, data: Dict[str, Any]) -> bool:
        """
        Publish sensor data to standardized topic.

        Args:
            sensor_id: Sensor identifier
            data: Sensor data dictionary

        Returns:
            True if successful, False otherwise
        """
        topic = f"wine_monitor/sensors/{sensor_id}/data"
        return self.publish(topic, data)

    def publish_prediction(self, prediction: Dict[str, Any]) -> bool:
        """
        Publish ML prediction.

        Args:
            prediction: Prediction dictionary

        Returns:
            True if successful, False otherwise
        """
        topic = "wine_monitor/predictions"
        return self.publish(topic, prediction)

    def publish_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Publish alert.

        Args:
            alert: Alert dictionary

        Returns:
            True if successful, False otherwise
        """
        topic = f"wine_monitor/alerts/{alert.get('severity', 'info')}"
        return self.publish(topic, alert, retain=True)

    def publish_health(self, health: Dict[str, Any]) -> bool:
        """
        Publish system health status.

        Args:
            health: Health status dictionary

        Returns:
            True if successful, False otherwise
        """
        topic = "wine_monitor/health"
        return self.publish(topic, health, retain=True)

    def add_message_callback(self, callback: Callable):
        """
        Add global message callback.

        Args:
            callback: Function that takes (topic, payload) as arguments
        """
        self.message_callbacks.append(callback)
        self.logger.debug(f"Added message callback: {callback.__name__}")

    def _process_buffer(self):
        """Process buffered messages when connection restored."""
        with self.buffer_lock:
            buffer_size = len(self.publish_buffer)

            if buffer_size == 0:
                return

            self.logger.info(f"Processing {buffer_size} buffered messages...")

            failed_messages = []

            while self.publish_buffer:
                message = self.publish_buffer.popleft()

                try:
                    result = self.client.publish(
                        message['topic'],
                        message['payload'],
                        message['qos'],
                        message['retain']
                    )

                    if result.rc != mqtt.MQTT_ERR_SUCCESS:
                        failed_messages.append(message)

                except Exception as e:
                    self.logger.error(f"Error publishing buffered message: {e}", exc_info=True)
                    failed_messages.append(message)

            # Re-add failed messages to buffer
            for message in failed_messages:
                self.publish_buffer.append(message)

            processed = buffer_size - len(failed_messages)
            self.logger.info(f"Processed {processed}/{buffer_size} buffered messages")

    def _start_workers(self):
        """Start worker threads."""
        if self.message_processor_thread is None or not self.message_processor_thread.is_alive():
            self.message_processor_thread = threading.Thread(
                target=self._message_processor_worker,
                daemon=True,
                name="mqtt_message_processor"
            )
            self.message_processor_thread.start()
            self.logger.debug("Started message processor thread")

    def _message_processor_worker(self):
        """Worker thread for processing incoming messages."""
        self.logger.info("Message processor worker started")

        while self.running:
            try:
                # Get message from queue with timeout
                try:
                    message = self.message_queue.get(timeout=1.0)
                except Empty:
                    continue

                topic = message['topic']
                payload = message['payload']

                # Call global callbacks
                for callback in self.message_callbacks:
                    try:
                        callback(topic, payload)
                    except Exception as e:
                        self.logger.error(f"Error in message callback {callback.__name__}: {e}", exc_info=True)

                # Call topic-specific callbacks
                for topic_pattern, callbacks in self.subscription_callbacks.items():
                    # Simple wildcard matching
                    if self._topic_matches(topic, topic_pattern):
                        for callback in callbacks:
                            try:
                                callback(topic, payload)
                            except Exception as e:
                                self.logger.error(f"Error in topic callback: {e}", exc_info=True)

                self.message_queue.task_done()

            except Exception as e:
                self.logger.error(f"Error in message processor worker: {e}", exc_info=True)

        self.logger.info("Message processor worker stopped")

    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """
        Check if topic matches pattern (with MQTT wildcards).

        Args:
            topic: Actual topic
            pattern: Topic pattern with wildcards

        Returns:
            True if matches, False otherwise
        """
        # Exact match
        if topic == pattern:
            return True

        # Multi-level wildcard (#)
        if '#' in pattern:
            prefix = pattern.split('#')[0]
            return topic.startswith(prefix)

        # Single-level wildcard (+)
        if '+' in pattern:
            topic_parts = topic.split('/')
            pattern_parts = pattern.split('/')

            if len(topic_parts) != len(pattern_parts):
                return False

            return all(
                p == '+' or p == t
                for p, t in zip(pattern_parts, topic_parts)
            )

        return False

    def _schedule_reconnect(self):
        """Schedule reconnection attempt."""
        with self.state_lock:
            if self.state == self.STATE_RECONNECTING:
                return

            self.state = self.STATE_RECONNECTING

        threading.Thread(
            target=self._reconnect_worker,
            daemon=True,
            name="mqtt_reconnect"
        ).start()

    def _reconnect_worker(self):
        """Worker thread for reconnection attempts."""
        while self.state == self.STATE_RECONNECTING:
            self.logger.info(f"Reconnecting in {self.current_reconnect_delay} seconds...")
            time.sleep(self.current_reconnect_delay)

            # Attempt reconnection
            if self.connect(blocking=True):
                self.logger.info("Reconnected successfully")
                return

            # Increase delay with exponential backoff
            if self.reconnect_exponential_backoff:
                self.current_reconnect_delay = min(
                    self.current_reconnect_delay * 2,
                    self.reconnect_max_delay
                )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get MQTT handler statistics.

        Returns:
            Dictionary with statistics
        """
        uptime = None
        if self.uptime_start:
            uptime = (datetime.now() - self.uptime_start).total_seconds()

        time_since_connected = None
        if self.last_connected:
            time_since_connected = (datetime.now() - self.last_connected).total_seconds()

        return {
            'state': self._state_name(),
            'connected': self.state == self.STATE_CONNECTED,
            'broker': f"{self.broker}:{self.port}",
            'client_id': self.client_id,
            'messages_received': self.messages_received,
            'messages_sent': self.messages_sent,
            'messages_buffered': self.messages_buffered,
            'buffer_size': len(self.publish_buffer),
            'connection_attempts': self.connection_attempts,
            'subscriptions': len(self.subscriptions),
            'last_connected': self.last_connected.isoformat() if self.last_connected else None,
            'last_disconnected': self.last_disconnected.isoformat() if self.last_disconnected else None,
            'uptime_seconds': uptime,
            'time_since_connected_seconds': time_since_connected,
        }

    def _state_name(self) -> str:
        """Get human-readable state name."""
        states = {
            self.STATE_DISCONNECTED: 'disconnected',
            self.STATE_CONNECTING: 'connecting',
            self.STATE_CONNECTED: 'connected',
            self.STATE_RECONNECTING: 'reconnecting',
        }
        return states.get(self.state, 'unknown')

    def is_connected(self) -> bool:
        """
        Check if connected to broker.

        Returns:
            True if connected, False otherwise
        """
        return self.state == self.STATE_CONNECTED

    def wait_for_connection(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for connection to be established.

        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            True if connected, False if timeout
        """
        return self.connected_event.wait(timeout)
