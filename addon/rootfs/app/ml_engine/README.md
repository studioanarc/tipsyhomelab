# Adaptive ML Engine for Wine Production Monitoring

A comprehensive machine learning system for predicting Pet Nat bottling times and detecting fermentation anomalies. The engine adapts to variable sensor configurations, providing tiered predictions based on available data.

## Features

- **Adaptive Model Selection**: Automatically selects appropriate model tier (MINIMAL, BASIC, ADVANCED) based on available sensors
- **Tiered Predictions**: Three prediction models with increasing accuracy
- **Anomaly Detection**: Multi-strategy detection of fermentation problems
- **Uncertainty Quantification**: Confidence scores and prediction intervals
- **Feature Engineering**: Comprehensive extraction of time-series features
- **Retraining Pipeline**: Easy model retraining with new data
- **Lightweight**: Fast predictions, suitable for embedded systems

## Architecture

```
ml_engine/
├── __init__.py                 # Package exports
├── model_manager.py            # Centralized model management
├── feature_engineering.py      # Time-series feature extraction
├── petnat_predictor.py         # Bottling time prediction models
├── anomaly_detector.py         # Fermentation anomaly detection
├── training_pipeline.py        # Model training and retraining
├── models.py                   # Model selection and uncertainty
└── pretrained/                 # Pre-trained model files
    ├── minimal_model.pkl
    ├── basic_model.pkl
    ├── advanced_model.pkl
    ├── anomaly_detector.pkl
    └── metadata.json
```

## Quick Start

### Basic Usage

```python
from ml_engine import ModelManager
import numpy as np

# Initialize model manager
manager = ModelManager()

# Prepare your fermentation data
timestamps = np.array([...])        # Unix timestamps or datetime objects
bubble_counts = np.array([...])     # Bubbles per minute
gravity = np.array([...])           # Specific gravity (optional)
temperature = np.array([...])       # Temperature in Celsius (optional)
ph = np.array([...])                # pH readings (optional)

# Create prediction pipeline
pipeline = manager.create_prediction_pipeline()

# Get predictions and anomalies
results = pipeline(
    timestamps=timestamps,
    bubble_counts=bubble_counts,
    gravity=gravity,
    temperature=temperature,
    ph=ph
)

# Access results
print(f"Hours to bottle: {results['prediction']['value']:.1f}")
print(f"Confidence: {results['prediction']['confidence']:.2%}")
print(f"Model tier: {results['prediction']['model_tier']}")
print(f"Health score: {results['health_score']:.1f}/100")

# Check anomalies
for anomaly in results['anomalies']:
    if anomaly['severity'] == 'critical':
        print(f"⚠️  {anomaly['description']}")
        print(f"   → {anomaly['recommendation']}")
```

### Individual Components

```python
from ml_engine import PetNatPredictor, AnomalyDetector, FeatureEngineer

# 1. Feature Engineering
engineer = FeatureEngineer()
features = engineer.extract_all_features(
    timestamps=timestamps,
    bubble_counts=bubble_counts,
    gravity=gravity
)
print(f"Extracted {len(features)} features")

# 2. Bottling Prediction
predictor = PetNatPredictor()
prediction = predictor.predict(
    timestamps=timestamps,
    bubble_counts=bubble_counts,
    gravity=gravity
)
print(f"Prediction: {prediction.value:.1f}h ± {prediction.uncertainty_upper - prediction.value:.1f}h")
print(f"Confidence: {prediction.confidence:.2%}")

# 3. Anomaly Detection
detector = AnomalyDetector()
anomalies = detector.detect_anomalies(
    timestamps=timestamps,
    bubble_counts=bubble_counts,
    gravity=gravity,
    temperature=temperature
)
summary = detector.get_summary(anomalies)
print(f"Status: {summary['status']}")
print(f"Critical issues: {summary['critical_count']}")
```

## Prediction Models

### MINIMAL Model (Bubble Count Only)

**Sensors Required**: Bubble counter only

**Algorithm**:
- Exponential decay curve fitting: `bubble_rate(t) = A * exp(-k*t) + C`
- Extrapolates to target bubble rate (1-2 bubbles/min)
- Rule-based thresholds

**Advantages**:
- Works with minimal hardware
- No training data required
- Fast and interpretable

**Accuracy**: Moderate (±15-20 hours typical)

### BASIC Model (Bubble + Gravity)

**Sensors Required**: Bubble counter + Gravity sensor (iSpindel)

**Algorithm**:
- Polynomial regression on gravity curve
- CO2 vs gravity correlation analysis
- Weighted ensemble of bubble and gravity predictions

**Advantages**:
- Much better accuracy than MINIMAL
- Accounts for actual fermentation progress
- Can detect stuck fermentation

**Accuracy**: Good (±8-12 hours typical)

### ADVANCED Model (All Sensors)

**Sensors Required**: Bubble counter + Gravity + Temperature + pH

**Algorithm**:
- Gradient Boosting Regressor (ensemble of decision trees)
- Temperature-compensated fermentation rate
- pH consideration for yeast health
- Multi-variate time series features

**Advantages**:
- Highest accuracy
- Robust to environmental variations
- Provides uncertainty estimates

**Accuracy**: Best (±3-6 hours with trained model, ±8-12 hours with rule-based fallback)

## Anomaly Detection

The anomaly detector identifies fermentation problems using multiple strategies:

### Detected Anomalies

1. **Stuck Fermentation**
   - Flat bubble rate for 24+ hours
   - Flat gravity while still > 1.002 SG
   - Severity: CRITICAL

2. **Too Fast Fermentation**
   - Excessive bubble rate (>30 bubbles/min early)
   - Risk of over-carbonation
   - Severity: WARNING

3. **Temperature Anomalies**
   - Too hot (>28°C): Stressed yeast
   - Too cold (<12°C): Slow/stuck fermentation
   - Unstable (high variance): Inconsistent conditions
   - Severity: WARNING to CRITICAL

4. **pH Anomalies**
   - Too low (<2.8): Possible infection
   - Too high (>4.2): Unusual for wine
   - Rapid changes: Bacterial activity
   - Severity: WARNING to CRITICAL

5. **Statistical Outliers**
   - Isolation Forest detection
   - Pattern-based anomalies
   - Severity: INFO

### Health Score

Overall fermentation health score (0-100):
- **100**: Perfect, no anomalies
- **75-99**: Good, minor issues
- **50-74**: Fair, monitor closely
- **25-49**: Poor, intervention recommended
- **0-24**: Critical, immediate action required

## Feature Engineering

Extracts 50+ features from time-series data:

### Bubble Features
- Current rate, mean, std, max, min
- Rate of change (velocity, acceleration)
- Cumulative CO2 production
- Exponential decay fitting
- Peak detection
- Time to threshold estimation

### Gravity Features
- Current gravity, start gravity, delta
- Apparent attenuation percentage
- Rate of gravity drop
- Polynomial curve fitting
- Predicted gravity in 24h
- Time to target gravity

### Temperature Features
- Current, mean, std, range
- Recent trends
- Variability metrics

### pH Features
- Current, start, delta
- Trend analysis

### Cross-Sensor Features
- Bubble-gravity correlation
- CO2 per gravity point
- Temperature-compensated bubble rate
- Bubble-temperature correlation

### Temporal Features
- Fermentation age (hours/days)
- Measurement count
- Measurement frequency

## Model Training

### Collecting Training Data

```python
from ml_engine.training_pipeline import TrainingDataset, TrainingPipeline

# Create dataset
dataset = TrainingDataset()

# Add completed fermentations with labels
dataset.add_fermentation(
    fermentation_id="batch_2024_001",
    timestamps=timestamps,
    bubble_counts=bubble_counts,
    gravity=gravity,
    temperature=temperature,
    ph=ph,
    actual_hours_to_bottle=72.5,  # Actual measured time
    metadata={
        'wine_type': 'Pet Nat Chenin Blanc',
        'yeast_strain': 'EC-1118',
        'starting_gravity': 1.048,
        'fermentation_temp': 18.5
    }
)

# Add more fermentations...
# (Recommend 20+ for BASIC, 50+ for ADVANCED)

# Save dataset
dataset.save('training_data.json')
```

### Training Models

```python
# Initialize training pipeline
pipeline = TrainingPipeline(output_dir='./pretrained')

# Train all models
results = pipeline.run_full_pipeline(
    dataset=dataset,
    train_basic=True,
    train_advanced=True,
    train_anomaly=True
)

# Check results
print(f"BASIC model - Test MAE: {results['models']['basic']['metrics']['test_mae']:.2f}h")
print(f"ADVANCED model - Test MAE: {results['models']['advanced']['metrics']['test_mae']:.2f}h")
```

### Evaluating Models

```python
# Evaluate on separate test set
test_dataset = TrainingDataset()
test_dataset.load('test_data.json')

metrics = pipeline.evaluate_model(
    model_path='./pretrained/advanced_model.pkl',
    test_dataset=test_dataset
)

print(f"Test MAE: {metrics['mae']:.2f}h")
print(f"Test R²: {metrics['r2']:.3f}")
```

## Model Selection Logic

The system automatically selects the best model based on:

1. **Sensor Availability**: Which sensors have valid data
2. **Data Quality**: Sufficient measurement history and consistency
3. **Model Availability**: Whether pre-trained models exist

Selection hierarchy:
```
ADVANCED → If all sensors available AND data quality ≥ 0.8
BASIC    → If bubble + gravity available AND data quality ≥ 0.6
MINIMAL  → If bubble counter available (fallback)
```

## Uncertainty Quantification

All predictions include:

- **Point Prediction**: Best estimate (hours to bottle)
- **Confidence Score**: 0-1 (higher = more confident)
- **Prediction Interval**: Lower and upper bounds
- **Warnings**: Data quality issues

Confidence based on:
- Model tier (ADVANCED > BASIC > MINIMAL)
- Data quality (age, measurement count, consistency)
- Model fit quality (R² scores)
- Cross-sensor agreement

## Dependencies

### Required
```
numpy>=1.20.0
scipy>=1.7.0
scikit-learn>=1.0.0
joblib>=1.0.0
```

### Optional (for development)
```
pandas>=1.3.0
matplotlib>=3.4.0
jupyter>=1.0.0
```

## Installation

```bash
# Install dependencies
pip install numpy scipy scikit-learn joblib

# Optional: Create baseline models
cd pretrained/
python create_baseline_models.py

# Or use placeholders (rule-based fallback)
python create_placeholder_models.py
```

## Performance

- **Prediction time**: <10ms on Raspberry Pi 4
- **Memory usage**: ~50MB with all models loaded
- **Training time**:
  - BASIC: ~1s for 100 samples
  - ADVANCED: ~10s for 100 samples

## Best Practices

1. **Data Collection**
   - Collect measurements every 15-30 minutes
   - Ensure at least 6 hours of data before first prediction
   - Maintain consistent measurement intervals

2. **Sensor Calibration**
   - Calibrate gravity sensor before each fermentation
   - Verify temperature sensor accuracy (±0.5°C)
   - Check pH sensor calibration weekly

3. **Model Retraining**
   - Retrain after every 10-20 fermentations
   - Use consistent wine styles for better accuracy
   - Keep separate models for different wine types if needed

4. **Anomaly Monitoring**
   - Check health score at least daily
   - Act on CRITICAL anomalies immediately
   - Log WARNING anomalies for pattern analysis

## Troubleshooting

### Low Confidence Predictions
- **Cause**: Insufficient data, poor sensor quality
- **Fix**: Wait for more measurements, check sensor calibration

### Model Selection Warnings
- **Cause**: Data quality issues
- **Fix**: Review warnings, improve measurement consistency

### High Error Rates
- **Cause**: Untrained models, inconsistent fermentations
- **Fix**: Train on real data, ensure consistent conditions

## Examples

See `/examples` directory for:
- `basic_prediction.py`: Simple prediction example
- `anomaly_monitoring.py`: Continuous anomaly detection
- `model_training.py`: Complete training workflow
- `api_integration.py`: REST API integration

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/tipsyhomelab/issues
- Documentation: https://tipsyhomelab.readthedocs.io
