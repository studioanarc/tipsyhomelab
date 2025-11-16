# Changelog

All notable changes to the Wine Fermentation Monitor add-on will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-16

### Added

#### Core Infrastructure
- Complete Home Assistant add-on structure with HACS compatibility
- Multi-stage Dockerfile with Python 3.11 for optimized image size
- Comprehensive configuration schema with Pydantic validation
- Structured JSON logging with file rotation
- Health check HTTP endpoints (health, ready, metrics)
- Graceful shutdown handling with signal management
- Environment variable support for flexible deployment

#### MQTT Integration
- Paho-MQTT client with connection retry logic
- Automatic reconnection with exponential backoff
- MQTT discovery support for Home Assistant
- Configurable QoS, retain, and keepalive settings
- Multi-sensor topic subscription management
- Message callback system for extensibility

#### Configuration Management
- YAML-based configuration with defaults
- JSON schema validation
- MQTT connection validation
- Sensor configuration per device
- ML model parameter configuration
- Alert threshold management
- Logging level and format control

#### Monitoring & Health
- Real-time service health tracking
- Prometheus-style metrics endpoint
- Kubernetes-compatible readiness probes
- Connection status monitoring
- Uptime tracking
- Error collection and reporting

#### Service Architecture
- Service manager orchestration pattern
- Modular service design for extensibility
- Thread-safe shutdown coordination
- Background task management
- Event-driven architecture

### Infrastructure
- Multi-architecture support (amd64, aarch64, armhf, armv7, i386)
- Optimized Docker build with caching
- Production-ready dependency pinning
- Data persistence with volume mounts
- Comprehensive .dockerignore for build optimization

### Documentation
- Complete README with installation instructions
- Configuration examples and schema documentation
- Troubleshooting guide
- MQTT topic reference
- Health check endpoint documentation

### Dependencies
- paho-mqtt 1.6.1 - MQTT client
- scikit-learn 1.3.2 - Machine learning
- pandas 2.1.4 - Data manipulation
- numpy 1.26.2 - Numerical computing
- flask 3.0.0 - HTTP server
- pydantic 2.5.2 - Data validation
- python-json-logger 2.0.7 - Structured logging
- tenacity 8.2.3 - Retry logic
- requests 2.31.0 - HTTP client for HA API

### Configuration Options
- MQTT broker connection settings
- Per-sensor topic and metadata configuration
- ML prediction and training parameters
- Alert threshold and cooldown settings
- Logging level and format options
- Data directory paths
- Health check intervals
- Graceful shutdown timeout

## [Unreleased]

### Planned Features
- Data collector service for sensor readings
- ML prediction service with model persistence
- Alert manager with notification cooldown
- Home Assistant entity publishing
- Real-time fermentation stage detection
- Historical data analytics
- Web dashboard for visualization
- Export data to CSV/Excel
- Backup and restore functionality
- Multi-batch monitoring support
- Integration with popular fermentation hardware
- Custom notification channels (email, Telegram, etc.)

### Planned Improvements
- AsyncIO MQTT client for better performance
- SQLite database for historical data
- GraphQL API for advanced queries
- WebSocket support for real-time updates
- Unit and integration tests
- CI/CD pipeline with GitHub Actions
- Automated Docker image publishing
- Translation support (i18n)

---

## Version History

- **1.0.0** - Initial release with core infrastructure
- **Unreleased** - Features planned for future releases

## Migration Guide

### From Development to 1.0.0

This is the initial release. No migration needed.

## Breaking Changes

### 1.0.0

None - initial release

## Security

### 1.0.0
- MQTT authentication support
- Secure credential handling via Home Assistant Supervisor
- No hardcoded secrets
- Read-only SSL certificate access
- Proper permission boundaries

## Known Issues

### 1.0.0
- ML services not yet implemented (planned for 1.1.0)
- Data collector service placeholder (planned for 1.1.0)
- Alert manager not yet active (planned for 1.1.0)

## Support

For issues, feature requests, or questions:
- GitHub Issues: https://github.com/tipsyhomelab/wine-fermentation-monitor/issues
- Documentation: https://github.com/tipsyhomelab/wine-fermentation-monitor/wiki
