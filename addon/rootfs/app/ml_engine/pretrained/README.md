# Pre-trained Models Directory

This directory contains pre-trained baseline models for wine fermentation monitoring.

## Models

### minimal_model.pkl
- **Type**: Rule-based (metadata only)
- **Sensors**: Bubble counter only
- **Algorithm**: Exponential decay curve fitting
- **Accuracy**: Moderate
- **Use case**: When only bubble counter is available

### basic_model.pkl
- **Type**: Ridge Regression
- **Sensors**: Bubble counter + Gravity (iSpindel)
- **Features**: ~10 features (bubble metrics, gravity metrics, correlation)
- **Accuracy**: Good
- **Use case**: When bubble counter and gravity sensor available

### advanced_model.pkl
- **Type**: Gradient Boosting Regressor
- **Sensors**: All sensors (bubble, gravity, temperature, pH)
- **Features**: ~20 features (comprehensive multi-variate analysis)
- **Accuracy**: Best
- **Use case**: When all sensors available

### anomaly_detector.pkl
- **Type**: Isolation Forest + Rule-based
- **Purpose**: Detect fermentation anomalies
- **Detects**: Stuck fermentation, temperature issues, pH problems, outliers
- **Output**: Anomaly list with severity and recommendations

## Creating Models

### Option 1: Use Baseline Models (Synthetic Data)

Run the creation script to generate baseline models:

```bash
cd /addon/rootfs/app/ml_engine/pretrained
pip install numpy scikit-learn joblib scipy
python create_baseline_models.py
```

**Note**: These baseline models are trained on synthetic data and should be replaced with real fermentation data for production use.

### Option 2: Train on Real Data

Use the training pipeline with real fermentation data:

```python
from ml_engine.training_pipeline import TrainingDataset, TrainingPipeline

# Create dataset
dataset = TrainingDataset()

# Add fermentation data
dataset.add_fermentation(
    fermentation_id="batch_001",
    timestamps=timestamps,
    bubble_counts=bubble_counts,
    gravity=gravity,
    temperature=temperature,
    ph=ph,
    actual_hours_to_bottle=72.5  # Actual measured time
)

# Add more fermentations...

# Train models
pipeline = TrainingPipeline(output_dir="./pretrained")
results = pipeline.run_full_pipeline(dataset)
```

## Model Format

All models are saved using joblib (pickle) format with the following structure:

```python
{
    'model': <sklearn model instance>,
    'scaler': <StandardScaler instance>,
    'feature_names': ['feature1', 'feature2', ...],
    'model_type': 'gradient_boosting',
    'model_tier': 'advanced',
    'n_samples': 100,
    'trained_at': '2025-01-01T12:00:00',
    'metrics': {
        'test_mae': 8.5,  # Mean absolute error in hours
        'test_r2': 0.85,  # R² score
        ...
    }
}
```

## Using Pre-trained Models

```python
from ml_engine import ModelManager

# Initialize model manager
manager = ModelManager(model_dir="./pretrained")

# Get predictor
predictor = manager.petnat_predictor

# Make prediction
result = predictor.predict(
    timestamps=timestamps,
    bubble_counts=bubble_counts,
    gravity=gravity,
    temperature=temperature,
    ph=ph
)

print(f"Hours to bottle: {result.value:.1f}")
print(f"Confidence: {result.confidence:.2f}")
print(f"Model tier: {result.model_tier.value}")
```

## Metadata

The `metadata.json` file contains information about all models:

```json
{
  "version": "1.0.0",
  "created": "2025-01-01T12:00:00",
  "models": {
    "basic": {
      "type": "ridge_regression",
      "sensors_required": ["bubble_counter", "gravity"],
      "trained": true,
      "file": "basic_model.pkl"
    },
    ...
  }
}
```

## Retraining Models

Models should be retrained periodically as more fermentation data is collected:

1. Collect labeled fermentation data (with actual bottling times)
2. Create TrainingDataset with all fermentations
3. Run training pipeline
4. Evaluate model performance on held-out test set
5. Replace old models if new models perform better

## Performance Expectations

**Baseline Models (Synthetic Data)**:
- Basic: MAE ~10-15 hours
- Advanced: MAE ~8-12 hours

**Production Models (Real Data, 50+ fermentations)**:
- Basic: MAE ~5-8 hours
- Advanced: MAE ~3-6 hours

**Note**: Actual performance depends on:
- Data quality
- Sensor accuracy
- Wine type consistency
- Environmental variability
- Number of training samples
