"""
Configuration management for Wine Fermentation Monitor
Handles loading, validation, and access to configuration settings
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


logger = logging.getLogger(__name__)


class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SensorConfig(BaseModel):
    """Configuration for a sensor"""
    enabled: bool = True
    topic: str
    device_class: str = ""
    unit: str = ""

    @field_validator('topic')
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """Validate MQTT topic format"""
        if not v or not v.strip():
            raise ValueError("Topic cannot be empty")
        if '#' in v or '+' in v:
            raise ValueError("Topic cannot contain wildcards")
        return v.strip()


class SensorsConfig(BaseModel):
    """Configuration for all sensors"""
    temperature: SensorConfig = Field(
        default=SensorConfig(
            enabled=True,
            topic="wine/sensors/temperature",
            device_class="temperature",
            unit="°C"
        )
    )
    specific_gravity: SensorConfig = Field(
        default=SensorConfig(
            enabled=True,
            topic="wine/sensors/sg",
            device_class="",
            unit="SG"
        )
    )
    ph: SensorConfig = Field(
        default=SensorConfig(
            enabled=True,
            topic="wine/sensors/ph",
            device_class="",
            unit="pH"
        )
    )
    pressure: SensorConfig = Field(
        default=SensorConfig(
            enabled=False,
            topic="wine/sensors/pressure",
            device_class="pressure",
            unit="kPa"
        )
    )


class MQTTConfig(BaseModel):
    """MQTT broker configuration"""
    host: str = "core-mosquitto"
    port: int = Field(default=1883, ge=1, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    discovery_prefix: str = "homeassistant"
    base_topic: str = "wine/fermentation"
    keepalive: int = Field(default=60, ge=10, le=3600)
    qos: int = Field(default=1, ge=0, le=2)
    retain: bool = True
    reconnect_delay: int = Field(default=5, ge=1, le=300)
    max_reconnect_attempts: int = Field(default=10, ge=1, le=100)

    @field_validator('host')
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate MQTT host"""
        if not v or not v.strip():
            raise ValueError("MQTT host cannot be empty")
        return v.strip()

    @field_validator('base_topic', 'discovery_prefix')
    @classmethod
    def validate_topics(cls, v: str) -> str:
        """Validate MQTT topics"""
        if not v or not v.strip():
            raise ValueError("Topic cannot be empty")
        # Remove leading/trailing slashes
        return v.strip().strip('/')


class MLConfig(BaseModel):
    """Machine Learning configuration"""
    enabled: bool = True
    prediction_interval: int = Field(default=3600, ge=60, le=86400)
    model_retrain_days: int = Field(default=7, ge=1, le=90)
    min_samples_for_training: int = Field(default=100, ge=10, le=10000)
    prediction_window_hours: int = Field(default=72, ge=1, le=720)
    feature_window_hours: int = Field(default=24, ge=1, le=168)
    model_type: str = Field(default="random_forest")
    enable_anomaly_detection: bool = True
    anomaly_threshold: float = Field(default=2.5, ge=1.0, le=5.0)

    @field_validator('model_type')
    @classmethod
    def validate_model_type(cls, v: str) -> str:
        """Validate ML model type"""
        valid_models = ["random_forest", "gradient_boosting", "linear_regression"]
        if v not in valid_models:
            raise ValueError(f"Model type must be one of {valid_models}")
        return v


class AlertsConfig(BaseModel):
    """Alerts configuration"""
    enabled: bool = True
    temperature_min: float = Field(default=18.0, ge=-10.0, le=50.0)
    temperature_max: float = Field(default=28.0, ge=-10.0, le=50.0)
    sg_stuck_threshold: float = Field(default=0.001, ge=0.0001, le=0.1)
    sg_stuck_hours: int = Field(default=48, ge=1, le=720)
    ph_min: float = Field(default=2.8, ge=0.0, le=14.0)
    ph_max: float = Field(default=4.0, ge=0.0, le=14.0)
    notification_cooldown: int = Field(default=3600, ge=60, le=86400)

    @model_validator(mode='after')
    def validate_ranges(self) -> 'AlertsConfig':
        """Validate alert ranges"""
        if self.temperature_min >= self.temperature_max:
            raise ValueError("temperature_min must be less than temperature_max")
        if self.ph_min >= self.ph_max:
            raise ValueError("ph_min must be less than ph_max")
        return self


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: LogLevel = LogLevel.INFO
    structured: bool = True
    log_to_file: bool = Field(default=True)
    log_file_path: str = Field(default="/data/logs/wine_monitor.log")
    max_log_size_mb: int = Field(default=10, ge=1, le=100)
    backup_count: int = Field(default=5, ge=1, le=20)


class Config(BaseModel):
    """Main configuration class"""
    mqtt: MQTTConfig = Field(default_factory=MQTTConfig)
    sensors: SensorsConfig = Field(default_factory=SensorsConfig)
    ml: MLConfig = Field(default_factory=MLConfig)
    alerts: AlertsConfig = Field(default_factory=AlertsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # Data paths
    data_dir: str = Field(default="/data")
    models_dir: str = Field(default="/data/models")
    history_dir: str = Field(default="/data/history")

    # Health check
    health_check_port: int = Field(default=8099, ge=1024, le=65535)
    health_check_interval: int = Field(default=30, ge=5, le=300)

    # Service settings
    shutdown_timeout: int = Field(default=30, ge=5, le=300)
    startup_delay: int = Field(default=5, ge=0, le=60)

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization tasks"""
        # Ensure directories exist
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.models_dir).mkdir(parents=True, exist_ok=True)
        Path(self.history_dir).mkdir(parents=True, exist_ok=True)
        Path(self.logging.log_file_path).parent.mkdir(parents=True, exist_ok=True)


class ConfigLoader:
    """Configuration loader with Home Assistant integration"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader

        Args:
            config_path: Path to configuration file (defaults to HA options.json)
        """
        self.config_path = config_path or os.getenv(
            'CONFIG_PATH',
            '/data/options.json'
        )
        self.config: Optional[Config] = None

    def load(self) -> Config:
        """
        Load and validate configuration

        Returns:
            Validated Config object

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If configuration is invalid
        """
        logger.info(f"Loading configuration from {self.config_path}")

        try:
            # Check if config file exists
            if not Path(self.config_path).exists():
                logger.warning(
                    f"Config file not found at {self.config_path}, "
                    "using defaults"
                )
                self.config = Config()
                return self.config

            # Load configuration from file
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)

            # Merge with environment variables
            config_data = self._merge_environment_vars(config_data)

            # Validate and create config object
            self.config = Config(**config_data)

            logger.info("Configuration loaded and validated successfully")
            self._log_config_summary()

            return self.config

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse configuration JSON: {e}")
            raise ValueError(f"Invalid JSON in configuration file: {e}")

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    def _merge_environment_vars(self, config_data: Dict) -> Dict:
        """
        Merge configuration with environment variables

        Args:
            config_data: Configuration dictionary

        Returns:
            Updated configuration dictionary
        """
        # MQTT settings from environment
        if mqtt_host := os.getenv('MQTT_HOST'):
            config_data.setdefault('mqtt', {})['host'] = mqtt_host

        if mqtt_port := os.getenv('MQTT_PORT'):
            config_data.setdefault('mqtt', {})['port'] = int(mqtt_port)

        if mqtt_user := os.getenv('MQTT_USERNAME'):
            config_data.setdefault('mqtt', {})['username'] = mqtt_user

        if mqtt_pass := os.getenv('MQTT_PASSWORD'):
            config_data.setdefault('mqtt', {})['password'] = mqtt_pass

        # Logging level from environment
        if log_level := os.getenv('LOG_LEVEL'):
            config_data.setdefault('logging', {})['level'] = log_level

        # Data directories from environment
        if data_dir := os.getenv('DATA_DIR'):
            config_data['data_dir'] = data_dir
            config_data['models_dir'] = f"{data_dir}/models"
            config_data['history_dir'] = f"{data_dir}/history"

        return config_data

    def _log_config_summary(self):
        """Log configuration summary"""
        if not self.config:
            return

        logger.info("Configuration Summary:")
        logger.info(f"  MQTT: {self.config.mqtt.host}:{self.config.mqtt.port}")
        logger.info(f"  ML Enabled: {self.config.ml.enabled}")
        logger.info(f"  Alerts Enabled: {self.config.alerts.enabled}")
        logger.info(f"  Log Level: {self.config.logging.level}")

        enabled_sensors = [
            name for name, sensor in self.config.sensors.model_dump().items()
            if isinstance(sensor, dict) and sensor.get('enabled', False)
        ]
        logger.info(f"  Enabled Sensors: {', '.join(enabled_sensors)}")

    def reload(self) -> Config:
        """
        Reload configuration from file

        Returns:
            Updated Config object
        """
        logger.info("Reloading configuration...")
        return self.load()

    def get(self) -> Config:
        """
        Get current configuration

        Returns:
            Current Config object

        Raises:
            RuntimeError: If configuration not loaded
        """
        if self.config is None:
            raise RuntimeError(
                "Configuration not loaded. Call load() first."
            )
        return self.config

    def validate_mqtt_connection(self) -> bool:
        """
        Validate MQTT connection settings

        Returns:
            True if settings appear valid
        """
        if not self.config:
            return False

        try:
            # Basic validation
            if not self.config.mqtt.host:
                logger.error("MQTT host is empty")
                return False

            if not (1 <= self.config.mqtt.port <= 65535):
                logger.error(f"Invalid MQTT port: {self.config.mqtt.port}")
                return False

            return True

        except Exception as e:
            logger.error(f"MQTT configuration validation failed: {e}")
            return False


# Singleton instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """
    Get singleton ConfigLoader instance

    Returns:
        ConfigLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def load_config() -> Config:
    """
    Convenience function to load configuration

    Returns:
        Loaded and validated Config object
    """
    return get_config_loader().load()
