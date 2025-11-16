# Machine Learning Models & Predictions

Detailed explanation of how TipsyHomeLab uses machine learning to predict fermentation completion, final gravity, and bottling windows.

---

## Table of Contents

1. [Overview](#overview)
2. [How Predictions Work](#how-predictions-work)
3. [Available Models](#available-models)
4. [Model Selection](#model-selection)
5. [Training Process](#training-process)
6. [Prediction Accuracy](#prediction-accuracy)
7. [Feature Engineering](#feature-engineering)
8. [Advanced Topics](#advanced-topics)

---

## Overview

TipsyHomeLab uses machine learning to transform real-time fermentation data into actionable predictions. The system learns from your fermentation patterns to provide increasingly accurate predictions over time.

### What Can Be Predicted?

**Primary Predictions:**
- **Completion Date**: When fermentation will finish
- **Final Gravity**: Expected final specific gravity
- **Bottling Window**: Optimal time to bottle (Pet Nat)
- **Bottle Pressure**: Expected CO2 pressure in bottles

**Secondary Predictions:**
- **Residual Sugar**: Remaining fermentable sugars
- **ABV**: Final alcohol by volume
- **Attenuation**: Percentage of sugar consumed
- **Carbonation Level**: CO2 volumes in solution

### Data Requirements

**Minimum Requirements:**
- 48 hours of continuous data
- At least one of: bubble rate OR gravity measurements
- Temperature data (recommended)

**Optimal Requirements:**
- 7+ days of historical fermentation data
- Multiple sensor types (bubble + gravity + temp)
- Previous batch data for transfer learning

---

## How Predictions Work

### Conceptual Overview

```
┌─────────────────┐
│  Sensor Data    │
│  - Bubbles/min  │
│  - Gravity      │──┐
│  - Temperature  │  │
│  - Time         │  │
└─────────────────┘  │
                     │
                     ▼
┌──────────────────────────────────┐
│   Feature Engineering            │
│   - Rate of change               │
│   - Moving averages              │
│   - Derivative calculations      │
│   - Temperature compensation     │
└──────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────┐
│   Model Selection                │
│   Auto-select best model based   │
│   on data quality & quantity     │
└──────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────┐
│   Prediction Algorithms          │
│   - Linear Regression            │
│   - Polynomial Regression        │
│   - Gradient Boosting            │
│   - LSTM Neural Network          │
└──────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────┐
│   Confidence Intervals           │
│   Calculate prediction certainty │
└──────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────┐
│   Predictions                    │
│   - Completion: 2024-11-20 ±1d   │
│   - Final Gravity: 1.002 ±0.001  │
│   - Bottle Pressure: 3.2 ±0.3bar │
└──────────────────────────────────┘
```

### Mathematical Foundation

Fermentation follows predictable patterns that can be modeled:

**Logistic Growth Model:**
```
SG(t) = SG_initial - (SG_initial - SG_final) / (1 + e^(-k(t-t0)))

Where:
- SG(t) = Specific gravity at time t
- SG_initial = Starting gravity (e.g., 1.050)
- SG_final = Final gravity (predicted)
- k = Fermentation rate constant
- t0 = Lag time before active fermentation
- t = Time in hours
```

**Bubble Rate Decay:**
```
BubbleRate(t) = BubbleRate_peak * e^(-λt)

Where:
- BubbleRate_peak = Maximum bubble rate
- λ = Decay constant
- t = Time since peak
```

---

## Available Models

### 1. Linear Regression

**Best For:**
- Simple fermentations
- Limited data (48-72 hours)
- Quick estimates

**How It Works:**
Fits a straight line to the data trend.

```python
# Simplified implementation
from sklearn.linear_model import LinearRegression

model = LinearRegression()
model.fit(time_data, gravity_data)
final_gravity = model.predict(future_time)
```

**Pros:**
- Fast computation
- Works with minimal data
- Easy to interpret

**Cons:**
- Assumes constant rate (unrealistic)
- Poor for non-linear fermentation curves
- Less accurate

**Accuracy:** ±0.003 SG, ±2 days

### 2. Polynomial Regression

**Best For:**
- Most fermentations
- 72+ hours of data
- Balanced accuracy/performance

**How It Works:**
Fits a polynomial curve (degree 2-4) to capture fermentation curve shape.

```python
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import Ridge

# Degree 3 polynomial
poly = PolynomialFeatures(degree=3)
X_poly = poly.fit_transform(time_data)

model = Ridge(alpha=1.0)  # Regularization prevents overfitting
model.fit(X_poly, gravity_data)
```

**Equation (degree 3):**
```
SG(t) = a*t³ + b*t² + c*t + d

Where coefficients a,b,c,d are learned from data
```

**Pros:**
- Captures fermentation curve well
- Good balance of accuracy and speed
- Handles inflection points

**Cons:**
- Can overfit with too high degree
- Requires regularization
- May extrapolate poorly

**Accuracy:** ±0.002 SG, ±1.5 days

### 3. Gradient Boosting (Default)

**Best For:**
- 7+ days of data
- Multiple sensors
- High accuracy needs

**How It Works:**
Ensemble of decision trees that iteratively improve predictions.

```python
from sklearn.ensemble import GradientBoostingRegressor

model = GradientBoostingRegressor(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=5,
    min_samples_split=4,
    random_state=42
)

model.fit(features, target)
```

**Features Used:**
- Time elapsed
- Current gravity
- Bubble rate
- Temperature
- Rate of change (1st derivative)
- Acceleration (2nd derivative)
- Moving averages
- Historical patterns

**Pros:**
- Very accurate
- Handles complex patterns
- Robust to outliers
- Captures interactions between variables

**Cons:**
- Requires more data
- Slower computation
- Black box (harder to interpret)

**Accuracy:** ±0.001 SG, ±0.5 days

### 4. LSTM Neural Network (Experimental)

**Best For:**
- Multiple batch history
- Research applications
- Maximum accuracy

**How It Works:**
Long Short-Term Memory network captures time series patterns.

```python
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

model = Sequential([
    LSTM(64, activation='relu', input_shape=(sequence_length, n_features)),
    Dropout(0.2),
    LSTM(32, activation='relu'),
    Dropout(0.2),
    Dense(16, activation='relu'),
    Dense(1)  # Output: prediction
])

model.compile(optimizer='adam', loss='mse')
```

**Pros:**
- State-of-the-art accuracy
- Learns complex temporal patterns
- Improves with more batches
- Can detect anomalies

**Cons:**
- Requires significant training data (10+ batches)
- Computationally expensive
- Risk of overfitting
- Requires GPU for reasonable speed

**Accuracy:** ±0.0005 SG, ±4 hours (with sufficient data)

---

## Model Selection

TipsyHomeLab automatically selects the best model based on available data.

### Auto-Selection Logic

```python
def select_model(data_hours, num_sensors, historical_batches):
    """
    Automatically select best model for current conditions
    """
    if data_hours < 48:
        return "insufficient_data"

    if data_hours < 72:
        return "linear"  # Not enough data for complex models

    if num_sensors == 1 and data_hours < 120:
        return "polynomial"  # Simple setup, moderate data

    if historical_batches < 5:
        return "gradient_boosting"  # Best for single batch

    if historical_batches >= 10:
        return "lstm"  # Enough data for neural network

    return "gradient_boosting"  # Default for most cases
```

### Manual Override

Force specific model in configuration:

```yaml
predictions:
  enabled: true
  model: gradient_boosting  # Options: linear, polynomial, gradient_boosting, lstm
```

---

## Training Process

### Data Collection

```python
class FermentationDataCollector:
    def __init__(self):
        self.data = {
            'timestamp': [],
            'gravity': [],
            'bubble_rate': [],
            'temperature': []
        }

    def add_reading(self, timestamp, gravity, bubble_rate, temp):
        """Add new sensor reading"""
        self.data['timestamp'].append(timestamp)
        self.data['gravity'].append(gravity)
        self.data['bubble_rate'].append(bubble_rate)
        self.data['temperature'].append(temp)

    def prepare_features(self):
        """Engineer features from raw data"""
        df = pd.DataFrame(self.data)

        # Time-based features
        df['hours_elapsed'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds() / 3600

        # Rate of change
        df['gravity_change'] = df['gravity'].diff()
        df['bubble_rate_change'] = df['bubble_rate'].diff()

        # Moving averages
        df['gravity_ma_6h'] = df['gravity'].rolling(6).mean()
        df['bubble_rate_ma_6h'] = df['bubble_rate'].rolling(6).mean()

        # Acceleration (2nd derivative)
        df['gravity_accel'] = df['gravity_change'].diff()

        return df
```

### Model Training

```python
class FermentationPredictor:
    def __init__(self, model_type='gradient_boosting'):
        self.model_type = model_type
        self.model = None

    def train(self, features, target):
        """Train model on fermentation data"""

        if self.model_type == 'gradient_boosting':
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                min_samples_split=4,
                subsample=0.8,
                random_state=42
            )

        # Train with cross-validation
        from sklearn.model_selection import cross_val_score
        scores = cross_val_score(self.model, features, target, cv=5)

        print(f"Model accuracy: {scores.mean():.4f} (+/- {scores.std():.4f})")

        # Final training on all data
        self.model.fit(features, target)

    def predict(self, features):
        """Make prediction with confidence interval"""
        prediction = self.model.predict(features)

        # Calculate confidence interval
        # Using prediction variance from ensemble
        confidence = self._calculate_confidence(features)

        return {
            'prediction': prediction,
            'confidence_lower': prediction - confidence,
            'confidence_upper': prediction + confidence
        }
```

### Retraining Schedule

Models are retrained automatically:

- **Real-time updates**: Every new sensor reading updates predictions
- **Model retraining**: Every 24 hours or when new significant data
- **Historical learning**: Completed batches added to training set

---

## Prediction Accuracy

### Factors Affecting Accuracy

**Positive Factors:**
- More sensor types (bubble + gravity + temp)
- Longer data collection period
- Stable temperature
- Consistent yeast performance
- Similar previous batches

**Negative Factors:**
- Sensor errors or dropout
- Temperature fluctuations
- Stuck fermentation
- Unusual yeast behavior
- Very early predictions (<48 hours)

### Accuracy Over Time

```
Prediction Accuracy vs. Time Elapsed

Error (days)
    ^
  4 |●
  3 | ●
  2 |  ●●
  1 |    ●●●
  0 |       ●●●●●●
    +─────────────────────> Time Elapsed (hours)
     24  48  72  96  120  144
```

**General Guidelines:**
- **24-48 hours**: ±3 days (very rough estimate)
- **48-72 hours**: ±2 days (improving)
- **72-96 hours**: ±1 day (good estimate)
- **96+ hours**: ±0.5 days (accurate)

### Confidence Intervals

All predictions include confidence intervals:

```
Final Gravity Prediction: 1.002 SG
Confidence Interval (95%): 1.001 - 1.003 SG

Interpretation: 95% certain final gravity will be between 1.001 and 1.003
```

Narrower intervals = more confident prediction

---

## Feature Engineering

### Raw Features

Direct sensor measurements:
- Current gravity
- Bubble rate
- Temperature
- Time elapsed

### Derived Features

**1. Rate of Change (1st Derivative):**
```python
gravity_change_per_hour = (gravity_current - gravity_1h_ago) / 1
```

**2. Acceleration (2nd Derivative):**
```python
gravity_accel = (gravity_change_now - gravity_change_1h_ago) / 1
```

**3. Moving Averages:**
```python
gravity_ma_6h = mean(gravity[-6:])  # Last 6 hours
gravity_ma_24h = mean(gravity[-24:])  # Last 24 hours
```

**4. Exponential Moving Average:**
```python
alpha = 0.3
ema = alpha * new_value + (1 - alpha) * previous_ema
```

**5. Time-Based Features:**
```python
hour_of_day = timestamp.hour
day_of_fermentation = (timestamp - start_time).days
```

**6. Temperature Compensation:**
```python
# Adjust gravity for temperature
gravity_corrected = gravity + 0.00130 * (temp - 20)
```

**7. Fermentation Phase:**
```python
if bubble_rate > 50:
    phase = "peak"
elif bubble_rate > 20:
    phase = "active"
elif bubble_rate > 5:
    phase = "slowing"
else:
    phase = "finishing"
```

### Feature Importance

Gradient boosting models reveal which features matter most:

```
Feature Importance (typical Pet Nat fermentation):

1. Hours elapsed           ████████████████████ 35%
2. Current gravity         ████████████████     28%
3. Gravity rate of change  ████████████         20%
4. Bubble rate             ███████              12%
5. Temperature             ██                    5%
```

---

## Advanced Topics

### Transfer Learning

Use knowledge from previous batches to improve predictions:

```python
class TransferLearningPredictor:
    def __init__(self):
        self.base_model = None  # Trained on many batches
        self.batch_model = None  # Fine-tuned for current batch

    def train_base_model(self, historical_batches):
        """Train on all historical fermentation data"""
        all_features = []
        all_targets = []

        for batch in historical_batches:
            features = batch.get_features()
            targets = batch.get_targets()
            all_features.append(features)
            all_targets.append(targets)

        self.base_model = GradientBoostingRegressor()
        self.base_model.fit(all_features, all_targets)

    def fine_tune(self, current_batch_data):
        """Fine-tune on current batch (transfer learning)"""
        # Start with base model weights
        self.batch_model = clone(self.base_model)

        # Continue training on current batch
        self.batch_model.fit(
            current_batch_data.features,
            current_batch_data.targets,
            # Lower learning rate for fine-tuning
            learning_rate=0.01
        )
```

**Benefits:**
- More accurate early predictions
- Faster convergence
- Learns yeast-specific patterns
- Adapts to brewing style

### Anomaly Detection

Detect when fermentation deviates from expected patterns:

```python
from sklearn.ensemble import IsolationForest

def detect_anomalies(data):
    """Detect unusual fermentation behavior"""
    model = IsolationForest(contamination=0.1)
    model.fit(data.features)

    predictions = model.predict(data.features)

    # -1 = anomaly, 1 = normal
    anomalies = predictions == -1

    if any(anomalies):
        print("WARNING: Unusual fermentation pattern detected!")
        print("Possible causes:")
        print("- Stuck fermentation")
        print("- Temperature shock")
        print("- Contamination")
        print("- Sensor malfunction")

    return anomalies
```

### Ensemble Methods

Combine multiple models for better predictions:

```python
class EnsemblePredictor:
    def __init__(self):
        self.models = [
            ('linear', LinearRegression()),
            ('poly', make_pipeline(PolynomialFeatures(3), Ridge())),
            ('gb', GradientBoostingRegressor())
        ]

    def predict(self, features):
        """Average predictions from all models"""
        predictions = []

        for name, model in self.models:
            pred = model.predict(features)
            predictions.append(pred)

        # Weighted average (GB gets more weight)
        weights = [0.2, 0.3, 0.5]
        final_prediction = np.average(predictions, weights=weights)

        # Calculate uncertainty from prediction variance
        uncertainty = np.std(predictions)

        return final_prediction, uncertainty
```

### Bayesian Optimization

Optimize model hyperparameters automatically:

```python
from skopt import BayesSearchCV

def optimize_hyperparameters(X, y):
    """Find best model hyperparameters"""

    # Define search space
    search_spaces = {
        'n_estimators': (50, 200),
        'learning_rate': (0.01, 0.3, 'log-uniform'),
        'max_depth': (3, 10),
        'min_samples_split': (2, 20)
    }

    # Bayesian optimization
    opt = BayesSearchCV(
        GradientBoostingRegressor(),
        search_spaces,
        n_iter=50,
        cv=5,
        random_state=42
    )

    opt.fit(X, y)

    print(f"Best score: {opt.best_score_}")
    print(f"Best params: {opt.best_params_}")

    return opt.best_estimator_
```

### Model Interpretability

Understand why model makes certain predictions:

```python
import shap

def explain_prediction(model, features):
    """Explain model predictions using SHAP values"""

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(features)

    # Show feature contributions
    shap.summary_plot(shap_values, features)

    # Force plot for single prediction
    shap.force_plot(
        explainer.expected_value,
        shap_values[0],
        features.iloc[0]
    )
```

Example output:
```
Prediction: Final Gravity = 1.002

Feature Contributions:
  Hours elapsed (120h)    → -0.015 SG (decreases gravity)
  Current gravity (1.010) → +0.008 SG (base level)
  Bubble rate (15/min)    → -0.003 SG (active fermentation)
  Temperature (20°C)      → +0.002 SG (optimal temp)
```

---

## Troubleshooting Predictions

### Prediction Not Available

**Symptom:** "Insufficient data for predictions"

**Causes:**
- Less than 48 hours of data
- Missing sensor data
- Gaps in data collection

**Solution:**
- Wait for more data
- Check sensor connections
- Ensure continuous monitoring

### Prediction Changes Dramatically

**Symptom:** Predicted completion date jumps by days

**Causes:**
- Temperature change affecting fermentation
- Stuck fermentation starting again
- Sensor calibration drift
- Phase transition (lag → active → slowing)

**Solution:**
- Normal during phase transitions
- Check temperature stability
- Verify sensor accuracy
- Wait for prediction to stabilize (24h)

### Prediction Seems Wrong

**Symptom:** Predicted final gravity very different from target

**Causes:**
- Unusual yeast behavior
- Different fermentation conditions
- Contamination
- Model hasn't seen similar fermentation

**Solution:**
- Manual override prediction if needed
- Let model learn from completed batch
- Check for stuck fermentation
- Verify initial gravity was correct

---

## Best Practices

1. **Start Simple**: Use auto mode initially
2. **Collect Quality Data**: Consistent sensor readings are crucial
3. **Stable Temperature**: Temperature swings confuse predictions
4. **Wait for Data**: Early predictions (<72h) are rough estimates
5. **Learn from History**: More batches = better predictions
6. **Monitor Confidence**: Wide intervals = uncertain predictions
7. **Manual Validation**: Always verify predictions make sense
8. **Update Models**: Let system learn from completed batches

---

## Future Improvements

**Planned Features:**
- Multi-modal learning (combine bubble + gravity models)
- Attention mechanisms for temporal patterns
- Reinforcement learning for optimal bottling timing
- Integration with weather data
- Strain-specific model training
- Computer vision for foam analysis
- Collaborative filtering (learn from community data)

---

## References

**Academic Papers:**
- "Modeling of Wine Fermentation Kinetics" - Garcia et al.
- "Predictive Models for Brewery Fermentation" - Boulton & Quain
- "Machine Learning for Bioprocess Optimization" - Chen et al.

**Books:**
- "Pattern Recognition and Machine Learning" - Bishop
- "Hands-On Machine Learning" - Géron
- "Time Series Forecasting" - Hyndman & Athanasopoulos

**Online Resources:**
- Scikit-learn documentation
- TensorFlow tutorials
- Kaggle fermentation datasets
