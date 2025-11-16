"""
Example Integration

Demonstrates how to integrate the MQTT handler, sensor registry, and data manager
for a complete wine production monitoring system.
"""

import logging
import time
import signal
import sys
from pathlib import Path

from mqtt_handler import MQTTHandler
from sensors import SensorRegistry
from data_manager import DataManager


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("wine_monitor")


class WineMonitoringSystem:
    """
    Complete wine production monitoring system integrating MQTT, sensors, and data storage.
    """

    def __init__(self, config: dict):
        """
        Initialize the monitoring system.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.running = False

        # Initialize components
        logger.info("Initializing Wine Monitoring System...")

        # Data manager
        db_path = config.get('database_path', '/data/wine_monitor.db')
        self.data_manager = DataManager(db_path, config.get('data_manager', {}))

        # Sensor registry
        self.sensor_registry = SensorRegistry(config.get('sensor_registry', {}))

        # MQTT handler
        self.mqtt_handler = MQTTHandler(config.get('mqtt', {}))

        # Register MQTT message callback
        self.mqtt_handler.add_message_callback(self.handle_mqtt_message)

        logger.info("System initialized successfully")

    def start(self):
        """Start the monitoring system."""
        logger.info("Starting Wine Monitoring System...")

        # Connect to MQTT broker
        if not self.mqtt_handler.connect(blocking=True):
            logger.error("Failed to connect to MQTT broker")
            return False

        # Subscribe to sensor topics
        topics = self.sensor_registry.get_all_topics()
        logger.info(f"Subscribing to {len(topics)} sensor topics...")
        self.mqtt_handler.subscribe_multiple(topics)

        self.running = True

        # Publish initial health status
        self.publish_health()

        logger.info("Wine Monitoring System started successfully")
        return True

    def stop(self):
        """Stop the monitoring system."""
        logger.info("Stopping Wine Monitoring System...")

        self.running = False

        # Disconnect from MQTT
        self.mqtt_handler.disconnect()

        # Cleanup old data
        self.data_manager.cleanup_old_data()

        logger.info("Wine Monitoring System stopped")

    def handle_mqtt_message(self, topic: str, payload: dict):
        """
        Handle incoming MQTT message.

        Args:
            topic: MQTT topic
            payload: Message payload (already parsed as dict)
        """
        logger.debug(f"Processing message from topic: {topic}")

        # Route message through sensor registry
        sensor_data = self.sensor_registry.process_message(topic, payload)

        if sensor_data:
            # Store in database
            if self.data_manager.store_sensor_data(sensor_data):
                logger.debug(f"Stored sensor data from {sensor_data['sensor_id']}")

                # Check for alerts
                self.check_alerts(sensor_data)

                # Publish processed data
                self.mqtt_handler.publish_sensor_data(
                    sensor_data['sensor_id'],
                    sensor_data
                )
            else:
                logger.warning(f"Failed to store sensor data from {sensor_data['sensor_id']}")

    def check_alerts(self, sensor_data: dict):
        """
        Check sensor data for alert conditions.

        Args:
            sensor_data: Sensor data dictionary
        """
        sensor_id = sensor_data['sensor_id']
        sensor_type = sensor_data['sensor_type']
        measurements = sensor_data['measurements']

        # Example alert conditions

        # Low battery warning for iSpindel
        if sensor_type == 'ispindel' and 'battery' in measurements:
            battery = measurements['battery']
            if battery < 3.3:
                self.create_alert(
                    alert_type='low_battery',
                    severity='warning' if battery >= 3.2 else 'critical',
                    sensor_id=sensor_id,
                    message=f"Low battery on {sensor_id}: {battery}V",
                    details={'battery_voltage': battery}
                )

        # Bubble rate alerts
        if sensor_type == 'bubble_counter' and 'bubble_rate' in measurements:
            bubble_rate = measurements['bubble_rate']

            # Get historical average
            from datetime import datetime, timedelta
            time_series = self.data_manager.get_time_series(
                sensor_id,
                'bubble_rate',
                datetime.now() - timedelta(hours=24)
            )

            if time_series and len(time_series) > 10:
                # Calculate average bubble rate over last 24h
                avg_rate = sum(v for _, v in time_series) / len(time_series)

                # Alert if bubble rate drops significantly (fermentation slowing/stuck)
                if bubble_rate < avg_rate * 0.3 and avg_rate > 1.0:
                    self.create_alert(
                        alert_type='fermentation_slowing',
                        severity='info',
                        sensor_id=sensor_id,
                        message=f"Fermentation activity decreasing on {sensor_id}",
                        details={
                            'current_rate': bubble_rate,
                            'average_rate': avg_rate,
                        }
                    )

        # Temperature alerts
        if 'temperature' in measurements:
            temp = measurements['temperature']

            # Wine fermentation typically 18-28°C
            if temp < 15:
                self.create_alert(
                    alert_type='low_temperature',
                    severity='warning',
                    sensor_id=sensor_id,
                    message=f"Low temperature on {sensor_id}: {temp}°C",
                    details={'temperature': temp}
                )
            elif temp > 30:
                self.create_alert(
                    alert_type='high_temperature',
                    severity='warning',
                    sensor_id=sensor_id,
                    message=f"High temperature on {sensor_id}: {temp}°C",
                    details={'temperature': temp}
                )

        # pH alerts (if available)
        if sensor_type == 'ph' and 'ph' in measurements:
            ph = measurements['ph']

            # Wine typically 3.0-4.0 pH
            if ph < 2.8 or ph > 4.2:
                self.create_alert(
                    alert_type='ph_out_of_range',
                    severity='warning',
                    sensor_id=sensor_id,
                    message=f"pH out of typical wine range on {sensor_id}: {ph}",
                    details={'ph': ph}
                )

    def create_alert(self, alert_type: str, severity: str, sensor_id: str, message: str, details: dict):
        """
        Create and publish an alert.

        Args:
            alert_type: Type of alert
            severity: Severity level (info, warning, critical)
            sensor_id: Sensor that triggered the alert
            message: Alert message
            details: Additional details
        """
        from datetime import datetime

        alert = {
            'timestamp': datetime.now().isoformat(),
            'alert_type': alert_type,
            'severity': severity,
            'sensor_id': sensor_id,
            'message': message,
            'details': details,
        }

        # Store in database
        self.data_manager.store_alert(alert)

        # Publish to MQTT
        self.mqtt_handler.publish_alert(alert)

        logger.warning(f"ALERT [{severity.upper()}]: {message}")

    def publish_health(self):
        """Publish system health status."""
        health = {
            'mqtt': self.mqtt_handler.get_statistics(),
            'sensors': self.sensor_registry.get_health_summary(),
            'database': self.data_manager.get_statistics(),
        }

        self.mqtt_handler.publish_health(health)

    def run(self):
        """Main run loop."""
        if not self.start():
            return

        # Publish health status periodically
        last_health_publish = time.time()
        health_publish_interval = 60  # seconds

        try:
            while self.running:
                # Publish health status
                if time.time() - last_health_publish >= health_publish_interval:
                    self.publish_health()
                    last_health_publish = time.time()

                # Check for missing required sensors
                all_online, missing = self.sensor_registry.check_required_sensors()
                if not all_online:
                    logger.warning(f"Required sensors offline: {missing}")

                time.sleep(10)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()


def main():
    """Main entry point."""

    # Example configuration
    config = {
        'mqtt': {
            'broker': 'localhost',
            'port': 1883,
            'username': None,  # Set if needed
            'password': None,  # Set if needed
            'client_id': 'wine_monitor',
            'keepalive': 60,
            'qos': 1,
            'buffer_size': 1000,
            'reconnect_delay': 5,
            'reconnect_max_delay': 300,
            'reconnect_exponential_backoff': True,
        },
        'sensor_registry': {
            'auto_discovery': True,
            'auto_register': True,
            'sensors': {
                # Pre-configured sensors (optional)
                # 'bubble_001': {
                #     'type': 'bubble',
                #     'timeout_seconds': 300,
                #     'cumulative_mode': True,
                # },
                # 'ispindel_001': {
                #     'type': 'ispindel',
                #     'timeout_seconds': 1800,
                #     'polynomial': [0.0, 0.001, 0.0001, 0.0],  # Calibration coefficients
                # },
            },
        },
        'data_manager': {
            'raw_retention_days': 90,
            'aggregated_retention_days': 365,
            'auto_aggregate': True,
            'aggregation_interval_minutes': 60,
        },
        'database_path': '/data/wine_monitor.db',
    }

    # Create and run system
    system = WineMonitoringSystem(config)

    # Handle signals for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        system.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the system
    system.run()


if __name__ == '__main__':
    main()
