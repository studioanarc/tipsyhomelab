#!/usr/bin/env python3
"""
Verify ML Engine Installation

Tests that all components can be imported and basic functionality works.
Run this script to verify the ML engine is properly installed.
"""

import sys
import os

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        import feature_engineering
        print("  ✓ feature_engineering")
    except ImportError as e:
        print(f"  ✗ feature_engineering: {e}")
        return False

    try:
        import models
        print("  ✓ models")
    except ImportError as e:
        print(f"  ✗ models: {e}")
        return False

    try:
        import petnat_predictor
        print("  ✓ petnat_predictor")
    except ImportError as e:
        print(f"  ✗ petnat_predictor: {e}")
        return False

    try:
        import anomaly_detector
        print("  ✓ anomaly_detector")
    except ImportError as e:
        print(f"  ✗ anomaly_detector: {e}")
        return False

    try:
        import model_manager
        print("  ✓ model_manager")
    except ImportError as e:
        print(f"  ✗ model_manager: {e}")
        return False

    try:
        import training_pipeline
        print("  ✓ training_pipeline")
    except ImportError as e:
        print(f"  ✗ training_pipeline: {e}")
        return False

    return True


def test_basic_functionality():
    """Test basic functionality without dependencies."""
    print("\nTesting basic functionality (without numpy/scikit-learn)...")

    try:
        from models import ModelTier, ModelSelector, PredictionResult, AnomalySeverity
        print("  ✓ Model enums and classes")

        # Test ModelSelector
        selector = ModelSelector()
        print("  ✓ ModelSelector instantiation")

        # Test PredictionResult
        result = PredictionResult(
            value=48.0,
            confidence=0.75,
            uncertainty_lower=38.0,
            uncertainty_upper=58.0,
            model_tier=ModelTier.BASIC,
            features_used=['bubble_current'],
            warnings=[]
        )
        result_dict = result.to_dict()
        print("  ✓ PredictionResult creation and serialization")

        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pretrained_models():
    """Test that pre-trained model files exist."""
    print("\nChecking pre-trained models...")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    pretrained_dir = os.path.join(script_dir, 'pretrained')

    required_files = [
        'minimal_model.pkl',
        'basic_model.pkl',
        'advanced_model.pkl',
        'anomaly_detector.pkl',
        'metadata.json'
    ]

    all_exist = True
    for filename in required_files:
        filepath = os.path.join(pretrained_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"  ✓ {filename} ({size} bytes)")
        else:
            print(f"  ✗ {filename} (missing)")
            all_exist = False

    return all_exist


def test_file_structure():
    """Test that all expected files exist."""
    print("\nChecking file structure...")

    script_dir = os.path.dirname(os.path.abspath(__file__))

    required_files = [
        '__init__.py',
        'feature_engineering.py',
        'models.py',
        'petnat_predictor.py',
        'anomaly_detector.py',
        'model_manager.py',
        'training_pipeline.py',
        'requirements.txt',
        'README.md'
    ]

    all_exist = True
    for filename in required_files:
        filepath = os.path.join(script_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"  ✓ {filename} ({size:,} bytes)")
        else:
            print(f"  ✗ {filename} (missing)")
            all_exist = False

    return all_exist


def test_with_dependencies():
    """Test functionality that requires numpy/scikit-learn."""
    print("\nTesting with dependencies (requires numpy, scipy, scikit-learn)...")

    try:
        import numpy as np
        import scipy
        import sklearn
        print("  ✓ Dependencies installed")

        # Test feature engineering
        from feature_engineering import FeatureEngineer
        engineer = FeatureEngineer()
        print("  ✓ FeatureEngineer instantiation")

        # Test with sample data
        timestamps = np.array([0, 1, 2, 3, 4])
        bubble_counts = np.array([10.0, 9.0, 8.0, 7.0, 6.0])

        features = engineer.extract_all_features(
            timestamps=timestamps,
            bubble_counts=bubble_counts
        )
        print(f"  ✓ Feature extraction ({len(features)} features)")

        # Test predictor
        from petnat_predictor import PetNatPredictor
        predictor = PetNatPredictor()
        print("  ✓ PetNatPredictor instantiation")

        result = predictor.predict(
            timestamps=timestamps,
            bubble_counts=bubble_counts
        )
        print(f"  ✓ Prediction made: {result.value:.1f}h (confidence: {result.confidence:.2%})")

        # Test anomaly detector
        from anomaly_detector import AnomalyDetector
        detector = AnomalyDetector()
        print("  ✓ AnomalyDetector instantiation")

        anomalies = detector.detect_anomalies(
            timestamps=timestamps,
            bubble_counts=bubble_counts
        )
        print(f"  ✓ Anomaly detection ({len(anomalies)} anomalies found)")

        # Test model manager
        from model_manager import ModelManager
        manager = ModelManager()
        print("  ✓ ModelManager instantiation")

        info = manager.get_model_info()
        print(f"  ✓ Model info retrieved")

        return True

    except ImportError:
        print("  ⚠ Dependencies not installed (this is OK)")
        print("    Install with: pip install numpy scipy scikit-learn joblib")
        return None  # None means "skipped"

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests."""
    print("=" * 80)
    print("ML Engine Installation Verification")
    print("=" * 80)
    print()

    results = []

    # Test 1: File structure
    results.append(("File Structure", test_file_structure()))

    # Test 2: Pre-trained models
    results.append(("Pre-trained Models", test_pretrained_models()))

    # Test 3: Imports
    results.append(("Module Imports", test_imports()))

    # Test 4: Basic functionality
    results.append(("Basic Functionality", test_basic_functionality()))

    # Test 5: With dependencies
    dep_result = test_with_dependencies()
    if dep_result is not None:
        results.append(("With Dependencies", dep_result))

    # Summary
    print("\n" + "=" * 80)
    print("Verification Summary")
    print("=" * 80)

    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} {test_name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if failed > 0:
        print("\n⚠ Some tests failed. Check errors above.")
        return 1
    else:
        print("\n✓ All tests passed! ML Engine is properly installed.")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Create baseline models: cd pretrained && python create_baseline_models.py")
        print("  3. Run examples: python example_usage.py")
        return 0


if __name__ == '__main__':
    sys.exit(main())
