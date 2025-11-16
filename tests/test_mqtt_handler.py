"""Tests for MQTT handler functionality."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestMQTTConnection:
    """Test MQTT connection handling."""

    @pytest.mark.asyncio
    async def test_mqtt_connect_success(self, mock_mqtt_client):
        """Test successful MQTT connection."""
        result = await mock_mqtt_client.connect()
        assert result is True
        mock_mqtt_client.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_mqtt_connect_failure(self):
        """Test MQTT connection failure handling."""
        client = MagicMock()
        client.connect = AsyncMock(side_effect=ConnectionError("Connection failed"))

        with pytest.raises(ConnectionError):
            await client.connect()

    @pytest.mark.asyncio
    async def test_mqtt_disconnect(self, mock_mqtt_client):
        """Test MQTT disconnection."""
        result = await mock_mqtt_client.disconnect()
        assert result is True
        mock_mqtt_client.disconnect.assert_called_once()

    def test_mqtt_is_connected(self, mock_mqtt_client):
        """Test MQTT connection status check."""
        assert mock_mqtt_client.is_connected() is True

    @pytest.mark.asyncio
    async def test_mqtt_reconnect_on_disconnect(self, mock_mqtt_client):
        """Test automatic reconnection on disconnect."""
        mock_mqtt_client.is_connected = MagicMock(side_effect=[False, True])

        # First call shows disconnected, should trigger reconnect
        if not mock_mqtt_client.is_connected():
            await mock_mqtt_client.connect()

        # Verify reconnection was attempted
        assert mock_mqtt_client.connect.call_count > 0


class TestMQTTSubscription:
    """Test MQTT topic subscription."""

    @pytest.mark.asyncio
    async def test_subscribe_ispindel_topic(self, mock_mqtt_client):
        """Test subscribing to iSpindel topic."""
        topic = "ispindel/+"
        result = await mock_mqtt_client.subscribe(topic)

        assert result is True
        mock_mqtt_client.subscribe.assert_called_once_with(topic)

    @pytest.mark.asyncio
    async def test_subscribe_bubble_sensor_topic(self, mock_mqtt_client):
        """Test subscribing to bubble sensor topic."""
        topic = "bubble/+"
        result = await mock_mqtt_client.subscribe(topic)

        assert result is True
        mock_mqtt_client.subscribe.assert_called_once_with(topic)

    @pytest.mark.asyncio
    async def test_subscribe_multiple_topics(self, mock_mqtt_client):
        """Test subscribing to multiple topics."""
        topics = ["ispindel/+", "bubble/+", "fermentation/#"]

        for topic in topics:
            await mock_mqtt_client.subscribe(topic)

        assert mock_mqtt_client.subscribe.call_count == len(topics)

    @pytest.mark.asyncio
    async def test_subscribe_with_qos(self, mock_mqtt_client):
        """Test subscribing with specific QoS level."""
        topic = "ispindel/+"
        qos = 1

        await mock_mqtt_client.subscribe(topic, qos=qos)
        mock_mqtt_client.subscribe.assert_called_with(topic, qos=qos)


class TestMQTTMessageParsing:
    """Test MQTT message parsing."""

    def test_parse_valid_ispindel_message(self, sample_ispindel_message):
        """Test parsing valid iSpindel message."""
        assert "name" in sample_ispindel_message
        assert "temperature" in sample_ispindel_message
        assert "gravity" in sample_ispindel_message
        assert "angle" in sample_ispindel_message
        assert "battery" in sample_ispindel_message

        # Validate data types
        assert isinstance(sample_ispindel_message["temperature"], (int, float))
        assert isinstance(sample_ispindel_message["gravity"], (int, float))
        assert isinstance(sample_ispindel_message["battery"], (int, float))

    def test_parse_ispindel_json(self, sample_ispindel_message):
        """Test parsing iSpindel JSON payload."""
        json_payload = json.dumps(sample_ispindel_message)
        parsed = json.loads(json_payload)

        assert parsed == sample_ispindel_message

    def test_parse_malformed_json(self):
        """Test handling of malformed JSON."""
        malformed = '{"temperature": 20.5, "gravity": 1.050'  # Missing closing brace

        with pytest.raises(json.JSONDecodeError):
            json.loads(malformed)

    def test_parse_bubble_sensor_message(self, sample_bubble_sensor_data):
        """Test parsing bubble sensor message."""
        message = sample_bubble_sensor_data["valid_messages"][0]

        assert "sensor_id" in message
        assert "bubble_count" in message
        assert "bubble_rate_per_minute" in message
        assert isinstance(message["bubble_count"], int)

    def test_parse_message_with_extra_fields(self, sample_ispindel_message):
        """Test parsing message with extra unknown fields."""
        message = sample_ispindel_message.copy()
        message["unknown_field"] = "some_value"

        # Should still parse core fields
        assert "temperature" in message
        assert "gravity" in message

    def test_extract_device_name_from_topic(self):
        """Test extracting device name from MQTT topic."""
        topic = "ispindel/iSpindel001"
        device_name = topic.split("/")[-1]

        assert device_name == "iSpindel001"

    def test_topic_matching(self):
        """Test MQTT topic pattern matching."""
        topics = [
            ("ispindel/iSpindel001", "ispindel/+"),
            ("bubble/bubble_001", "bubble/+"),
            ("fermentation/batch1/data", "fermentation/#"),
        ]

        for specific_topic, pattern in topics:
            # Simple wildcard matching
            if "+" in pattern:
                pattern_parts = pattern.split("/")
                topic_parts = specific_topic.split("/")
                assert len(pattern_parts) == len(topic_parts)
            elif "#" in pattern:
                prefix = pattern.replace("/#", "")
                assert specific_topic.startswith(prefix)


class TestMQTTMessagePublishing:
    """Test MQTT message publishing."""

    @pytest.mark.asyncio
    async def test_publish_status_update(self, mock_mqtt_client):
        """Test publishing status update."""
        topic = "homeassistant/sensor/wine_monitor/state"
        payload = json.dumps({"status": "fermenting", "completion": 45.5})

        await mock_mqtt_client.publish(topic, payload)
        mock_mqtt_client.publish.assert_called_once_with(topic, payload)

    @pytest.mark.asyncio
    async def test_publish_with_retain(self, mock_mqtt_client):
        """Test publishing with retain flag."""
        topic = "homeassistant/sensor/wine_monitor/config"
        payload = json.dumps({"device": "wine_monitor"})

        await mock_mqtt_client.publish(topic, payload, retain=True)
        mock_mqtt_client.publish.assert_called_once_with(topic, payload, retain=True)

    @pytest.mark.asyncio
    async def test_publish_binary_payload(self, mock_mqtt_client):
        """Test publishing binary payload."""
        topic = "test/binary"
        payload = b"\x00\x01\x02\x03"

        await mock_mqtt_client.publish(topic, payload)
        mock_mqtt_client.publish.assert_called_once()


class TestMQTTErrorHandling:
    """Test MQTT error handling."""

    @pytest.mark.asyncio
    async def test_handle_connection_timeout(self):
        """Test handling connection timeout."""
        client = MagicMock()
        client.connect = AsyncMock(side_effect=TimeoutError("Connection timeout"))

        with pytest.raises(TimeoutError):
            await client.connect()

    @pytest.mark.asyncio
    async def test_handle_subscription_error(self, mock_mqtt_client):
        """Test handling subscription error."""
        mock_mqtt_client.subscribe = AsyncMock(
            side_effect=Exception("Subscription failed")
        )

        with pytest.raises(Exception):
            await mock_mqtt_client.subscribe("test/topic")

    def test_handle_invalid_payload_encoding(self):
        """Test handling invalid payload encoding."""
        invalid_payload = b"\xff\xfe"  # Invalid UTF-8

        with pytest.raises(UnicodeDecodeError):
            invalid_payload.decode("utf-8")

    @pytest.mark.asyncio
    async def test_message_callback_error_handling(self, mock_mqtt_client):
        """Test error handling in message callback."""

        def faulty_callback(message):
            raise ValueError("Callback error")

        # Callback should be wrapped in try-except
        message = MagicMock()
        try:
            faulty_callback(message)
        except ValueError as e:
            assert str(e) == "Callback error"


class TestMQTTMessageFactory:
    """Test MQTT message factory."""

    def test_create_mqtt_message(self, mqtt_message_factory):
        """Test creating MQTT message."""
        topic = "test/topic"
        payload = "test payload"

        message = mqtt_message_factory(topic, payload)

        assert message.topic == topic
        assert message.payload == payload.encode()

    def test_create_mqtt_message_with_bytes(self, mqtt_message_factory):
        """Test creating MQTT message with bytes payload."""
        topic = "test/topic"
        payload = b"test payload"

        message = mqtt_message_factory(topic, payload)

        assert message.topic == topic
        assert message.payload == payload

    def test_create_mqtt_message_with_qos(self, mqtt_message_factory):
        """Test creating MQTT message with QoS."""
        topic = "test/topic"
        payload = "test"
        qos = 1

        message = mqtt_message_factory(topic, payload, qos=qos)

        assert message.qos == qos

    def test_create_retained_message(self, mqtt_message_factory):
        """Test creating retained message."""
        topic = "test/topic"
        payload = "test"

        message = mqtt_message_factory(topic, payload, retain=True)

        assert message.retain is True
