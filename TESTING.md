# Testing Guide for Wine Monitor

This document provides comprehensive information about the testing infrastructure.

## Test Structure

### Test Files

- **test_mqtt_handler.py** (281 lines)
  - MQTT connection and disconnection
  - Topic subscription
  - Message parsing (JSON, malformed data)
  - Message publishing
  - Error handling
  - Topic pattern matching

- **test_sensors.py** (333 lines)
  - Sensor data validation
  - iSpindel sensor functionality
  - Bubble sensor functionality
  - Data sanity checks
  - Multi-sensor handling

- **test_ml_engine.py** (441 lines)
  - Model predictions
  - Training functionality
  - Accuracy metrics
  - Feature engineering
  - Model persistence
  - Anomaly detection

- **test_data_manager.py** (575 lines)
  - Database connection
  - Data insertion (single and bulk)
  - Querying (time range, aggregates)
  - Updates and deletions
  - Data retention
  - Backup functionality
  - Transaction management

### Test Fixtures

Located in `tests/fixtures/`:

1. **sample_fermentation_data.json**
   - 2 fermentation batches
   - Complete time series data
   - ML training samples

2. **ispindel_messages.json**
   - Valid message examples
   - Invalid message examples
   - Calibration data
   - MQTT topic patterns

3. **bubble_sensor_data.json**
   - Valid sensor messages
   - Invalid message examples
   - Time series data
   - Fermentation phase definitions

### Pytest Fixtures (conftest.py)

- `mock_mqtt_client` - Mock MQTT client
- `mock_database` - Mock database connection
- `mock_ml_model` - Mock ML model
- `sample_ispindel_message` - Sample iSpindel data
- `sample_bubble_sensor_data` - Sample bubble sensor data
- `sample_fermentation_data` - Sample fermentation data
- `mqtt_message_factory` - Factory for creating MQTT messages
- `mock_time_series_data` - Generated time series data

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_mqtt_handler.py -v

# Run specific test class
pytest tests/test_sensors.py::TestSensorDataValidation -v

# Run specific test
pytest tests/test_mqtt_handler.py::TestMQTTConnection::test_mqtt_connect_success -v
```

### Coverage Reports

```bash
# Run with coverage
pytest tests/ --cov=custom_components --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Markers

```bash
# Run only unit tests
pytest tests/ -v -m unit

# Run only integration tests
pytest tests/ -v -m integration

# Skip slow tests
pytest tests/ -v -m "not slow"
```

## CI/CD Pipeline

### CI Workflow (.github/workflows/ci.yml)

Runs on every push and PR:

1. **Linting**
   - black (code formatting)
   - isort (import sorting)
   - flake8 (style guide)
   - pylint (code quality)

2. **Testing**
   - Python 3.10, 3.11, 3.12
   - MQTT broker service
   - PostgreSQL service
   - Coverage reporting

3. **Validation**
   - HACS validation

4. **Build**
   - Docker image build

5. **Integration Tests**
   - Full stack testing

6. **Security**
   - Trivy vulnerability scanning
   - Bandit security checks

### Release Workflow (.github/workflows/release.yml)

Triggered on release:

1. **Validation**
   - Run full test suite
   - Validate manifest

2. **Publishing**
   - Publish to HACS
   - Build Docker images (multi-platform)
   - Create GitHub release
   - Upload release assets

## Validation Schemas

Located in `custom_components/wine_monitor/validators.py`:

### Config Validation
- MQTT broker settings
- Port ranges
- Topic patterns
- Update intervals

### Sensor Data Validation
- Temperature: -10°C to 50°C
- Gravity: 0.990 to 1.150
- Battery: 0V to 5V
- Angle: 0° to 90°
- RSSI: -100 to 0 dBm

### Sanity Checks
- Gravity trend monitoring
- Temperature stability
- Battery degradation
- Bubble rate lifecycle
- Statistical anomaly detection

## Development Workflow

### 1. Setup

```bash
./scripts/test_setup.sh
source venv/bin/activate
```

### 2. Make Changes

Edit code in `custom_components/wine_monitor/`

### 3. Run Tests

```bash
pytest tests/ -v
```

### 4. Check Coverage

```bash
pytest tests/ --cov=custom_components --cov-report=term
```

### 5. Format Code

```bash
black .
isort .
```

### 6. Run Linters

```bash
flake8 .
pylint custom_components/
```

### 7. Commit

```bash
git add .
git commit -m "feat: description"
```

Pre-commit hooks will run automatically.

## Local Testing with Docker

### Start Services

```bash
docker-compose up -d mqtt postgres
```

### Simulate Sensors

```bash
python scripts/simulate_sensors.py
```

Or in Docker:

```bash
docker-compose up mqtt-publisher
```

### Run Tests in Docker

```bash
docker-compose --profile test up test-runner
```

## Test Data

### Generate Test Data

The `simulate_sensors.py` script generates realistic fermentation data:

- Lag phase (Day 0-1)
- Exponential phase (Day 1-3)
- Stationary phase (Day 3-10)
- Finishing phase (Day 10+)

### Customize Simulation

```bash
MQTT_BROKER=localhost \
MQTT_PORT=1883 \
SIMULATION_DAYS=7 \
SIMULATION_INTERVAL=30 \
python scripts/simulate_sensors.py
```

## Troubleshooting

### Tests Fail to Connect to MQTT

1. Ensure MQTT broker is running:
   ```bash
   docker-compose up -d mqtt
   ```

2. Check MQTT_BROKER environment variable:
   ```bash
   export MQTT_BROKER=localhost
   export MQTT_PORT=1883
   ```

### Database Connection Errors

1. Start PostgreSQL:
   ```bash
   docker-compose up -d postgres
   ```

2. Check connection:
   ```bash
   docker-compose exec postgres psql -U wine_user -d wine_monitor
   ```

### Import Errors

1. Ensure virtual environment is activated:
   ```bash
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

## Best Practices

1. **Write tests first** (TDD approach)
2. **Keep tests isolated** (use fixtures and mocks)
3. **Test edge cases** (invalid data, errors, timeouts)
4. **Maintain high coverage** (aim for >80%)
5. **Use descriptive test names**
6. **Group related tests** (use test classes)
7. **Clean up resources** (use fixtures with teardown)
8. **Document complex tests** (add docstrings)

## Resources

- pytest documentation: https://docs.pytest.org/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- unittest.mock: https://docs.python.org/3/library/unittest.mock.html
- Coverage.py: https://coverage.readthedocs.io/
