# Changelog

All notable changes to TipsyHomeLab will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned Features
- Multi-language support (French, German, Italian)
- Mobile app for notifications and monitoring
- Integration with brewing software (Brewfather, Brewersfriend)
- Computer vision for foam analysis
- Automatic recipe import
- Community data sharing (opt-in)
- LSTM neural network predictions
- Pressure sensor auto-calibration

---

## [1.0.0] - 2024-11-16

### Added - Initial Release

#### Core Features
- **MQTT Integration**: Full MQTT support for sensor communication
- **Multi-Sensor Support**:
  - Bubble counters (optical and acoustic)
  - iSpindel hydrometers
  - Tilt hydrometers
  - DS18B20 temperature sensors
  - Atlas Scientific pH sensors
  - Pressure transducers
- **Machine Learning Predictions**:
  - Automatic fermentation completion prediction
  - Final gravity prediction
  - Bottle pressure calculation for Pet Nat
  - Multiple ML models (linear, polynomial, gradient boosting)
  - Confidence intervals for all predictions
- **Pet Nat Specialization**:
  - Bottling window detection
  - Pressure safety calculations
  - Temperature-compensated predictions
  - CO2 volume tracking
- **Alerting System**:
  - Fermentation lifecycle alerts
  - Safety warnings (high pressure, temperature)
  - Sensor health monitoring
  - Customizable notification channels
  - Quiet hours configuration
- **Home Assistant Integration**:
  - MQTT auto-discovery
  - Custom Lovelace cards
  - Entity attributes
  - Services for manual control
- **Data Management**:
  - InfluxDB integration
  - CSV export
  - Historical data compression
  - Configurable retention policies

#### Documentation
- Comprehensive README with quick start guide
- Complete installation guide
- Sensor setup guide with wiring diagrams
- Configuration reference
- ML models explanation
- MQTT API documentation
- Pet Nat production guide
- Fermentation theory documentation
- Troubleshooting guide
- Example configurations
- Dashboard templates

#### Examples
- Minimal configuration (bubble counter only)
- iSpindel + bubble counter setup
- Full sensor suite configuration
- MQTT message examples
- Lovelace dashboard templates
- Automation examples

#### Developer Tools
- Comprehensive test suite
- CI/CD pipeline
- Pre-commit hooks
- Code formatting (black, isort)
- Linting (flake8, pylint)
- Type checking (mypy)

### Security
- MQTT authentication support
- TLS/SSL support for MQTT
- Secure credential storage
- Input validation
- Safe default configurations

---

## Version History

### Version Number Format

`MAJOR.MINOR.PATCH`

- **MAJOR**: Incompatible API changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Schedule

- **Major releases**: Annually or for breaking changes
- **Minor releases**: Quarterly for new features
- **Patch releases**: As needed for bug fixes

---

## Upgrading

### From Pre-Release to 1.0.0

First official release - no upgrade path needed.

### Future Upgrade Notes

Upgrade instructions will be provided here for each major version change.

---

## Breaking Changes

### v1.0.0
No breaking changes (initial release).

---

## Known Issues

### v1.0.0

1. **LSTM Model Performance**
   - LSTM predictions require significant computational resources
   - Recommended to use gradient boosting for Raspberry Pi installations
   - GPU recommended for LSTM model

2. **Multiple Batch Limits**
   - Performance may degrade with >5 simultaneous batches
   - Consider using lighter prediction models for multiple batches

3. **Historical Data Migration**
   - No automatic migration from other fermentation monitoring systems
   - Manual CSV import required

### Workarounds

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for workarounds and solutions.

---

## Deprecation Notices

### v1.0.0
No deprecations (initial release).

---

## Credits

### v1.0.0 Contributors

- **Core Development**: TipsyHomeLab Team
- **Documentation**: Community Contributors
- **Testing**: Beta Testers
- **Sensor Support**: Hardware Community

### Special Thanks

- iSpindel project for pioneering DIY fermentation monitoring
- Tilt Hydrometer team
- Home Assistant community
- Pet Nat winemakers who provided feedback
- All beta testers and early adopters

---

## Support

For issues and questions:
- [GitHub Issues](https://github.com/yourusername/tipsyhomelab/issues)
- [GitHub Discussions](https://github.com/yourusername/tipsyhomelab/discussions)
- [Discord Community](https://discord.gg/tipsyhomelab)

---

## Links

- [Documentation](https://github.com/yourusername/tipsyhomelab/tree/main/docs)
- [Installation Guide](docs/INSTALLATION.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [License](LICENSE)

---

**Legend:**
- `Added` - New features
- `Changed` - Changes in existing functionality
- `Deprecated` - Soon-to-be removed features
- `Removed` - Removed features
- `Fixed` - Bug fixes
- `Security` - Security improvements

---

[Unreleased]: https://github.com/yourusername/tipsyhomelab/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/tipsyhomelab/releases/tag/v1.0.0
