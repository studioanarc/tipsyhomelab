"""
Example Usage of the ML Engine

Demonstrates how to use the adaptive ML engine for wine production monitoring.
"""

import numpy as np
from datetime import datetime, timedelta

# Import ML engine components
from model_manager import ModelManager
from petnat_predictor import PetNatPredictor
from anomaly_detector import AnomalyDetector
from feature_engineering import FeatureEngineer


def generate_sample_data():
    """
    Generate sample fermentation data for demonstration.

    In production, this would come from actual sensors.
    """
    # Simulate 72 hours of fermentation with 15-minute intervals
    n_points = 4 * 72  # 4 measurements per hour * 72 hours
    hours = np.linspace(0, 72, n_points)

    # Convert to timestamps
    start_time = datetime.now() - timedelta(hours=72)
    timestamps = np.array([start_time + timedelta(hours=h) for h in hours])

    # Simulate bubble count with exponential decay
    # Starts high (~25 bubbles/min), decays to ~1.5 bubbles/min
    bubble_counts = 25 * np.exp(-0.04 * hours) + 1.5 + np.random.normal(0, 0.5, n_points)
    bubble_counts = np.maximum(bubble_counts, 0)  # No negative bubbles

    # Simulate gravity drop (1.048 → 1.002)
    # Logistic curve for realistic fermentation
    gravity_start = 1.048
    gravity_final = 1.002
    k = 0.08  # Fermentation rate
    t_mid = 40  # Midpoint of fermentation
    gravity = gravity_final + (gravity_start - gravity_final) / (1 + np.exp(k * (hours - t_mid)))
    gravity += np.random.normal(0, 0.0005, n_points)  # Small noise

    # Simulate temperature (18-22°C with some variation)
    temperature = 20 + 2 * np.sin(hours / 12) + np.random.normal(0, 0.3, n_points)

    # Simulate pH drop (3.8 → 3.2)
    ph = 3.8 - 0.6 * (hours / 72) ** 0.5 + np.random.normal(0, 0.02, n_points)

    return {
        'timestamps': timestamps,
        'bubble_counts': bubble_counts,
        'gravity': gravity,
        'temperature': temperature,
        'ph': ph,
        'hours': hours
    }


def example_1_basic_prediction():
    """Example 1: Basic prediction with minimal sensors."""
    print("=" * 80)
    print("EXAMPLE 1: Basic Prediction (Bubble Counter Only)")
    print("=" * 80)

    # Generate sample data
    data = generate_sample_data()

    # Initialize predictor
    predictor = PetNatPredictor()

    # Make prediction with bubble count only
    result = predictor.predict(
        timestamps=data['timestamps'],
        bubble_counts=data['bubble_counts']
    )

    # Display results
    print(f"\nCurrent Status:")
    print(f"  Fermentation age: {data['hours'][-1]:.1f} hours ({data['hours'][-1]/24:.1f} days)")
    print(f"  Current bubble rate: {data['bubble_counts'][-1]:.1f} bubbles/min")
    print(f"\nPrediction:")
    print(f"  Hours to bottle: {result.value:.1f}h ({result.value/24:.1f} days)")
    print(f"  Confidence: {result.confidence:.1%}")
    print(f"  Model tier: {result.model_tier.value}")
    print(f"  Prediction interval: {result.uncertainty_lower:.1f}h - {result.uncertainty_upper:.1f}h")
    print(f"\nWarnings:")
    for warning in result.warnings:
        print(f"  ⚠️  {warning}")

    print("\n")


def example_2_advanced_prediction():
    """Example 2: Advanced prediction with all sensors."""
    print("=" * 80)
    print("EXAMPLE 2: Advanced Prediction (All Sensors)")
    print("=" * 80)

    # Generate sample data
    data = generate_sample_data()

    # Initialize predictor
    predictor = PetNatPredictor()

    # Make prediction with all sensors
    result = predictor.predict(
        timestamps=data['timestamps'],
        bubble_counts=data['bubble_counts'],
        gravity=data['gravity'],
        temperature=data['temperature'],
        ph=data['ph']
    )

    # Display results
    print(f"\nCurrent Status:")
    print(f"  Fermentation age: {data['hours'][-1]:.1f} hours")
    print(f"  Bubble rate: {data['bubble_counts'][-1]:.1f} bubbles/min")
    print(f"  Specific gravity: {data['gravity'][-1]:.3f}")
    print(f"  Temperature: {data['temperature'][-1]:.1f}°C")
    print(f"  pH: {data['ph'][-1]:.2f}")
    print(f"\nPrediction:")
    print(f"  Hours to bottle: {result.value:.1f}h")
    print(f"  Confidence: {result.confidence:.1%}")
    print(f"  Model tier: {result.model_tier.value}")
    print(f"  Uncertainty: ±{(result.uncertainty_upper - result.value):.1f}h")

    if result.warnings:
        print(f"\nWarnings:")
        for warning in result.warnings:
            print(f"  ⚠️  {warning}")

    print("\n")


def example_3_anomaly_detection():
    """Example 3: Anomaly detection."""
    print("=" * 80)
    print("EXAMPLE 3: Anomaly Detection")
    print("=" * 80)

    # Generate sample data
    data = generate_sample_data()

    # Add some anomalies
    # Simulate temperature spike
    data['temperature'][-20:-10] += 8  # Temperature spike to ~28°C

    # Initialize detector
    detector = AnomalyDetector()

    # Detect anomalies
    anomalies = detector.detect_anomalies(
        timestamps=data['timestamps'],
        bubble_counts=data['bubble_counts'],
        gravity=data['gravity'],
        temperature=data['temperature'],
        ph=data['ph']
    )

    # Get summary
    summary = detector.get_summary(anomalies)

    print(f"\nFermentation Health:")
    print(f"  Health score: {summary['health_score']:.1f}/100")
    print(f"  Status: {summary['status'].upper()}")
    print(f"  Anomalies detected: {summary['total_count']}")
    print(f"    - Critical: {summary['critical_count']}")
    print(f"    - Warnings: {summary['warning_count']}")
    print(f"    - Info: {summary['info_count']}")

    if anomalies:
        print(f"\nDetected Anomalies:")
        for i, anomaly in enumerate(anomalies, 1):
            severity_symbols = {
                'critical': '🔴',
                'warning': '🟡',
                'info': 'ℹ️'
            }
            symbol = severity_symbols.get(anomaly.severity.value, '•')

            print(f"\n  {symbol} {i}. {anomaly.anomaly_type.value.upper().replace('_', ' ')}")
            print(f"     Severity: {anomaly.severity.value}")
            print(f"     Score: {anomaly.score:.2f}")
            print(f"     {anomaly.description}")
            print(f"     → Recommendation: {anomaly.recommendation}")

    print("\n")


def example_4_feature_extraction():
    """Example 4: Feature extraction."""
    print("=" * 80)
    print("EXAMPLE 4: Feature Extraction")
    print("=" * 80)

    # Generate sample data
    data = generate_sample_data()

    # Initialize feature engineer
    engineer = FeatureEngineer()

    # Extract features
    features = engineer.extract_all_features(
        timestamps=data['timestamps'],
        bubble_counts=data['bubble_counts'],
        gravity=data['gravity'],
        temperature=data['temperature'],
        ph=data['ph']
    )

    print(f"\nExtracted {len(features)} features from time-series data:\n")

    # Display key features
    key_features = [
        'bubble_current', 'bubble_decay_rate', 'co2_cumulative',
        'gravity_current', 'apparent_attenuation', 'gravity_rate',
        'temp_current', 'ph_current',
        'bubble_gravity_correlation', 'fermentation_age_hours'
    ]

    for feature_name in key_features:
        if feature_name in features:
            value = features[feature_name]
            print(f"  {feature_name:.<35} {value:.4f}")

    print(f"\n  (+ {len(features) - len(key_features)} additional features)")
    print("\n")


def example_5_complete_pipeline():
    """Example 5: Complete pipeline with ModelManager."""
    print("=" * 80)
    print("EXAMPLE 5: Complete Pipeline (ModelManager)")
    print("=" * 80)

    # Generate sample data
    data = generate_sample_data()

    # Initialize model manager
    manager = ModelManager()

    # Display model info
    info = manager.get_model_info()
    print(f"\nModel Manager Status:")
    print(f"  Model directory: {info['model_dir']}")
    print(f"  Available models:")
    for model_name, available in info['available_models'].items():
        status = "✓" if available else "✗"
        print(f"    {status} {model_name}")

    # Create prediction pipeline
    pipeline = manager.create_prediction_pipeline()

    # Run complete pipeline
    results = pipeline(
        timestamps=data['timestamps'],
        bubble_counts=data['bubble_counts'],
        gravity=data['gravity'],
        temperature=data['temperature'],
        ph=data['ph']
    )

    # Display results
    print(f"\nPipeline Results:")

    if results['prediction']:
        pred = results['prediction']
        print(f"\n  Prediction:")
        print(f"    Hours to bottle: {pred['value']:.1f}h")
        print(f"    Confidence: {pred['confidence']:.1%}")
        print(f"    Model: {pred['model_tier']}")

    print(f"\n  Health:")
    print(f"    Score: {results['health_score']:.1f}/100")
    print(f"    Status: {results['anomaly_summary']['status']}")

    if results['anomalies']:
        print(f"\n  Top Concerns:")
        for concern in results['anomaly_summary']['top_concerns']:
            print(f"    • {concern['description']}")

    print("\n")


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "ML ENGINE USAGE EXAMPLES" + " " * 34 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    try:
        example_1_basic_prediction()
        example_2_advanced_prediction()
        example_3_anomaly_detection()
        example_4_feature_extraction()
        example_5_complete_pipeline()

        print("=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)
        print("\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
