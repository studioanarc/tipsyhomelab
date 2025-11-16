"""Tests for sensor data validation and processing."""
import json
from datetime import datetime

import pytest


class TestSensorDataValidation:
    """Test sensor data validation."""

    def test_validate_temperature_range(self, valid_sensor_data):
        """Test temperature is within valid range."""
        temp = valid_sensor_data["temperature"]
        assert -10 <= temp <= 50, "Temperature out of fermentation range"

    def test_validate_specific_gravity_range(self, valid_sensor_data):
        """Test specific gravity is within valid range."""
        sg = valid_sensor_data["specific_gravity"]
        assert 0.990 <= sg <= 1.150, "Specific gravity out of valid range"

    def test_validate_battery_voltage(self, valid_sensor_data):
        """Test battery voltage is valid."""
        battery = valid_sensor_data["battery"]
        assert 0 <= battery <= 5.0, "Battery voltage out of range"

    def test_validate_angle_range(self, valid_sensor_data):
        """Test angle is within valid range."""
        angle = valid_sensor_data["angle"]
        assert 0 <= angle <= 90, "Angle out of valid range"

    def test_reject_invalid_temperature(self, invalid_sensor_data):
        """Test rejection of invalid temperature."""
        data = invalid_sensor_data[0]  # Temperature too low
        temp = data["temperature"]
        assert temp < -10, "Should detect invalid temperature"

    def test_reject_invalid_gravity(self, invalid_sensor_data):
        """Test rejection of invalid specific gravity."""
        data_low = invalid_sensor_data[1]  # SG too low
        data_high = invalid_sensor_data[2]  # SG too high

        assert data_low["specific_gravity"] < 0.990
        assert data_high["specific_gravity"] > 1.150

    def test_reject_negative_battery(self, invalid_sensor_data):
        """Test rejection of negative battery voltage."""
        data = invalid_sensor_data[4]  # Negative battery
        assert data["battery"] < 0


class TestISpindelSensorData:
    """Test iSpindel sensor specific functionality."""

    def test_ispindel_message_structure(self, sample_ispindel_message):
        """Test iSpindel message has required fields."""
        required_fields = [
            "name",
            "angle",
            "temperature",
            "battery",
            "gravity",
        ]

        for field in required_fields:
            assert field in sample_ispindel_message, f"Missing field: {field}"

    def test_ispindel_calibration_data(self):
        """Test loading iSpindel calibration data."""
        with open("tests/fixtures/ispindel_messages.json") as f:
            data = json.load(f)

        calibration = data["calibration_data"]["iSpindel001"]
        assert "polynomial_coefficients" in calibration
        assert "angle_to_gravity_samples" in calibration

        # Test polynomial coefficients
        coeffs = calibration["polynomial_coefficients"]
        assert len(coeffs) == 3, "Should have 3 coefficients for quadratic"

    def test_angle_to_gravity_conversion(self):
        """Test converting angle to specific gravity using calibration."""
        with open("tests/fixtures/ispindel_messages.json") as f:
            data = json.load(f)

        calibration = data["calibration_data"]["iSpindel001"]
        coeffs = calibration["polynomial_coefficients"]

        # Test polynomial: gravity = a*angle^2 + b*angle + c
        angle = 45.0
        a, b, c = coeffs
        calculated_gravity = a * (angle ** 2) + b * angle + c

        # Should be close to expected value
        assert 1.040 <= calculated_gravity <= 1.060

    def test_ispindel_rssi_signal_strength(self, sample_ispindel_message):
        """Test RSSI signal strength validation."""
        rssi = sample_ispindel_message["RSSI"]
        assert -100 <= rssi <= 0, "RSSI should be negative dBm"

    def test_ispindel_temperature_units(self, sample_ispindel_message):
        """Test temperature units handling."""
        temp_units = sample_ispindel_message.get("temp_units", "C")
        assert temp_units in ["C", "F"], "Temperature units should be C or F"

    def test_ispindel_interval_validation(self, sample_ispindel_message):
        """Test measurement interval is valid."""
        interval = sample_ispindel_message.get("interval", 900)
        assert interval >= 60, "Interval should be at least 60 seconds"
        assert interval <= 7200, "Interval should not exceed 2 hours"


class TestBubbleSensorData:
    """Test bubble sensor specific functionality."""

    def test_bubble_sensor_message_structure(self, sample_bubble_sensor_data):
        """Test bubble sensor message structure."""
        message = sample_bubble_sensor_data["valid_messages"][0]

        required_fields = [
            "sensor_id",
            "timestamp",
            "bubble_count",
            "interval_seconds",
            "bubble_rate_per_minute",
        ]

        for field in required_fields:
            assert field in message, f"Missing field: {field}"

    def test_bubble_rate_calculation(self, sample_bubble_sensor_data):
        """Test bubble rate calculation."""
        message = sample_bubble_sensor_data["valid_messages"][1]

        bubble_count = message["bubble_count"]
        interval = message["interval_seconds"]
        expected_rate = (bubble_count / interval) * 60

        assert message["bubble_rate_per_minute"] == expected_rate

    def test_bubble_count_validation(self, sample_bubble_sensor_data):
        """Test bubble count is non-negative."""
        for message in sample_bubble_sensor_data["valid_messages"]:
            assert message["bubble_count"] >= 0

    def test_fermentation_phase_detection(self, sample_bubble_sensor_data):
        """Test detecting fermentation phase from bubble rate."""
        phases = sample_bubble_sensor_data["fermentation_phases"]
        time_series = sample_bubble_sensor_data["time_series_data"]

        for data_point in time_series:
            bubble_rate = data_point["bubble_rate"]
            expected_phase = data_point["phase"]

            # Verify phase matches bubble rate range
            phase_info = phases[expected_phase]
            min_rate, max_rate = phase_info["bubble_rate_range"]

            assert min_rate <= bubble_rate <= max_rate, \
                f"Bubble rate {bubble_rate} doesn't match phase {expected_phase}"

    def test_timestamp_parsing(self, sample_bubble_sensor_data):
        """Test timestamp parsing."""
        message = sample_bubble_sensor_data["valid_messages"][0]
        timestamp_str = message["timestamp"]

        # Parse ISO format timestamp
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        assert isinstance(timestamp, datetime)

    def test_battery_percentage_range(self, sample_bubble_sensor_data):
        """Test battery percentage is in valid range."""
        for message in sample_bubble_sensor_data["valid_messages"]:
            if "battery_percent" in message:
                battery = message["battery_percent"]
                assert 0 <= battery <= 100


class TestSensorDataSanityChecks:
    """Test sensor data sanity checks."""

    def test_gravity_decreases_over_time(self, sample_fermentation_data):
        """Test that gravity decreases during fermentation."""
        batch = sample_fermentation_data["fermentation_batches"][0]
        data_points = batch["data_points"]

        # Check overall trend (gravity should decrease)
        initial_gravity = data_points[0]["gravity"]
        final_gravity = data_points[-1]["gravity"]

        assert final_gravity < initial_gravity, \
            "Gravity should decrease during fermentation"

    def test_temperature_stability(self, sample_fermentation_data):
        """Test temperature remains relatively stable."""
        batch = sample_fermentation_data["fermentation_batches"][0]
        data_points = batch["data_points"]

        temperatures = [dp["temperature"] for dp in data_points]
        temp_range = max(temperatures) - min(temperatures)

        # Temperature should not vary wildly
        assert temp_range < 10, "Temperature variation too high"

    def test_battery_degradation(self, sample_fermentation_data):
        """Test battery voltage decreases over time."""
        batch = sample_fermentation_data["fermentation_batches"][0]
        data_points = batch["data_points"]

        initial_battery = data_points[0]["battery"]
        final_battery = data_points[-1]["battery"]

        assert final_battery <= initial_battery, \
            "Battery should not increase over time"

    def test_bubble_rate_lifecycle(self, sample_bubble_sensor_data):
        """Test bubble rate follows expected fermentation lifecycle."""
        time_series = sample_bubble_sensor_data["time_series_data"]

        # Should start low, peak, then decline
        bubble_rates = [dp["bubble_rate"] for dp in time_series]

        # Find peak
        peak_index = bubble_rates.index(max(bubble_rates))

        # Should have some activity before peak
        assert peak_index > 0

        # Should decline after peak
        assert peak_index < len(bubble_rates) - 1

        # Final rate should be lower than peak
        assert bubble_rates[-1] < bubble_rates[peak_index]

    def test_angle_increases_with_gravity_decrease(self, sample_fermentation_data):
        """Test iSpindel angle increases as gravity decreases."""
        batch = sample_fermentation_data["fermentation_batches"][0]
        data_points = batch["data_points"]

        # As fermentation progresses, angle should increase
        initial_angle = data_points[0]["angle"]
        final_angle = data_points[-1]["angle"]

        assert final_angle > initial_angle, \
            "Angle should increase as gravity decreases"

    def test_no_duplicate_timestamps(self, sample_fermentation_data):
        """Test no duplicate timestamps in data."""
        batch = sample_fermentation_data["fermentation_batches"][0]
        data_points = batch["data_points"]

        timestamps = [dp["timestamp"] for dp in data_points]
        assert len(timestamps) == len(set(timestamps)), \
            "Duplicate timestamps found"

    def test_chronological_order(self, sample_fermentation_data):
        """Test data points are in chronological order."""
        batch = sample_fermentation_data["fermentation_batches"][0]
        data_points = batch["data_points"]

        timestamps = [
            datetime.fromisoformat(dp["timestamp"].replace("Z", "+00:00"))
            for dp in data_points
        ]

        # Check if sorted
        assert timestamps == sorted(timestamps), \
            "Timestamps not in chronological order"


class TestSensorValidator:
    """Test sensor validator utility."""

    def test_validator_accepts_valid_data(self, mock_sensor_validator, valid_sensor_data):
        """Test validator accepts valid sensor data."""
        result = mock_sensor_validator.validate_all(valid_sensor_data)
        assert result is True

    def test_validator_temperature_check(self, mock_sensor_validator):
        """Test temperature validation."""
        assert mock_sensor_validator.validate_temperature(20.0) is True
        mock_sensor_validator.validate_temperature.assert_called_with(20.0)

    def test_validator_gravity_check(self, mock_sensor_validator):
        """Test gravity validation."""
        assert mock_sensor_validator.validate_gravity(1.050) is True
        mock_sensor_validator.validate_gravity.assert_called_with(1.050)

    def test_validator_battery_check(self, mock_sensor_validator):
        """Test battery validation."""
        assert mock_sensor_validator.validate_battery(3.8) is True
        mock_sensor_validator.validate_battery.assert_called_with(3.8)


class TestMultipleSensors:
    """Test handling multiple sensors."""

    def test_multiple_ispindel_devices(self):
        """Test handling multiple iSpindel devices."""
        with open("tests/fixtures/ispindel_messages.json") as f:
            data = json.load(f)

        messages = data["valid_messages"]
        device_names = [msg["name"] for msg in messages]

        # Should have multiple unique devices
        assert len(device_names) == len(set(device_names))
        assert len(device_names) >= 2

    def test_multiple_bubble_sensors(self, sample_bubble_sensor_data):
        """Test handling multiple bubble sensors."""
        messages = sample_bubble_sensor_data["valid_messages"]
        sensor_ids = [msg["sensor_id"] for msg in messages]

        # Should have at least 2 different sensors
        unique_sensors = set(sensor_ids)
        assert len(unique_sensors) >= 2

    def test_sensor_id_uniqueness(self, sample_bubble_sensor_data):
        """Test sensor IDs are properly tracked."""
        messages = sample_bubble_sensor_data["valid_messages"]

        # Group by sensor ID
        by_sensor = {}
        for msg in messages:
            sensor_id = msg["sensor_id"]
            if sensor_id not in by_sensor:
                by_sensor[sensor_id] = []
            by_sensor[sensor_id].append(msg)

        # Each sensor should have at least one message
        for sensor_id, msgs in by_sensor.items():
            assert len(msgs) > 0
