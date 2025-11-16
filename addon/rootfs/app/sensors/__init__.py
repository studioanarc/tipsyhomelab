"""
Sensors Package

Wine production monitoring sensors with dynamic discovery and health monitoring.
"""

from .base_sensor import BaseSensor, SensorStatus, DataQuality
from .bubble_sensor import BubbleSensor
from .ispindel_sensor import ISpindelSensor
from .optional_sensors import (
    GenericSensor,
    PHSensor,
    DissolvedOxygenSensor,
    PressureSensor,
    TemperatureSensor,
    HumiditySensor,
)
from .sensor_registry import SensorRegistry

__all__ = [
    'BaseSensor',
    'SensorStatus',
    'DataQuality',
    'BubbleSensor',
    'ISpindelSensor',
    'GenericSensor',
    'PHSensor',
    'DissolvedOxygenSensor',
    'PressureSensor',
    'TemperatureSensor',
    'HumiditySensor',
    'SensorRegistry',
]
