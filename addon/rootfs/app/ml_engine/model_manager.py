"""
Model Manager

Centralized management of all ML models:
- Load pre-trained models
- Model versioning
- Model selection based on sensor availability
- Caching and performance optimization
- Thread-safe model access
"""

import os
import joblib
import json
from typing import Dict, Optional, Any
from pathlib import Path
import threading
from datetime import datetime

from .petnat_predictor import PetNatPredictor, MinimalModel, BasicModel, AdvancedModel
from .anomaly_detector import AnomalyDetector
from .feature_engineering import FeatureEngineer
from .models import ModelTier, ModelSelector


class ModelManager:
    """
    Manages all ML models for the wine production monitoring system.

    Responsibilities:
    - Load pre-trained models from disk
    - Provide thread-safe access to models
    - Cache model predictions
    - Handle model versioning
    - Graceful degradation when models unavailable
    """

    def __init__(self, model_dir: Optional[str] = None):
        """
        Initialize model manager.

        Args:
            model_dir: Directory containing pre-trained models
                       Defaults to ./pretrained relative to this file
        """
        if model_dir is None:
            # Default to pretrained directory relative to this file
            model_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'pretrained'
            )

        self.model_dir = model_dir
        self._lock = threading.Lock()

        # Model instances
        self._petnat_predictor: Optional[PetNatPredictor] = None
        self._anomaly_detector: Optional[AnomalyDetector] = None
        self._feature_engineer: Optional[FeatureEngineer] = None
        self._model_selector: Optional[ModelSelector] = None

        # Model metadata
        self.model_metadata: Dict[str, Any] = {}

        # Load models
        self._load_models()

    def _load_models(self):
        """Load all models and metadata."""
        with self._lock:
            # Load metadata if available
            metadata_path = os.path.join(self.model_dir, 'metadata.json')
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        self.model_metadata = json.load(f)
                except Exception as e:
                    print(f"Warning: Could not load metadata: {e}")
                    self.model_metadata = self._get_default_metadata()
            else:
                self.model_metadata = self._get_default_metadata()

            # Initialize core components (always available)
            self._feature_engineer = FeatureEngineer()
            self._model_selector = ModelSelector()

            # Initialize Pet Nat predictor
            try:
                self._petnat_predictor = PetNatPredictor(model_dir=self.model_dir)
                print("Pet Nat predictor loaded successfully")
            except Exception as e:
                print(f"Warning: Could not load Pet Nat predictor: {e}")
                self._petnat_predictor = PetNatPredictor()  # Use default

            # Initialize anomaly detector
            try:
                anomaly_model_path = os.path.join(self.model_dir, 'anomaly_detector.pkl')
                if os.path.exists(anomaly_model_path):
                    saved_data = joblib.load(anomaly_model_path)
                    self._anomaly_detector = AnomalyDetector()
                    if 'outlier_detector' in saved_data:
                        self._anomaly_detector.outlier_detector = saved_data['outlier_detector']
                        self._anomaly_detector.outlier_fitted = True
                    print("Anomaly detector loaded successfully")
                else:
                    self._anomaly_detector = AnomalyDetector()
                    print("Anomaly detector initialized with defaults")
            except Exception as e:
                print(f"Warning: Could not load anomaly detector: {e}")
                self._anomaly_detector = AnomalyDetector()

    def _get_default_metadata(self) -> Dict[str, Any]:
        """Get default metadata when no saved metadata exists."""
        return {
            'version': '1.0.0',
            'created': datetime.now().isoformat(),
            'models': {
                'minimal': {
                    'type': 'rule_based',
                    'sensors_required': ['bubble_counter'],
                    'description': 'Exponential decay model using bubble count only'
                },
                'basic': {
                    'type': 'regression',
                    'sensors_required': ['bubble_counter', 'gravity'],
                    'description': 'Polynomial regression with bubble and gravity'
                },
                'advanced': {
                    'type': 'gradient_boosting',
                    'sensors_required': ['bubble_counter', 'gravity', 'temperature'],
                    'description': 'Ensemble model with all sensors',
                    'trained': False
                },
                'anomaly_detector': {
                    'type': 'isolation_forest',
                    'description': 'Multi-strategy anomaly detection',
                    'trained': False
                }
            }
        }

    @property
    def petnat_predictor(self) -> PetNatPredictor:
        """Get Pet Nat predictor instance (thread-safe)."""
        with self._lock:
            if self._petnat_predictor is None:
                self._petnat_predictor = PetNatPredictor(model_dir=self.model_dir)
            return self._petnat_predictor

    @property
    def anomaly_detector(self) -> AnomalyDetector:
        """Get anomaly detector instance (thread-safe)."""
        with self._lock:
            if self._anomaly_detector is None:
                self._anomaly_detector = AnomalyDetector()
            return self._anomaly_detector

    @property
    def feature_engineer(self) -> FeatureEngineer:
        """Get feature engineer instance (thread-safe)."""
        with self._lock:
            if self._feature_engineer is None:
                self._feature_engineer = FeatureEngineer()
            return self._feature_engineer

    @property
    def model_selector(self) -> ModelSelector:
        """Get model selector instance (thread-safe)."""
        with self._lock:
            if self._model_selector is None:
                self._model_selector = ModelSelector()
            return self._model_selector

    def get_available_models(self) -> Dict[str, bool]:
        """
        Check which models are available.

        Returns:
            Dictionary mapping model names to availability
        """
        available = {
            'minimal': True,  # Always available (rule-based)
            'basic': True,    # Always available (rule-based)
            'advanced': False,
            'anomaly_detector': True
        }

        # Check for pre-trained advanced model
        advanced_path = os.path.join(self.model_dir, 'advanced_model.pkl')
        if os.path.exists(advanced_path):
            try:
                # Try to load to verify it's valid
                joblib.load(advanced_path)
                available['advanced'] = True
            except Exception:
                pass

        # Check for trained anomaly detector
        anomaly_path = os.path.join(self.model_dir, 'anomaly_detector.pkl')
        if os.path.exists(anomaly_path):
            available['anomaly_detector'] = True

        return available

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about loaded models.

        Returns:
            Dictionary with model information
        """
        return {
            'model_dir': self.model_dir,
            'metadata': self.model_metadata,
            'available_models': self.get_available_models(),
            'components': {
                'petnat_predictor': self._petnat_predictor is not None,
                'anomaly_detector': self._anomaly_detector is not None,
                'feature_engineer': self._feature_engineer is not None,
                'model_selector': self._model_selector is not None
            }
        }

    def save_model(
        self,
        model: Any,
        model_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Save a trained model to disk.

        Args:
            model: Model instance to save
            model_name: Name of the model (e.g., 'advanced_model')
            metadata: Optional metadata to save with model
        """
        with self._lock:
            os.makedirs(self.model_dir, exist_ok=True)

            # Save model
            model_path = os.path.join(self.model_dir, f'{model_name}.pkl')
            joblib.dump(model, model_path)

            # Update metadata
            if metadata:
                self.model_metadata['models'][model_name] = metadata

            # Save metadata
            metadata_path = os.path.join(self.model_dir, 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(self.model_metadata, f, indent=2)

            print(f"Model '{model_name}' saved to {model_path}")

    def reload_models(self):
        """Reload all models from disk."""
        print("Reloading models...")
        self._load_models()
        print("Models reloaded successfully")

    def get_recommended_tier(
        self,
        has_bubble: bool = True,
        has_gravity: bool = False,
        has_temperature: bool = False,
        has_ph: bool = False
    ) -> ModelTier:
        """
        Get recommended model tier based on available sensors.

        Args:
            has_bubble: Bubble counter available
            has_gravity: Gravity sensor available
            has_temperature: Temperature sensor available
            has_ph: pH sensor available

        Returns:
            Recommended ModelTier
        """
        if has_bubble and has_gravity and has_temperature and has_ph:
            # Check if advanced model is available
            if self.get_available_models()['advanced']:
                return ModelTier.ADVANCED
            else:
                return ModelTier.BASIC
        elif has_bubble and has_gravity:
            return ModelTier.BASIC
        elif has_bubble:
            return ModelTier.MINIMAL
        else:
            return ModelTier.MINIMAL  # Fallback

    def create_prediction_pipeline(self):
        """
        Create a complete prediction pipeline.

        Returns:
            Function that takes sensor data and returns predictions + anomalies
        """
        def pipeline(
            timestamps,
            bubble_counts=None,
            gravity=None,
            temperature=None,
            ph=None
        ):
            """
            Complete prediction pipeline.

            Args:
                timestamps: Array of timestamps
                bubble_counts: Bubble rates (optional)
                gravity: Gravity readings (optional)
                temperature: Temperature readings (optional)
                ph: pH readings (optional)

            Returns:
                Dictionary with predictions and anomaly results
            """
            results = {
                'timestamp': datetime.now().isoformat(),
                'prediction': None,
                'anomalies': [],
                'health_score': 100.0,
                'features': {}
            }

            try:
                # Extract features
                features = self.feature_engineer.extract_all_features(
                    timestamps=timestamps,
                    bubble_counts=bubble_counts,
                    gravity=gravity,
                    temperature=temperature,
                    ph=ph
                )
                results['features'] = features

                # Get prediction
                if bubble_counts is not None:
                    prediction = self.petnat_predictor.predict(
                        timestamps=timestamps,
                        bubble_counts=bubble_counts,
                        gravity=gravity,
                        temperature=temperature,
                        ph=ph
                    )
                    results['prediction'] = prediction.to_dict()

                # Detect anomalies
                anomalies = self.anomaly_detector.detect_anomalies(
                    timestamps=timestamps,
                    bubble_counts=bubble_counts,
                    gravity=gravity,
                    temperature=temperature,
                    ph=ph
                )
                results['anomalies'] = [a.to_dict() for a in anomalies]

                # Get health score
                results['health_score'] = self.anomaly_detector.get_health_score(anomalies)

                # Get anomaly summary
                results['anomaly_summary'] = self.anomaly_detector.get_summary(anomalies)

            except Exception as e:
                results['error'] = str(e)

            return results

        return pipeline

    def __repr__(self) -> str:
        """String representation of model manager."""
        available = self.get_available_models()
        available_count = sum(available.values())
        return f"ModelManager(model_dir='{self.model_dir}', models_available={available_count}/4)"
