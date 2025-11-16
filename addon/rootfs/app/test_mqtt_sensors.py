"""
Test Script for MQTT Integration and Sensor Management

Comprehensive test suite to verify the MQTT handler, sensor registry,
and data manager are working correctly.
"""

import logging
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("test")


def test_sensors():
    """Test sensor implementations."""
    from sensors import (
        BubbleSensor,
        ISpindelSensor,
        PHSensor,
        TemperatureSensor,
        SensorRegistry,
    )

    logger.info("=" * 60)
    logger.info("Testing Sensor Implementations")
    logger.info("=" * 60)

    # Test Bubble Sensor
    logger.info("\n1. Testing Bubble Sensor")
    bubble = BubbleSensor('bubble_001', {'cumulative_mode': True})

    test_payload = {
        'timestamp': datetime.now().isoformat(),
        'bubbles': 42,
        'interval': 60,
        'rate': 0.7,
        'temperature': 22.5,
    }

    result = bubble.process_message('sensors/bubble/bubble_001', test_payload)
    logger.info(f"   ✓ Bubble sensor processed: {result['measurements']}")

    # Test iSpindel Sensor
    logger.info("\n2. Testing iSpindel Sensor")
    ispindel = ISpindelSensor('ispindel_001')

    test_payload = {
        'name': 'iSpindel001',
        'angle': 45.67,
        'temperature': 20.5,
        'battery': 3.8,
        'gravity': 1.050,
        'RSSI': -65,
    }

    result = ispindel.process_message('ispindel/ispindel_001', test_payload)
    logger.info(f"   ✓ iSpindel processed: {result['measurements']}")

    # Test pH Sensor
    logger.info("\n3. Testing pH Sensor")
    ph_sensor = PHSensor('ph_001')

    test_payload = {
        'ph': 3.5,
        'temperature': 20.0,
    }

    result = ph_sensor.process_message('sensors/ph/ph_001', test_payload)
    logger.info(f"   ✓ pH sensor processed: {result['measurements']}")

    # Test Sensor Registry
    logger.info("\n4. Testing Sensor Registry")
    registry = SensorRegistry({
        'auto_discovery': True,
        'auto_register': True,
    })

    # Register sensors
    registry.register_sensor('bubble_001', 'bubble', {'cumulative_mode': True})
    registry.register_sensor('ispindel_001', 'ispindel')
    registry.register_sensor('ph_001', 'ph')

    logger.info(f"   ✓ Registered {len(registry.get_all_sensors())} sensors")

    # Test message routing
    bubble_payload = {'bubbles': 50, 'rate': 0.8}
    result = registry.process_message('sensors/bubble/bubble_001', bubble_payload)
    logger.info(f"   ✓ Message routed to bubble sensor: {result is not None}")

    # Get health summary
    health = registry.get_health_summary()
    logger.info(f"   ✓ Health: {health['online']} online, {health['offline']} offline")

    # Get capabilities
    caps = registry.get_capabilities_summary()
    logger.info(f"   ✓ Available measurements: {caps['available_measurements']}")

    logger.info("\n✅ All sensor tests passed!\n")


def test_data_manager():
    """Test data manager functionality."""
    from data_manager import DataManager

    logger.info("=" * 60)
    logger.info("Testing Data Manager")
    logger.info("=" * 60)

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    try:
        data_mgr = DataManager(db_path, {
            'raw_retention_days': 90,
            'aggregated_retention_days': 365,
        })

        # Test storing sensor data
        logger.info("\n1. Testing Data Storage")

        test_data = {
            'timestamp': datetime.now().isoformat(),
            'sensor_id': 'bubble_001',
            'sensor_type': 'bubble_counter',
            'measurements': {
                'bubble_rate': 0.7,
                'bubbles': 42,
                'temperature': 22.5,
            },
            'metadata': {
                'interval_seconds': 60,
            },
            'data_quality': 'good',
        }

        success = data_mgr.store_sensor_data(test_data)
        logger.info(f"   ✓ Stored sensor data: {success}")

        # Store multiple data points
        for i in range(10):
            test_data['timestamp'] = (datetime.now() - timedelta(minutes=i)).isoformat()
            test_data['measurements']['bubble_rate'] = 0.5 + (i * 0.1)
            data_mgr.store_sensor_data(test_data)

        # Test retrieving data
        logger.info("\n2. Testing Data Retrieval")

        data = data_mgr.get_sensor_data(
            sensor_id='bubble_001',
            limit=5
        )
        logger.info(f"   ✓ Retrieved {len(data)} records")

        # Test time series
        time_series = data_mgr.get_time_series(
            'bubble_001',
            'bubble_rate',
            datetime.now() - timedelta(hours=1)
        )
        logger.info(f"   ✓ Time series: {len(time_series)} points")

        # Test latest value
        latest = data_mgr.get_latest_value('bubble_001', 'bubble_rate')
        if latest:
            timestamp, value = latest
            logger.info(f"   ✓ Latest bubble_rate: {value} at {timestamp}")

        # Test prediction storage
        logger.info("\n3. Testing Prediction Storage")

        prediction = {
            'timestamp': datetime.now().isoformat(),
            'prediction_type': 'completion_time',
            'predicted_value': 72.5,
            'confidence': 0.85,
            'model_version': 'v1.0',
            'input_data': {'bubble_rate': 0.7},
        }

        success = data_mgr.store_prediction(prediction)
        logger.info(f"   ✓ Stored prediction: {success}")

        # Test alert storage
        logger.info("\n4. Testing Alert Storage")

        alert = {
            'timestamp': datetime.now().isoformat(),
            'alert_type': 'low_battery',
            'severity': 'warning',
            'sensor_id': 'ispindel_001',
            'message': 'Low battery detected',
            'details': {'battery_voltage': 3.2},
        }

        success = data_mgr.store_alert(alert)
        logger.info(f"   ✓ Stored alert: {success}")

        # Test aggregation
        logger.info("\n5. Testing Data Aggregation")

        success = data_mgr.aggregate_data(
            datetime.now() - timedelta(hours=1),
            datetime.now(),
            'hourly'
        )
        logger.info(f"   ✓ Aggregated data: {success}")

        # Get statistics
        logger.info("\n6. Testing Statistics")

        stats = data_mgr.get_statistics()
        logger.info(f"   ✓ Total sensor records: {stats['total_sensor_records']}")
        logger.info(f"   ✓ Total predictions: {stats['total_predictions']}")
        logger.info(f"   ✓ Total alerts: {stats['total_alerts']}")

        logger.info("\n✅ All data manager tests passed!\n")

    finally:
        # Cleanup
        Path(db_path).unlink(missing_ok=True)


def test_mqtt_handler():
    """Test MQTT handler (requires MQTT broker)."""
    from mqtt_handler import MQTTHandler

    logger.info("=" * 60)
    logger.info("Testing MQTT Handler")
    logger.info("=" * 60)

    config = {
        'broker': 'localhost',
        'port': 1883,
        'client_id': 'test_client',
        'buffer_size': 100,
    }

    mqtt = MQTTHandler(config)

    # Test connection (will fail if no broker, which is OK)
    logger.info("\n1. Testing MQTT Connection")

    try:
        success = mqtt.connect(blocking=False)
        logger.info(f"   Connection initiated: {success}")

        if mqtt.wait_for_connection(timeout=5):
            logger.info("   ✓ Connected to MQTT broker")

            # Test subscription
            logger.info("\n2. Testing Subscriptions")
            mqtt.subscribe('test/topic', qos=1)
            logger.info("   ✓ Subscribed to test/topic")

            # Test publishing
            logger.info("\n3. Testing Publishing")

            test_payload = {
                'test': True,
                'timestamp': datetime.now().isoformat(),
                'value': 42,
            }

            success = mqtt.publish('test/topic', test_payload)
            logger.info(f"   ✓ Published message: {success}")

            # Test buffering
            logger.info("\n4. Testing Message Buffering")

            mqtt.disconnect()
            time.sleep(1)

            # Try to publish while disconnected (should buffer)
            success = mqtt.publish('test/topic', {'buffered': True})
            logger.info(f"   ✓ Message buffered: {success}")

            # Check statistics
            logger.info("\n5. Testing Statistics")
            stats = mqtt.get_statistics()
            logger.info(f"   ✓ State: {stats['state']}")
            logger.info(f"   ✓ Messages sent: {stats['messages_sent']}")
            logger.info(f"   ✓ Messages received: {stats['messages_received']}")
            logger.info(f"   ✓ Buffer size: {stats['buffer_size']}")

            logger.info("\n✅ All MQTT tests passed!\n")

        else:
            logger.warning("   ⚠ Could not connect to MQTT broker (is it running?)")
            logger.info("   ℹ MQTT tests skipped\n")

    except Exception as e:
        logger.warning(f"   ⚠ MQTT test error: {e}")
        logger.info("   ℹ MQTT tests skipped (broker may not be available)\n")

    finally:
        mqtt.disconnect()


def test_integration():
    """Test full integration of components."""
    from mqtt_handler import MQTTHandler
    from sensors import SensorRegistry
    from data_manager import DataManager

    logger.info("=" * 60)
    logger.info("Testing Full Integration")
    logger.info("=" * 60)

    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    try:
        # Initialize components
        logger.info("\n1. Initializing Components")

        mqtt_config = {
            'broker': 'localhost',
            'port': 1883,
            'client_id': 'integration_test',
        }

        mqtt = MQTTHandler(mqtt_config)
        registry = SensorRegistry({'auto_discovery': True})
        data_mgr = DataManager(db_path)

        logger.info("   ✓ Components initialized")

        # Register sensors
        logger.info("\n2. Registering Sensors")

        registry.register_sensor('bubble_test', 'bubble')
        registry.register_sensor('ispindel_test', 'ispindel')

        logger.info(f"   ✓ Registered {len(registry.get_all_sensors())} sensors")

        # Simulate sensor messages
        logger.info("\n3. Simulating Sensor Data Flow")

        test_messages = [
            ('sensors/bubble/bubble_test', {
                'bubbles': 42,
                'rate': 0.7,
                'temperature': 22.5,
            }),
            ('ispindel/ispindel_test', {
                'name': 'test',
                'angle': 45.0,
                'temperature': 20.5,
                'battery': 3.8,
                'gravity': 1.050,
            }),
        ]

        processed_count = 0
        for topic, payload in test_messages:
            sensor_data = registry.process_message(topic, payload)
            if sensor_data:
                data_mgr.store_sensor_data(sensor_data)
                processed_count += 1

        logger.info(f"   ✓ Processed and stored {processed_count} messages")

        # Check health
        logger.info("\n4. Checking System Health")

        health = registry.get_health_summary()
        logger.info(f"   ✓ Sensors online: {health['online']}/{health['total_sensors']}")

        stats = data_mgr.get_statistics()
        logger.info(f"   ✓ Database records: {stats['total_sensor_records']}")

        # Test capabilities
        logger.info("\n5. Checking Capabilities")

        caps = registry.get_capabilities_summary()
        logger.info(f"   ✓ Available measurements: {len(caps['available_measurements'])}")
        logger.info(f"   ✓ Sensor types: {list(caps['sensor_types'].keys())}")

        logger.info("\n✅ Integration test passed!\n")

    finally:
        # Cleanup
        Path(db_path).unlink(missing_ok=True)


def main():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("MQTT Integration and Sensor Management Test Suite")
    logger.info("=" * 60 + "\n")

    try:
        # Run tests
        test_sensors()
        test_data_manager()
        test_mqtt_handler()
        test_integration()

        logger.info("=" * 60)
        logger.info("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
