"""
Create Baseline Pre-trained Models

This script creates baseline/dummy models for demonstration purposes.
In production, these should be trained on real fermentation data.

Run this script to generate the .pkl files:
    python create_baseline_models.py
"""

import numpy as np
import joblib
import json
from datetime import datetime
from sklearn.ensemble import GradientBoostingRegressor, IsolationForest
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler


def create_minimal_model():
    """
    Create minimal model (rule-based, no actual ML needed).

    This is just a placeholder - the actual minimal model uses
    rule-based exponential decay fitting in petnat_predictor.py
    """
    return {
        'model_type': 'rule_based',
        'description': 'Exponential decay model using bubble count only',
        'created_at': datetime.now().isoformat(),
        'version': '1.0.0'
    }


def create_basic_model():
    """
    Create basic model (Ridge regression).

    Uses synthetic data to create a baseline model structure.
    Should be replaced with real training data.
    """
    # Synthetic training data (20 samples)
    np.random.seed(42)
    n_samples = 20

    # Features: bubble_current, bubble_decay_rate, gravity_current, gravity_rate, etc.
    # Simplified to 10 features for baseline
    n_features = 10
    X = np.random.randn(n_samples, n_features)

    # Synthetic labels (hours to bottle)
    # Roughly: inversely related to bubble decay rate and gravity rate
    y = 50 + 30 * X[:, 0] - 20 * X[:, 1] + 10 * np.random.randn(n_samples)
    y = np.clip(y, 0, 200)  # Keep reasonable range

    # Train model
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = Ridge(alpha=1.0, random_state=42)
    model.fit(X_scaled, y)

    # Feature names (typical BASIC model features)
    feature_names = [
        'bubble_current', 'bubble_mean', 'bubble_decay_rate',
        'co2_cumulative', 'bubble_recent_trend',
        'gravity_current', 'gravity_delta', 'gravity_rate',
        'bubble_gravity_correlation', 'fermentation_age_hours'
    ]

    return {
        'model': model,
        'scaler': scaler,
        'feature_names': feature_names,
        'model_type': 'ridge_regression',
        'model_tier': 'basic',
        'n_samples': n_samples,
        'trained_at': datetime.now().isoformat(),
        'description': 'Baseline Ridge regression model (trained on synthetic data)',
        'note': 'Replace with real training data for production use'
    }


def create_advanced_model():
    """
    Create advanced model (Gradient Boosting).

    Uses synthetic data to create a baseline model structure.
    Should be replaced with real training data.
    """
    # Synthetic training data (50 samples)
    np.random.seed(42)
    n_samples = 50

    # More features for advanced model (20 features)
    n_features = 20
    X = np.random.randn(n_samples, n_features)

    # Synthetic labels with more complex relationship
    y = (40 +
         25 * X[:, 0] +           # bubble_current
         -15 * X[:, 1] +          # bubble_decay_rate
         30 * X[:, 5] +           # gravity_current
         -10 * X[:, 6] +          # gravity_rate
         5 * X[:, 10] +           # temp_current
         8 * np.random.randn(n_samples))
    y = np.clip(y, 0, 300)

    # Train model
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=4,
        min_samples_split=5,
        min_samples_leaf=3,
        subsample=0.8,
        random_state=42,
        loss='huber'
    )
    model.fit(X_scaled, y)

    # Feature names (typical ADVANCED model features)
    feature_names = [
        'bubble_current', 'bubble_mean', 'bubble_std', 'bubble_decay_rate',
        'bubble_rate_change', 'co2_cumulative', 'bubble_recent_trend',
        'gravity_current', 'gravity_delta', 'apparent_attenuation',
        'gravity_rate', 'temp_current', 'temp_mean', 'temp_std',
        'ph_current', 'ph_delta',
        'bubble_gravity_correlation', 'bubble_temp_correlation',
        'fermentation_age_hours', 'measurement_count'
    ]

    return {
        'model': model,
        'scaler': scaler,
        'feature_names': feature_names,
        'model_type': 'gradient_boosting',
        'model_tier': 'advanced',
        'n_samples': n_samples,
        'trained_at': datetime.now().isoformat(),
        'description': 'Baseline Gradient Boosting model (trained on synthetic data)',
        'note': 'Replace with real training data for production use'
    }


def create_anomaly_detector_model():
    """
    Create anomaly detector (Isolation Forest).

    Uses synthetic normal fermentation data.
    Should be replaced with real training data including anomalies.
    """
    # Synthetic normal fermentation data (100 samples)
    np.random.seed(42)
    n_samples = 100

    # Generate realistic-looking fermentation data
    # Normal ranges for features
    X = np.random.randn(n_samples, 15) * 0.5  # Reduced variance for "normal" data

    # Add some realistic scaling
    # bubble_current: 0-30
    X[:, 0] = np.clip(np.abs(X[:, 0]) * 10, 0, 30)
    # gravity_current: 1.000-1.080
    X[:, 1] = 1.040 + X[:, 1] * 0.02
    # temp_current: 15-25°C
    X[:, 2] = 20 + X[:, 2] * 3
    # pH: 3.0-4.0
    X[:, 3] = 3.5 + X[:, 3] * 0.3

    # Add a few outliers (10%)
    n_outliers = int(n_samples * 0.1)
    outlier_indices = np.random.choice(n_samples, n_outliers, replace=False)
    X[outlier_indices] *= 3  # Make them significantly different

    # Train Isolation Forest
    model = IsolationForest(
        contamination=0.1,
        random_state=42,
        n_estimators=100,
        max_samples='auto'
    )
    model.fit(X)

    feature_names = [
        'bubble_current', 'gravity_current', 'temp_current', 'ph_current',
        'bubble_std', 'gravity_rate', 'temp_std', 'ph_delta',
        'co2_cumulative', 'apparent_attenuation', 'bubble_decay_r2',
        'gravity_poly_r2', 'fermentation_age_hours', 'measurement_count',
        'bubble_cv'
    ]

    return {
        'outlier_detector': model,
        'feature_names': feature_names,
        'model_type': 'isolation_forest',
        'n_samples': n_samples,
        'trained_at': datetime.now().isoformat(),
        'description': 'Baseline anomaly detector (trained on synthetic data)',
        'note': 'Replace with real training data for production use'
    }


def create_metadata():
    """Create metadata file describing all models."""
    return {
        'version': '1.0.0',
        'created': datetime.now().isoformat(),
        'description': 'Baseline pre-trained models for wine fermentation monitoring',
        'note': 'These are baseline models trained on synthetic data. Replace with models trained on real fermentation data for production use.',
        'models': {
            'minimal': {
                'type': 'rule_based',
                'sensors_required': ['bubble_counter'],
                'description': 'Exponential decay model using bubble count only',
                'accuracy': 'Moderate (baseline)',
                'file': 'minimal_model.pkl'
            },
            'basic': {
                'type': 'ridge_regression',
                'sensors_required': ['bubble_counter', 'gravity'],
                'description': 'Ridge regression with bubble and gravity',
                'accuracy': 'Good (baseline)',
                'file': 'basic_model.pkl',
                'trained': True
            },
            'advanced': {
                'type': 'gradient_boosting',
                'sensors_required': ['bubble_counter', 'gravity', 'temperature', 'ph'],
                'description': 'Gradient Boosting with all sensors',
                'accuracy': 'Best (baseline)',
                'file': 'advanced_model.pkl',
                'trained': True
            },
            'anomaly_detector': {
                'type': 'isolation_forest',
                'description': 'Multi-strategy anomaly detection',
                'file': 'anomaly_detector.pkl',
                'trained': True
            }
        }
    }


def main():
    """Create and save all baseline models."""
    import os

    print("Creating baseline models...")

    # Create models
    minimal = create_minimal_model()
    basic = create_basic_model()
    advanced = create_advanced_model()
    anomaly = create_anomaly_detector_model()
    metadata = create_metadata()

    # Get current directory (should be pretrained/)
    output_dir = os.path.dirname(os.path.abspath(__file__))

    # Save models
    print("Saving models...")

    joblib.dump(minimal, os.path.join(output_dir, 'minimal_model.pkl'))
    print("  ✓ minimal_model.pkl")

    joblib.dump(basic, os.path.join(output_dir, 'basic_model.pkl'))
    print("  ✓ basic_model.pkl")

    joblib.dump(advanced, os.path.join(output_dir, 'advanced_model.pkl'))
    print("  ✓ advanced_model.pkl")

    joblib.dump(anomaly, os.path.join(output_dir, 'anomaly_detector.pkl'))
    print("  ✓ anomaly_detector.pkl")

    # Save metadata
    with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    print("  ✓ metadata.json")

    print("\nBaseline models created successfully!")
    print(f"Location: {output_dir}")
    print("\nNote: These are baseline models trained on synthetic data.")
    print("For production use, retrain with real fermentation data using training_pipeline.py")


if __name__ == '__main__':
    main()
