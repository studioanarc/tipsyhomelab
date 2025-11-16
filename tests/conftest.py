"""Pytest configuration and fixtures for wine production monitoring tests."""
import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry


# Test data paths
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_mqtt_client():
    """Mock MQTT client for testing."""
    client = MagicMock()
    client.connect = AsyncMock(return_value=True)
    client.disconnect = AsyncMock(return_value=True)
    client.subscribe = AsyncMock(return_value=True)
    client.publish = AsyncMock(return_value=True)
    client.is_connected = MagicMock(return_value=True)
    return client


@pytest.fixture
def sample_ispindel_message():
    """Load sample iSpindel MQTT message."""
    with open(FIXTURES_DIR / "ispindel_messages.json") as f:
        data = json.load(f)
    return data["valid_messages"][0]


@pytest.fixture
def sample_bubble_sensor_data():
    """Load sample bubble sensor data."""
    with open(FIXTURES_DIR / "bubble_sensor_data.json") as f:
        return json.load(f)


@pytest.fixture
def sample_fermentation_data():
    """Load sample fermentation time series data."""
    with open(FIXTURES_DIR / "sample_fermentation_data.json") as f:
        return json.load(f)


@pytest.fixture
def mock_database():
    """Mock database connection for testing."""
    db = MagicMock()
    db.insert = AsyncMock(return_value=True)
    db.query = AsyncMock(return_value=[])
    db.update = AsyncMock(return_value=True)
    db.delete = AsyncMock(return_value=True)
    db.close = AsyncMock(return_value=True)
    return db


@pytest.fixture
def mock_config_entry():
    """Create mock config entry for Home Assistant."""
    return MockConfigEntry(
        domain="wine_monitor",
        data={
            "mqtt_broker": "localhost",
            "mqtt_port": 1883,
            "mqtt_username": "test_user",
            "mqtt_password": "test_pass",
            "ispindel_topic": "ispindel/+",
            "bubble_sensor_topic": "bubble/+",
        },
        unique_id="test_wine_monitor",
    )


@pytest.fixture
async def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    hass.states = MagicMock()
    hass.states.async_set = AsyncMock()
    hass.bus = MagicMock()
    hass.bus.async_fire = AsyncMock()
    return hass


@pytest.fixture
def mock_ml_model():
    """Mock ML model for predictions."""
    model = MagicMock()
    model.predict = MagicMock(return_value=[[0.75]])  # Predicted completion percentage
    model.score = MagicMock(return_value=0.95)  # Model accuracy
    model.fit = MagicMock()
    return model


@pytest.fixture
def valid_sensor_data():
    """Provide valid sensor data for validation tests."""
    return {
        "temperature": 20.5,
        "specific_gravity": 1.050,
        "battery": 3.8,
        "angle": 45.2,
        "rssi": -65,
    }


@pytest.fixture
def invalid_sensor_data():
    """Provide invalid sensor data for validation tests."""
    return [
        {"temperature": -50, "specific_gravity": 1.050},  # Temperature too low
        {"temperature": 20, "specific_gravity": 0.5},  # SG too low
        {"temperature": 20, "specific_gravity": 2.0},  # SG too high
        {"temperature": 100, "specific_gravity": 1.050},  # Temperature too high
        {"battery": -1},  # Negative battery
        {"angle": 200},  # Invalid angle
    ]


@pytest.fixture
def mock_sensor_validator():
    """Mock sensor data validator."""
    validator = MagicMock()
    validator.validate_temperature = MagicMock(return_value=True)
    validator.validate_gravity = MagicMock(return_value=True)
    validator.validate_battery = MagicMock(return_value=True)
    validator.validate_all = MagicMock(return_value=True)
    return validator


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_time_series_data():
    """Generate mock time series data for ML training."""
    import numpy as np
    from datetime import datetime, timedelta

    base_time = datetime.now()
    data = []

    for i in range(100):
        data.append({
            "timestamp": (base_time + timedelta(hours=i)).isoformat(),
            "temperature": 20 + np.random.normal(0, 1),
            "gravity": 1.050 - (i * 0.0005) + np.random.normal(0, 0.001),
            "bubble_rate": max(0, 60 - i * 0.5 + np.random.normal(0, 5)),
        })

    return data


@pytest.fixture
def mqtt_message_factory():
    """Factory for creating MQTT messages."""
    def _create_message(topic, payload, qos=0, retain=False):
        msg = MagicMock()
        msg.topic = topic
        msg.payload = payload if isinstance(payload, bytes) else payload.encode()
        msg.qos = qos
        msg.retain = retain
        return msg

    return _create_message


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    logger = MagicMock()
    logger.debug = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.critical = MagicMock()
    return logger


# Environment setup for tests
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ["TESTING"] = "true"
    os.environ["MQTT_BROKER"] = "localhost"
    os.environ["MQTT_PORT"] = "1883"
    yield
    del os.environ["TESTING"]
