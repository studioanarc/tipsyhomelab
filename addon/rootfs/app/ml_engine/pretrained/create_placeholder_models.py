"""
Create Placeholder Models (No Dependencies Required)

This creates minimal placeholder pickle files that have the correct structure
but don't contain actual trained models. These allow the ML engine to load
without errors, but will fall back to rule-based predictions.

For actual models, run create_baseline_models.py with scikit-learn installed.
"""

import pickle
import json
from datetime import datetime


def create_placeholder_minimal():
    """Create minimal model placeholder."""
    return {
        'model_type': 'rule_based',
        'description': 'Exponential decay model using bubble count only',
        'created_at': datetime.now().isoformat(),
        'version': '1.0.0',
        'note': 'Placeholder - uses rule-based prediction in petnat_predictor.py'
    }


def create_placeholder_basic():
    """Create basic model placeholder."""
    return {
        'model': None,  # Will trigger fallback to rule-based
        'scaler': None,
        'feature_names': [
            'bubble_current', 'bubble_mean', 'bubble_decay_rate',
            'co2_cumulative', 'bubble_recent_trend',
            'gravity_current', 'gravity_delta', 'gravity_rate',
            'bubble_gravity_correlation', 'fermentation_age_hours'
        ],
        'model_type': 'placeholder',
        'model_tier': 'basic',
        'n_samples': 0,
        'trained_at': datetime.now().isoformat(),
        'description': 'Placeholder - run create_baseline_models.py to generate real model',
        'note': 'Uses rule-based fallback until trained'
    }


def create_placeholder_advanced():
    """Create advanced model placeholder."""
    return {
        'model': None,  # Will trigger fallback to rule-based
        'scaler': None,
        'feature_names': [
            'bubble_current', 'bubble_mean', 'bubble_std', 'bubble_decay_rate',
            'bubble_rate_change', 'co2_cumulative', 'bubble_recent_trend',
            'gravity_current', 'gravity_delta', 'apparent_attenuation',
            'gravity_rate', 'temp_current', 'temp_mean', 'temp_std',
            'ph_current', 'ph_delta',
            'bubble_gravity_correlation', 'bubble_temp_correlation',
            'fermentation_age_hours', 'measurement_count'
        ],
        'model_type': 'placeholder',
        'model_tier': 'advanced',
        'n_samples': 0,
        'trained_at': datetime.now().isoformat(),
        'description': 'Placeholder - run create_baseline_models.py to generate real model',
        'note': 'Uses rule-based fallback until trained'
    }


def create_placeholder_anomaly():
    """Create anomaly detector placeholder."""
    return {
        'outlier_detector': None,  # Will use rule-based detection only
        'feature_names': [
            'bubble_current', 'gravity_current', 'temp_current', 'ph_current',
            'bubble_std', 'gravity_rate', 'temp_std', 'ph_delta',
            'co2_cumulative', 'apparent_attenuation', 'bubble_decay_r2',
            'gravity_poly_r2', 'fermentation_age_hours', 'measurement_count',
            'bubble_cv'
        ],
        'model_type': 'placeholder',
        'n_samples': 0,
        'trained_at': datetime.now().isoformat(),
        'description': 'Placeholder - uses rule-based anomaly detection only',
        'note': 'Run create_baseline_models.py to generate statistical model'
    }


def create_metadata():
    """Create metadata file."""
    return {
        'version': '1.0.0',
        'created': datetime.now().isoformat(),
        'description': 'Placeholder models for wine fermentation monitoring',
        'note': 'These are placeholders. Run create_baseline_models.py with scikit-learn to generate real models.',
        'models': {
            'minimal': {
                'type': 'rule_based',
                'sensors_required': ['bubble_counter'],
                'description': 'Exponential decay model using bubble count only',
                'accuracy': 'Moderate',
                'file': 'minimal_model.pkl',
                'trained': False
            },
            'basic': {
                'type': 'placeholder',
                'sensors_required': ['bubble_counter', 'gravity'],
                'description': 'Ridge regression with bubble and gravity (placeholder)',
                'accuracy': 'Good (when trained)',
                'file': 'basic_model.pkl',
                'trained': False
            },
            'advanced': {
                'type': 'placeholder',
                'sensors_required': ['bubble_counter', 'gravity', 'temperature', 'ph'],
                'description': 'Gradient Boosting with all sensors (placeholder)',
                'accuracy': 'Best (when trained)',
                'file': 'advanced_model.pkl',
                'trained': False
            },
            'anomaly_detector': {
                'type': 'placeholder',
                'description': 'Multi-strategy anomaly detection (rule-based only)',
                'file': 'anomaly_detector.pkl',
                'trained': False
            }
        },
        'installation_instructions': {
            'baseline_models': 'pip install numpy scikit-learn joblib scipy && python create_baseline_models.py',
            'production_models': 'Use training_pipeline.py with real fermentation data'
        }
    }


def main():
    """Create and save all placeholder models."""
    import os

    print("Creating placeholder models...")
    print("Note: These are placeholders that use rule-based fallbacks.")
    print("For ML models, install scikit-learn and run create_baseline_models.py\n")

    # Create models
    minimal = create_placeholder_minimal()
    basic = create_placeholder_basic()
    advanced = create_placeholder_advanced()
    anomaly = create_placeholder_anomaly()
    metadata = create_metadata()

    # Get current directory (should be pretrained/)
    output_dir = os.path.dirname(os.path.abspath(__file__))

    # Save models using pickle
    print("Saving placeholder models...")

    with open(os.path.join(output_dir, 'minimal_model.pkl'), 'wb') as f:
        pickle.dump(minimal, f)
    print("  ✓ minimal_model.pkl")

    with open(os.path.join(output_dir, 'basic_model.pkl'), 'wb') as f:
        pickle.dump(basic, f)
    print("  ✓ basic_model.pkl")

    with open(os.path.join(output_dir, 'advanced_model.pkl'), 'wb') as f:
        pickle.dump(advanced, f)
    print("  ✓ advanced_model.pkl")

    with open(os.path.join(output_dir, 'anomaly_detector.pkl'), 'wb') as f:
        pickle.dump(anomaly, f)
    print("  ✓ anomaly_detector.pkl")

    # Save metadata
    with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    print("  ✓ metadata.json")

    print("\nPlaceholder models created successfully!")
    print(f"Location: {output_dir}")
    print("\nThese placeholders allow the ML engine to load without errors.")
    print("The system will use rule-based predictions until you train real models.")
    print("\nTo create baseline models:")
    print("  pip install numpy scikit-learn joblib scipy")
    print("  python create_baseline_models.py")


if __name__ == '__main__':
    main()
