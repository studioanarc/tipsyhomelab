"""
Base Sensor Abstract Class

Defines the interface and common functionality for all sensor types
in the wine production monitoring system.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
from enum import Enum


class SensorStatus(Enum):
    """Sensor health status"""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class DataQuality(Enum):
    """Data quality indicators"""
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    INVALID = "invalid"


class BaseSensor(ABC):
    """
    Abstract base class for all sensors.

    All sensor implementations must inherit from this class and implement
    the abstract methods for parsing, validation, and capability reporting.
    """

    def __init__(self, sensor_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize base sensor.

        Args:
            sensor_id: Unique identifier for this sensor instance
            config: Optional configuration dictionary
        """
        self.sensor_id = sensor_id
        self.config = config or {}
        self.logger = logging.getLogger(f"sensor.{self.__class__.__name__}.{sensor_id}")

        # Health monitoring
        self.last_seen: Optional[datetime] = None
        self.last_value: Optional[Dict[str, Any]] = None
        self.status = SensorStatus.UNKNOWN
        self.message_count = 0
        self.error_count = 0
        self.created_at = datetime.now()

        # Data quality tracking
        self.quality_history: List[DataQuality] = []
        self.max_quality_history = 100

        # Timeout settings
        self.timeout_seconds = config.get('timeout_seconds', 300)  # 5 minutes default

        self.logger.info(f"Initialized {self.__class__.__name__} with ID: {sensor_id}")

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Return the capabilities of this sensor.

        Returns:
            Dictionary describing sensor capabilities including:
            - sensor_type: Type identifier
            - measurements: List of measurement types this sensor provides
            - units: Units for each measurement
            - required: Whether this sensor is required for operation
            - update_interval: Expected update interval in seconds
            - metadata: Additional sensor-specific information
        """
        pass

    @abstractmethod
    def parse_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse incoming MQTT message payload.

        Args:
            payload: Raw message payload (already JSON decoded)

        Returns:
            Normalized sensor data dictionary with standard keys:
            - timestamp: ISO format timestamp
            - sensor_id: Sensor identifier
            - measurements: Dict of measurement_name -> value
            - metadata: Optional additional data

        Raises:
            ValueError: If message format is invalid
        """
        pass

    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, DataQuality, Optional[str]]:
        """
        Validate parsed sensor data.

        Args:
            data: Parsed sensor data from parse_message()

        Returns:
            Tuple of (is_valid, quality, error_message)
            - is_valid: Whether data passes basic validation
            - quality: Data quality assessment
            - error_message: Description if validation failed, None otherwise
        """
        pass

    def get_mqtt_topics(self) -> List[str]:
        """
        Get list of MQTT topics this sensor subscribes to.

        Returns:
            List of topic patterns (wildcards allowed)
        """
        return [f"sensors/{self.sensor_id}/#"]

    def update_health(self, success: bool = True, quality: Optional[DataQuality] = None):
        """
        Update sensor health status.

        Args:
            success: Whether the last operation was successful
            quality: Data quality of last reading
        """
        self.last_seen = datetime.now()
        self.message_count += 1

        if not success:
            self.error_count += 1

        # Track quality history
        if quality:
            self.quality_history.append(quality)
            if len(self.quality_history) > self.max_quality_history:
                self.quality_history.pop(0)

        # Update status based on recent activity
        self.status = self._calculate_status()

    def _calculate_status(self) -> SensorStatus:
        """Calculate current sensor status based on health metrics."""
        if self.last_seen is None:
            return SensorStatus.UNKNOWN

        # Check if sensor has timed out
        time_since_last_seen = datetime.now() - self.last_seen
        if time_since_last_seen > timedelta(seconds=self.timeout_seconds):
            return SensorStatus.OFFLINE

        # Check error rate
        if self.message_count > 10:
            error_rate = self.error_count / self.message_count
            if error_rate > 0.5:
                return SensorStatus.DEGRADED

        # Check recent data quality
        if len(self.quality_history) >= 5:
            recent_quality = self.quality_history[-5:]
            poor_count = sum(1 for q in recent_quality if q in [DataQuality.POOR, DataQuality.INVALID])
            if poor_count >= 3:
                return SensorStatus.DEGRADED

        return SensorStatus.ONLINE

    def get_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report for this sensor.

        Returns:
            Dictionary with health metrics and status
        """
        uptime = None
        if self.created_at:
            uptime = (datetime.now() - self.created_at).total_seconds()

        time_since_last_seen = None
        if self.last_seen:
            time_since_last_seen = (datetime.now() - self.last_seen).total_seconds()

        error_rate = 0
        if self.message_count > 0:
            error_rate = self.error_count / self.message_count

        # Calculate quality statistics
        quality_stats = {}
        if self.quality_history:
            quality_stats = {
                'good': sum(1 for q in self.quality_history if q == DataQuality.GOOD),
                'acceptable': sum(1 for q in self.quality_history if q == DataQuality.ACCEPTABLE),
                'poor': sum(1 for q in self.quality_history if q == DataQuality.POOR),
                'invalid': sum(1 for q in self.quality_history if q == DataQuality.INVALID),
            }

        return {
            'sensor_id': self.sensor_id,
            'sensor_type': self.__class__.__name__,
            'status': self.status.value,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'time_since_last_seen_seconds': time_since_last_seen,
            'uptime_seconds': uptime,
            'message_count': self.message_count,
            'error_count': self.error_count,
            'error_rate': error_rate,
            'quality_stats': quality_stats,
            'last_value': self.last_value,
            'timeout_seconds': self.timeout_seconds,
        }

    def process_message(self, topic: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Complete message processing pipeline.

        Args:
            topic: MQTT topic the message was received on
            payload: Message payload (JSON decoded)

        Returns:
            Normalized and validated sensor data, or None if processing failed
        """
        try:
            # Parse the message
            data = self.parse_message(payload)

            # Validate the data
            is_valid, quality, error_msg = self.validate_data(data)

            if not is_valid:
                self.logger.warning(f"Invalid data from {self.sensor_id}: {error_msg}")
                self.update_health(success=False, quality=quality)
                return None

            # Add quality metadata
            data['data_quality'] = quality.value

            # Update health status
            self.update_health(success=True, quality=quality)
            self.last_value = data

            self.logger.debug(f"Processed message from {self.sensor_id}: {data}")
            return data

        except Exception as e:
            self.logger.error(f"Error processing message from {self.sensor_id}: {e}", exc_info=True)
            self.update_health(success=False)
            return None

    def is_required(self) -> bool:
        """
        Check if this sensor is required for system operation.

        Returns:
            True if sensor is required, False otherwise
        """
        capabilities = self.get_capabilities()
        return capabilities.get('required', False)

    def get_expected_interval(self) -> int:
        """
        Get expected update interval in seconds.

        Returns:
            Expected interval between sensor updates
        """
        capabilities = self.get_capabilities()
        return capabilities.get('update_interval', 60)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize sensor to dictionary.

        Returns:
            Dictionary representation of sensor
        """
        return {
            'sensor_id': self.sensor_id,
            'sensor_type': self.__class__.__name__,
            'config': self.config,
            'capabilities': self.get_capabilities(),
            'health': self.get_health_report(),
            'topics': self.get_mqtt_topics(),
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.sensor_id}, status={self.status.value})"
