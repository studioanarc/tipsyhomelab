# Wine Monitor - Home Assistant Integration

A comprehensive Home Assistant integration for monitoring wine fermentation using IoT sensors (iSpindel and bubble counters).

## Features

- **Real-time Monitoring**: Track fermentation progress with iSpindel and bubble sensor data
- **MQTT Integration**: Seamless integration with MQTT brokers
- **ML-Powered Predictions**: Machine learning engine predicts fermentation completion
- **Data Persistence**: PostgreSQL database for long-term data storage
- **Grafana Dashboards**: Beautiful visualizations of fermentation data
- **Automated Testing**: Comprehensive test suite with CI/CD pipelines

## Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (optional, for local testing)
- Home Assistant instance
- MQTT Broker (e.g., Mosquitto)

### Installation

1. Clone the repository
2. Run setup script: `./scripts/test_setup.sh`
3. Activate virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements-dev.txt`

### Development Setup

Start all services:
```bash
docker-compose up -d
```

Run tests:
```bash
pytest tests/ -v --cov=custom_components
```

## Project Structure

- `.github/workflows/` - CI/CD pipelines
- `custom_components/wine_monitor/` - Integration code
- `tests/` - Test suite
- `scripts/` - Utility scripts
- `docker-compose.yml` - Local development environment

## License

MIT
