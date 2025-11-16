# Contributing to TipsyHomeLab

Thank you for your interest in contributing to TipsyHomeLab! This document provides guidelines for contributing to the project.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How Can I Contribute?](#how-can-i-contribute)
3. [Development Setup](#development-setup)
4. [Coding Guidelines](#coding-guidelines)
5. [Submitting Changes](#submitting-changes)
6. [Reporting Bugs](#reporting-bugs)
7. [Suggesting Enhancements](#suggesting-enhancements)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, background, or identity.

### Expected Behavior

- Be respectful and considerate
- Welcome newcomers and help them get started
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment or discrimination of any kind
- Trolling, insulting comments, or personal attacks
- Publishing others' private information
- Other conduct that could reasonably be considered inappropriate

---

## How Can I Contribute?

### Reporting Bugs

Found a bug? Help us fix it!

**Before submitting:**
1. Check if the bug has already been reported
2. Verify it's not due to misconfiguration
3. Test with the latest version

**When submitting:**
- Use the bug report template
- Include detailed steps to reproduce
- Provide logs and error messages
- Specify your environment (HA version, sensors, etc.)

### Suggesting Enhancements

Have an idea? We'd love to hear it!

**Good enhancement suggestions include:**
- Clear use case description
- Expected behavior
- Why this would be useful to others
- Mockups or examples (if applicable)

### Adding Sensor Support

Want to add support for a new sensor?

1. Check if sensor communicates via MQTT (or can be bridged)
2. Document the sensor's message format
3. Add parser in `sensor.py`
4. Update `SENSORS.md` with wiring diagrams
5. Add example messages in `examples/mqtt_examples/`
6. Test thoroughly
7. Submit pull request

### Improving Documentation

Documentation contributions are highly valued!

- Fix typos or unclear explanations
- Add examples and tutorials
- Translate to other languages
- Add diagrams or illustrations
- Improve code comments

### Writing Code

Code contributions welcome!

**Areas that need help:**
- Additional ML models
- New sensor integrations
- Dashboard card improvements
- Testing and test coverage
- Performance optimizations
- Bug fixes

---

## Development Setup

### Prerequisites

```bash
# Required
- Python 3.9+
- Git
- Home Assistant development environment
- MQTT broker (Mosquitto)

# Recommended
- Docker & Docker Compose
- Pre-commit hooks
- IDE with Python support (VS Code, PyCharm)
```

### Setting Up Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/tipsyhomelab.git
   cd tipsyhomelab
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

5. **Set Up Testing Environment**
   ```bash
   # Start MQTT broker and test services
   docker-compose up -d
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=custom_components/tipsyhomelab --cov-report=html

# Run specific test file
pytest tests/test_predictions.py

# Run with verbose output
pytest -v
```

### Manual Testing

```bash
# Copy to Home Assistant custom_components
cp -r custom_components/tipsyhomelab /config/custom_components/

# Restart Home Assistant
ha core restart

# Check logs
ha core logs | grep tipsyhomelab
```

---

## Coding Guidelines

### Python Style

Follow PEP 8 and Home Assistant coding standards:

```python
# Good: Clear variable names, type hints, docstrings
def calculate_pressure(
    gravity_points: float,
    temperature: float = 20.0
) -> float:
    """
    Calculate bottle pressure from remaining gravity points.

    Args:
        gravity_points: Remaining gravity points (current - final)
        temperature: Temperature in Celsius (default: 20.0)

    Returns:
        Predicted pressure in bar
    """
    co2_g_per_l = gravity_points * 1.6
    pressure_bar = co2_g_per_l * 0.5
    temp_correction = 1 + 0.009 * (temperature - 20)
    return pressure_bar * temp_correction

# Bad: Unclear, no types, no docs
def calc(g, t=20):
    return g * 1.6 * 0.5 * (1 + 0.009 * (t - 20))
```

### Code Organization

```python
# Standard library imports first
import logging
from datetime import datetime

# Third-party imports
import numpy as np
from homeassistant.core import HomeAssistant

# Local imports
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .ml import PredictionEngine
```

### Type Hints

Always use type hints:

```python
from typing import Dict, List, Optional

def process_sensor_data(
    data: Dict[str, float],
    sensors: List[str],
    timeout: Optional[int] = None
) -> bool:
    """Process sensor data."""
    pass
```

### Logging

Use appropriate log levels:

```python
import logging

_LOGGER = logging.getLogger(__name__)

# DEBUG: Detailed debugging information
_LOGGER.debug("Processing sensor data: %s", data)

# INFO: General informational messages
_LOGGER.info("Fermentation batch '%s' started", batch_name)

# WARNING: Warning messages for recoverable issues
_LOGGER.warning("Sensor offline, using cached data")

# ERROR: Error messages for failures
_LOGGER.error("Failed to connect to MQTT broker: %s", error)

# CRITICAL: Critical errors requiring immediate attention
_LOGGER.critical("Predicted pressure exceeds safe limits!")
```

### Documentation

All functions should have docstrings:

```python
def predict_completion_date(
    bubble_rate: List[float],
    timestamps: List[int],
    model: str = "auto"
) -> Dict[str, Any]:
    """
    Predict fermentation completion date using ML model.

    Uses historical bubble rate data to predict when fermentation
    will complete (< 2 bubbles/min sustained for 24 hours).

    Args:
        bubble_rate: List of bubble rate measurements (bubbles/min)
        timestamps: Unix timestamps for each measurement (milliseconds)
        model: Model type ("auto", "linear", "polynomial", "gradient_boosting")

    Returns:
        Dictionary containing:
        - predicted_date: ISO format date string
        - confidence: Confidence score (0.0-1.0)
        - confidence_interval: Dict with 'lower' and 'upper' bounds

    Raises:
        ValueError: If insufficient data (< 48 hours)
        ModelError: If prediction fails

    Example:
        >>> bubble_rates = [45.2, 43.1, 40.3, 38.2]
        >>> timestamps = [1699900000000, 1699903600000, ...]
        >>> result = predict_completion_date(bubble_rates, timestamps)
        >>> print(result['predicted_date'])
        '2024-11-20T14:30:00Z'
    """
    pass
```

### Testing

Write tests for all new functionality:

```python
import pytest
from custom_components.tipsyhomelab.predictions import calculate_pressure

def test_pressure_calculation_standard_temp():
    """Test pressure calculation at standard temperature."""
    gravity_points = 5.0
    pressure = calculate_pressure(gravity_points, temperature=20.0)
    assert pressure == pytest.approx(4.0, rel=0.01)

def test_pressure_calculation_cold_temp():
    """Test pressure calculation at cold temperature."""
    gravity_points = 5.0
    pressure = calculate_pressure(gravity_points, temperature=10.0)
    # Pressure should be ~10% lower at 10°C
    assert pressure < 4.0
    assert pressure == pytest.approx(3.64, rel=0.01)

def test_pressure_calculation_invalid_input():
    """Test pressure calculation with invalid input."""
    with pytest.raises(ValueError):
        calculate_pressure(-1.0)  # Negative gravity points
```

---

## Submitting Changes

### Pull Request Process

1. **Create a Branch**
   ```bash
   git checkout -b feature/my-new-feature
   # or
   git checkout -b fix/bug-description
   ```

2. **Make Changes**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation
   - Follow coding guidelines

3. **Test Thoroughly**
   ```bash
   # Run tests
   pytest

   # Run linters
   flake8 custom_components/
   pylint custom_components/

   # Check formatting
   black --check custom_components/
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "Add feature: brief description

   Detailed explanation of what this commit does and why.

   - Bullet point 1
   - Bullet point 2

   Fixes #123"
   ```

5. **Push to Your Fork**
   ```bash
   git push origin feature/my-new-feature
   ```

6. **Create Pull Request**
   - Go to GitHub and create PR
   - Use the PR template
   - Link related issues
   - Add screenshots if applicable
   - Request review

### Commit Message Guidelines

Follow conventional commits:

```
feat: Add support for Tilt Pro hydrometer
fix: Correct pressure calculation for cold temperatures
docs: Update sensor setup guide with wiring diagrams
test: Add tests for prediction confidence intervals
refactor: Simplify MQTT message parsing
perf: Optimize prediction model training
chore: Update dependencies
```

### PR Requirements

Before submitting, ensure:
- [ ] All tests pass
- [ ] Code is properly formatted (black, isort)
- [ ] Linting passes (flake8, pylint)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No merge conflicts
- [ ] Commits are clean and well-described

### Review Process

1. Automated checks run (CI/CD)
2. Maintainer reviews code
3. Address feedback
4. Approval and merge

---

## Reporting Bugs

### Bug Report Template

```markdown
**Describe the Bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Configure '...'
2. Start fermentation '...'
3. Wait for '...'
4. See error

**Expected Behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - Home Assistant Version: [e.g., 2023.11]
 - TipsyHomeLab Version: [e.g., 1.0.2]
 - Sensors: [e.g., iSpindel, bubble counter]
 - MQTT Broker: [e.g., Mosquitto 2.0]

**Logs**
```
Paste relevant logs here
```

**Additional Context**
Any other context about the problem.
```

---

## Suggesting Enhancements

### Enhancement Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem. Ex. I'm frustrated when [...]

**Describe the solution you'd like**
Clear and concise description of what you want.

**Describe alternatives you've considered**
Other solutions or features you've considered.

**Additional context**
Screenshots, mockups, examples, etc.

**Would you be willing to contribute this?**
Yes/No - We can help you get started!
```

---

## Questions?

- Open a [Discussion](https://github.com/yourusername/tipsyhomelab/discussions)
- Join our [Discord](https://discord.gg/tipsyhomelab)
- Email: contribute@tipsyhomelab.com

---

## Recognition

Contributors are recognized in:
- README.md acknowledgments section
- CHANGELOG.md for significant contributions
- GitHub contributors page

---

Thank you for contributing to TipsyHomeLab! Together we're making fermentation monitoring accessible to everyone. 🍾
