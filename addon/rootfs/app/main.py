"""
Wine Fermentation Monitor - Main Service Orchestrator
Coordinates all monitoring, prediction, and alerting services
"""

import asyncio
import logging
import signal
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from threading import Thread, Event

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, Response
from pythonjsonlogger import jsonlogger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from config import load_config, Config, get_config_loader


# Global shutdown event
shutdown_event = Event()

# Service health status
service_health = {
    'status': 'starting',
    'mqtt_connected': False,
    'last_mqtt_message': None,
    'services_running': {},
    'startup_time': datetime.utcnow().isoformat(),
    'uptime_seconds': 0,
    'errors': []
}


class StructuredLogger:
    """Configure structured logging"""

    @staticmethod
    def setup(config: Config) -> logging.Logger:
        """
        Setup structured logging with proper formatting

        Args:
            config: Configuration object

        Returns:
            Configured logger
        """
        # Create root logger
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, config.logging.level.value))

        # Clear existing handlers
        logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, config.logging.level.value))

        if config.logging.structured:
            # JSON formatter for structured logging
            formatter = jsonlogger.JsonFormatter(
                '%(asctime)s %(name)s %(levelname)s %(message)s',
                timestamp=True
            )
        else:
            # Standard formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (if enabled)
        if config.logging.log_to_file:
            try:
                from logging.handlers import RotatingFileHandler

                # Ensure log directory exists
                Path(config.logging.log_file_path).parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                file_handler = RotatingFileHandler(
                    config.logging.log_file_path,
                    maxBytes=config.logging.max_log_size_mb * 1024 * 1024,
                    backupCount=config.logging.backup_count
                )
                file_handler.setLevel(getattr(logging, config.logging.level.value))
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

                logger.info(f"File logging enabled: {config.logging.log_file_path}")

            except Exception as e:
                logger.warning(f"Failed to setup file logging: {e}")

        return logger


class MQTTService:
    """MQTT connection and message handling service"""

    def __init__(self, config: Config):
        """
        Initialize MQTT service

        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__ + '.MQTTService')
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.reconnect_attempts = 0
        self.message_callbacks = []

    @retry(
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(Exception)
    )
    def connect(self):
        """Connect to MQTT broker with retry logic"""
        self.logger.info(
            f"Connecting to MQTT broker at "
            f"{self.config.mqtt.host}:{self.config.mqtt.port}"
        )

        try:
            # Create MQTT client
            self.client = mqtt.Client(
                client_id=f"wine_monitor_{int(time.time())}",
                clean_session=True
            )

            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            # Set authentication if configured
            if self.config.mqtt.username:
                self.client.username_pw_set(
                    self.config.mqtt.username,
                    self.config.mqtt.password
                )

            # Connect to broker
            self.client.connect(
                self.config.mqtt.host,
                self.config.mqtt.port,
                self.config.mqtt.keepalive
            )

            # Start network loop in background
            self.client.loop_start()

            # Wait for connection
            timeout = 30
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.5)

            if not self.connected:
                raise ConnectionError("Failed to connect to MQTT broker")

            self.logger.info("MQTT connection established")
            service_health['mqtt_connected'] = True

        except Exception as e:
            self.logger.error(f"MQTT connection failed: {e}")
            service_health['mqtt_connected'] = False
            service_health['errors'].append(f"MQTT connection failed: {str(e)}")
            raise

    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connect callback"""
        if rc == 0:
            self.connected = True
            self.reconnect_attempts = 0
            self.logger.info("MQTT connected successfully")

            # Subscribe to sensor topics
            self._subscribe_to_sensors()

        else:
            self.connected = False
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized"
            }
            error_msg = error_messages.get(rc, f"Unknown error code: {rc}")
            self.logger.error(f"MQTT connection failed: {error_msg}")

    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnect callback"""
        self.connected = False
        service_health['mqtt_connected'] = False

        if rc != 0:
            self.logger.warning(f"MQTT unexpected disconnect (rc: {rc})")
            self.reconnect_attempts += 1

            if self.reconnect_attempts < self.config.mqtt.max_reconnect_attempts:
                self.logger.info(
                    f"Attempting reconnect ({self.reconnect_attempts}/"
                    f"{self.config.mqtt.max_reconnect_attempts})"
                )
                time.sleep(self.config.mqtt.reconnect_delay)

    def _on_message(self, client, userdata, message):
        """MQTT message callback"""
        try:
            self.logger.debug(
                f"Received message on topic: {message.topic}, "
                f"payload: {message.payload}"
            )

            service_health['last_mqtt_message'] = {
                'topic': message.topic,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Call registered callbacks
            for callback in self.message_callbacks:
                try:
                    callback(message.topic, message.payload)
                except Exception as e:
                    self.logger.error(f"Message callback error: {e}")

        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}")

    def _subscribe_to_sensors(self):
        """Subscribe to all enabled sensor topics"""
        for sensor_name, sensor_config in self.config.sensors.model_dump().items():
            if isinstance(sensor_config, dict) and sensor_config.get('enabled'):
                topic = sensor_config.get('topic')
                if topic:
                    self.client.subscribe(topic, qos=self.config.mqtt.qos)
                    self.logger.info(f"Subscribed to {sensor_name}: {topic}")

    def publish(self, topic: str, payload: Any, retain: bool = None):
        """
        Publish message to MQTT broker

        Args:
            topic: MQTT topic
            payload: Message payload
            retain: Retain flag (uses config default if None)
        """
        if not self.connected:
            self.logger.warning("Cannot publish, MQTT not connected")
            return

        if retain is None:
            retain = self.config.mqtt.retain

        try:
            self.client.publish(
                topic,
                payload,
                qos=self.config.mqtt.qos,
                retain=retain
            )
        except Exception as e:
            self.logger.error(f"Failed to publish to {topic}: {e}")

    def register_callback(self, callback):
        """Register message callback"""
        self.message_callbacks.append(callback)

    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.logger.info("Disconnecting from MQTT broker")
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False


class HealthCheckServer:
    """HTTP health check endpoint"""

    def __init__(self, config: Config):
        """
        Initialize health check server

        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__ + '.HealthCheck')
        self.app = Flask(__name__)
        self.setup_routes()
        self.server_thread: Optional[Thread] = None

    def setup_routes(self):
        """Setup Flask routes"""

        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            # Update uptime
            startup_time = datetime.fromisoformat(service_health['startup_time'])
            uptime = (datetime.utcnow() - startup_time).total_seconds()
            service_health['uptime_seconds'] = int(uptime)

            # Determine overall health
            is_healthy = (
                service_health['mqtt_connected'] and
                service_health['status'] in ['running', 'healthy']
            )

            status_code = 200 if is_healthy else 503

            return jsonify({
                'status': 'healthy' if is_healthy else 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'details': service_health
            }), status_code

        @self.app.route('/metrics', methods=['GET'])
        def metrics():
            """Metrics endpoint (Prometheus-style)"""
            metrics_data = f"""# HELP wine_monitor_up Service availability
# TYPE wine_monitor_up gauge
wine_monitor_up {{service="wine_fermentation_monitor"}} {1 if service_health['mqtt_connected'] else 0}

# HELP wine_monitor_uptime_seconds Service uptime in seconds
# TYPE wine_monitor_uptime_seconds counter
wine_monitor_uptime_seconds {{service="wine_fermentation_monitor"}} {service_health['uptime_seconds']}

# HELP wine_monitor_mqtt_connected MQTT connection status
# TYPE wine_monitor_mqtt_connected gauge
wine_monitor_mqtt_connected {{service="wine_fermentation_monitor"}} {1 if service_health['mqtt_connected'] else 0}
"""
            return Response(metrics_data, mimetype='text/plain')

        @self.app.route('/ready', methods=['GET'])
        def ready():
            """Readiness check endpoint"""
            is_ready = service_health['status'] == 'running'
            return jsonify({
                'ready': is_ready,
                'timestamp': datetime.utcnow().isoformat()
            }), 200 if is_ready else 503

    def start(self):
        """Start health check server in background thread"""
        self.logger.info(f"Starting health check server on port {self.config.health_check_port}")

        def run_server():
            self.app.run(
                host='0.0.0.0',
                port=self.config.health_check_port,
                debug=False,
                use_reloader=False
            )

        self.server_thread = Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.logger.info("Health check server started")


class ServiceManager:
    """Main service orchestrator"""

    def __init__(self):
        """Initialize service manager"""
        self.logger = logging.getLogger(__name__ + '.ServiceManager')
        self.config: Optional[Config] = None
        self.mqtt_service: Optional[MQTTService] = None
        self.health_server: Optional[HealthCheckServer] = None
        self.running = False

    def setup_signal_handlers(self):
        """Setup graceful shutdown signal handlers"""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            self.logger.info(f"Received signal {signal_name}, initiating shutdown...")
            shutdown_event.set()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    def initialize(self):
        """Initialize all services"""
        try:
            self.logger.info("Initializing Wine Fermentation Monitor...")
            service_health['status'] = 'initializing'

            # Load configuration
            self.logger.info("Loading configuration...")
            self.config = load_config()

            # Setup logging with loaded config
            StructuredLogger.setup(self.config)
            self.logger.info("Logging configured")

            # Startup delay if configured
            if self.config.startup_delay > 0:
                self.logger.info(f"Startup delay: {self.config.startup_delay}s")
                time.sleep(self.config.startup_delay)

            # Initialize MQTT service
            self.logger.info("Initializing MQTT service...")
            self.mqtt_service = MQTTService(self.config)
            self.mqtt_service.connect()
            service_health['services_running']['mqtt'] = True

            # Initialize health check server
            self.logger.info("Initializing health check server...")
            self.health_server = HealthCheckServer(self.config)
            self.health_server.start()
            service_health['services_running']['health_check'] = True

            # TODO: Initialize other services
            # - Data collector
            # - ML prediction service
            # - Alert manager
            # - Home Assistant integration

            self.running = True
            service_health['status'] = 'running'
            self.logger.info("All services initialized successfully")

        except Exception as e:
            self.logger.error(f"Initialization failed: {e}", exc_info=True)
            service_health['status'] = 'error'
            service_health['errors'].append(f"Initialization failed: {str(e)}")
            raise

    def run(self):
        """Main service loop"""
        self.logger.info("Wine Fermentation Monitor is running")

        try:
            while not shutdown_event.is_set():
                # Main service loop
                # TODO: Add periodic tasks here
                # - Check sensor data freshness
                # - Trigger ML predictions
                # - Process alerts
                # - Update HA entities

                # Update health status
                service_health['status'] = 'healthy'

                # Sleep with interrupt check
                shutdown_event.wait(timeout=self.config.health_check_interval)

        except Exception as e:
            self.logger.error(f"Service loop error: {e}", exc_info=True)
            service_health['status'] = 'error'
            service_health['errors'].append(f"Service loop error: {str(e)}")

    def shutdown(self):
        """Graceful shutdown of all services"""
        self.logger.info("Shutting down services...")
        service_health['status'] = 'stopping'

        shutdown_timeout = self.config.shutdown_timeout if self.config else 30

        try:
            # Disconnect MQTT
            if self.mqtt_service:
                self.logger.info("Disconnecting MQTT...")
                self.mqtt_service.disconnect()
                service_health['services_running']['mqtt'] = False

            # TODO: Shutdown other services
            # - Stop data collector
            # - Save ML model state
            # - Flush alerts
            # - Update HA entities

            self.running = False
            service_health['status'] = 'stopped'
            self.logger.info("All services stopped gracefully")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}", exc_info=True)

    def start(self):
        """Start the service manager"""
        try:
            # Setup signal handlers
            self.setup_signal_handlers()

            # Initialize services
            self.initialize()

            # Run main loop
            self.run()

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")

        except Exception as e:
            self.logger.error(f"Fatal error: {e}", exc_info=True)
            sys.exit(1)

        finally:
            # Always attempt graceful shutdown
            self.shutdown()


def main():
    """Main entry point"""
    # Initial logging setup (before config is loaded)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Wine Fermentation Monitor Starting")
    logger.info("=" * 60)

    # Create and start service manager
    manager = ServiceManager()
    manager.start()

    logger.info("Wine Fermentation Monitor stopped")
    sys.exit(0)


if __name__ == '__main__':
    main()
