"""
Adaptive ML Engine for Wine Production Monitoring

This package provides machine learning capabilities for fermentation monitoring,
including Pet Nat bottling predictions and anomaly detection. The engine adapts
to variable sensor configurations, providing tiered predictions based on available data.
"""

__version__ = "1.0.0"

from .model_manager import ModelManager
from .petnat_predictor import PetNatPredictor
from .anomaly_detector import AnomalyDetector
from .feature_engineering import FeatureEngineer

__all__ = [
    'ModelManager',
    'PetNatPredictor',
    'AnomalyDetector',
    'FeatureEngineer',
]
