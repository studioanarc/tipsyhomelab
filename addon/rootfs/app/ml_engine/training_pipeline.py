"""
Training Pipeline for Model Retraining

Provides functionality to retrain models on collected fermentation data.
Supports incremental learning and model evaluation.

Usage:
    1. Collect labeled fermentation data (actual bottling times)
    2. Run training pipeline to create/update models
    3. Evaluate model performance
    4. Deploy updated models
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import IsolationForest
import joblib
import json
import os
from datetime import datetime

from .feature_engineering import FeatureEngineer
from .models import ModelTier


class TrainingDataset:
    """
    Container for fermentation training data.

    Stores time-series data from multiple fermentations with labels
    (actual hours to bottling).
    """

    def __init__(self):
        """Initialize empty dataset."""
        self.fermentations: List[Dict[str, Any]] = []

    def add_fermentation(
        self,
        fermentation_id: str,
        timestamps: np.ndarray,
        bubble_counts: np.ndarray,
        actual_hours_to_bottle: float,
        gravity: Optional[np.ndarray] = None,
        temperature: Optional[np.ndarray] = None,
        ph: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a completed fermentation to the dataset.

        Args:
            fermentation_id: Unique identifier for this fermentation
            timestamps: Array of measurement timestamps
            bubble_counts: Bubble count rates
            actual_hours_to_bottle: Actual hours from this point until bottling
            gravity: Gravity readings (optional)
            temperature: Temperature readings (optional)
            ph: pH readings (optional)
            metadata: Additional metadata (wine type, yeast strain, etc.)
        """
        fermentation = {
            'id': fermentation_id,
            'timestamps': timestamps,
            'bubble_counts': bubble_counts,
            'gravity': gravity,
            'temperature': temperature,
            'ph': ph,
            'label': actual_hours_to_bottle,
            'metadata': metadata or {}
        }
        self.fermentations.append(fermentation)

    def save(self, filepath: str):
        """Save dataset to disk."""
        # Convert numpy arrays to lists for JSON serialization
        data = {
            'fermentations': [
                {
                    'id': f['id'],
                    'timestamps': f['timestamps'].tolist(),
                    'bubble_counts': f['bubble_counts'].tolist(),
                    'gravity': f['gravity'].tolist() if f['gravity'] is not None else None,
                    'temperature': f['temperature'].tolist() if f['temperature'] is not None else None,
                    'ph': f['ph'].tolist() if f['ph'] is not None else None,
                    'label': f['label'],
                    'metadata': f['metadata']
                }
                for f in self.fermentations
            ]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self, filepath: str):
        """Load dataset from disk."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        self.fermentations = []
        for f in data['fermentations']:
            self.fermentations.append({
                'id': f['id'],
                'timestamps': np.array(f['timestamps']),
                'bubble_counts': np.array(f['bubble_counts']),
                'gravity': np.array(f['gravity']) if f['gravity'] is not None else None,
                'temperature': np.array(f['temperature']) if f['temperature'] is not None else None,
                'ph': np.array(f['ph']) if f['ph'] is not None else None,
                'label': f['label'],
                'metadata': f['metadata']
            })

    def __len__(self) -> int:
        """Get number of fermentations in dataset."""
        return len(self.fermentations)


class ModelTrainer:
    """
    Trains ML models on fermentation data.

    Supports training different model tiers (MINIMAL, BASIC, ADVANCED)
    and provides cross-validation and evaluation metrics.
    """

    def __init__(self, random_state: int = 42):
        """
        Initialize model trainer.

        Args:
            random_state: Random seed for reproducibility
        """
        self.random_state = random_state
        self.feature_engineer = FeatureEngineer()

    def prepare_training_data(
        self,
        dataset: TrainingDataset,
        model_tier: ModelTier
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare training data by extracting features.

        Args:
            dataset: Training dataset
            model_tier: Which model tier to prepare data for

        Returns:
            Tuple of (X features, y labels, feature names)
        """
        X_list = []
        y_list = []
        feature_names = None

        for fermentation in dataset.fermentations:
            # Extract features based on model tier
            if model_tier == ModelTier.MINIMAL:
                # Only bubble counts
                if fermentation['bubble_counts'] is None:
                    continue
                features = self.feature_engineer.extract_all_features(
                    timestamps=fermentation['timestamps'],
                    bubble_counts=fermentation['bubble_counts']
                )
            elif model_tier == ModelTier.BASIC:
                # Bubble counts + gravity
                if fermentation['bubble_counts'] is None or fermentation['gravity'] is None:
                    continue
                features = self.feature_engineer.extract_all_features(
                    timestamps=fermentation['timestamps'],
                    bubble_counts=fermentation['bubble_counts'],
                    gravity=fermentation['gravity']
                )
            else:  # ADVANCED
                # All sensors
                if fermentation['bubble_counts'] is None:
                    continue
                features = self.feature_engineer.extract_all_features(
                    timestamps=fermentation['timestamps'],
                    bubble_counts=fermentation['bubble_counts'],
                    gravity=fermentation['gravity'],
                    temperature=fermentation['temperature'],
                    ph=fermentation['ph']
                )

            # Store feature names (consistent across all samples)
            if feature_names is None:
                feature_names = list(features.keys())

            # Convert to array
            X_list.append([features[name] for name in feature_names])
            y_list.append(fermentation['label'])

        X = np.array(X_list)
        y = np.array(y_list)

        return X, y, feature_names

    def train_basic_model(
        self,
        dataset: TrainingDataset,
        alpha: float = 1.0
    ) -> Dict[str, Any]:
        """
        Train BASIC tier model (Ridge regression).

        Args:
            dataset: Training dataset
            alpha: Regularization strength

        Returns:
            Dictionary with trained model and metadata
        """
        print("Training BASIC model (Ridge regression)...")

        # Prepare data
        X, y, feature_names = self.prepare_training_data(dataset, ModelTier.BASIC)

        if len(X) < 5:
            raise ValueError("Not enough training samples (need at least 5)")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=self.random_state
        )

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train model
        model = Ridge(alpha=alpha, random_state=self.random_state)
        model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred_train = model.predict(X_train_scaled)
        y_pred_test = model.predict(X_test_scaled)

        metrics = {
            'train_mae': mean_absolute_error(y_train, y_pred_train),
            'train_rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
            'train_r2': r2_score(y_train, y_pred_train),
            'test_mae': mean_absolute_error(y_test, y_pred_test),
            'test_rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
            'test_r2': r2_score(y_test, y_pred_test)
        }

        # Cross-validation
        cv_scores = cross_val_score(
            model, X_train_scaled, y_train,
            cv=min(5, len(X_train)),
            scoring='neg_mean_absolute_error'
        )
        metrics['cv_mae'] = -cv_scores.mean()
        metrics['cv_mae_std'] = cv_scores.std()

        print(f"BASIC model trained - Test MAE: {metrics['test_mae']:.2f}h, R²: {metrics['test_r2']:.3f}")

        return {
            'model': model,
            'scaler': scaler,
            'feature_names': feature_names,
            'metrics': metrics,
            'model_type': 'ridge_regression',
            'model_tier': ModelTier.BASIC.value,
            'n_samples': len(X),
            'trained_at': datetime.now().isoformat()
        }

    def train_advanced_model(
        self,
        dataset: TrainingDataset,
        model_type: str = 'gradient_boosting'
    ) -> Dict[str, Any]:
        """
        Train ADVANCED tier model (Gradient Boosting or Random Forest).

        Args:
            dataset: Training dataset
            model_type: 'gradient_boosting' or 'random_forest'

        Returns:
            Dictionary with trained model and metadata
        """
        print(f"Training ADVANCED model ({model_type})...")

        # Prepare data
        X, y, feature_names = self.prepare_training_data(dataset, ModelTier.ADVANCED)

        if len(X) < 10:
            raise ValueError("Not enough training samples (need at least 10)")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=self.random_state
        )

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train model
        if model_type == 'gradient_boosting':
            model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=4,
                min_samples_split=5,
                min_samples_leaf=3,
                subsample=0.8,
                random_state=self.random_state,
                loss='huber'
            )
        elif model_type == 'random_forest':
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=3,
                random_state=self.random_state,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred_train = model.predict(X_train_scaled)
        y_pred_test = model.predict(X_test_scaled)

        metrics = {
            'train_mae': mean_absolute_error(y_train, y_pred_train),
            'train_rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
            'train_r2': r2_score(y_train, y_pred_train),
            'test_mae': mean_absolute_error(y_test, y_pred_test),
            'test_rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
            'test_r2': r2_score(y_test, y_pred_test)
        }

        # Cross-validation
        cv_scores = cross_val_score(
            model, X_train_scaled, y_train,
            cv=min(5, len(X_train)),
            scoring='neg_mean_absolute_error'
        )
        metrics['cv_mae'] = -cv_scores.mean()
        metrics['cv_mae_std'] = cv_scores.std()

        # Feature importance
        if hasattr(model, 'feature_importances_'):
            feature_importance = dict(zip(feature_names, model.feature_importances_))
            # Sort by importance
            feature_importance = dict(
                sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            )
            metrics['feature_importance'] = feature_importance

        print(f"ADVANCED model trained - Test MAE: {metrics['test_mae']:.2f}h, R²: {metrics['test_r2']:.3f}")

        return {
            'model': model,
            'scaler': scaler,
            'feature_names': feature_names,
            'metrics': metrics,
            'model_type': model_type,
            'model_tier': ModelTier.ADVANCED.value,
            'n_samples': len(X),
            'trained_at': datetime.now().isoformat()
        }

    def train_anomaly_detector(
        self,
        dataset: TrainingDataset,
        contamination: float = 0.1
    ) -> Dict[str, Any]:
        """
        Train anomaly detector (Isolation Forest).

        Args:
            dataset: Training dataset (should include both normal and anomalous fermentations)
            contamination: Expected proportion of outliers

        Returns:
            Dictionary with trained model and metadata
        """
        print("Training anomaly detector (Isolation Forest)...")

        # Extract features from all fermentations
        X_list = []
        for fermentation in dataset.fermentations:
            features = self.feature_engineer.extract_all_features(
                timestamps=fermentation['timestamps'],
                bubble_counts=fermentation['bubble_counts'],
                gravity=fermentation['gravity'],
                temperature=fermentation['temperature'],
                ph=fermentation['ph']
            )
            X_list.append(list(features.values()))

        X = np.array(X_list)
        feature_names = list(dataset.fermentations[0] if len(dataset.fermentations) > 0 else {})

        if len(X) < 10:
            raise ValueError("Not enough training samples (need at least 10)")

        # Train Isolation Forest
        model = IsolationForest(
            contamination=contamination,
            random_state=self.random_state,
            n_estimators=100,
            max_samples='auto'
        )
        model.fit(X)

        # Predict anomaly scores
        anomaly_scores = model.decision_function(X)
        predictions = model.predict(X)

        # Calculate metrics
        n_anomalies = np.sum(predictions == -1)
        anomaly_rate = n_anomalies / len(predictions)

        metrics = {
            'n_samples': len(X),
            'n_anomalies_detected': int(n_anomalies),
            'anomaly_rate': anomaly_rate,
            'contamination': contamination
        }

        print(f"Anomaly detector trained - {n_anomalies}/{len(X)} anomalies detected ({anomaly_rate*100:.1f}%)")

        return {
            'outlier_detector': model,
            'feature_names': feature_names,
            'metrics': metrics,
            'model_type': 'isolation_forest',
            'n_samples': len(X),
            'trained_at': datetime.now().isoformat()
        }


class TrainingPipeline:
    """
    Complete training pipeline for all models.

    Orchestrates the training process:
    1. Load training data
    2. Train all model tiers
    3. Evaluate models
    4. Save models to disk
    """

    def __init__(self, output_dir: str):
        """
        Initialize training pipeline.

        Args:
            output_dir: Directory to save trained models
        """
        self.output_dir = output_dir
        self.trainer = ModelTrainer()
        os.makedirs(output_dir, exist_ok=True)

    def run_full_pipeline(
        self,
        dataset: TrainingDataset,
        train_basic: bool = True,
        train_advanced: bool = True,
        train_anomaly: bool = True
    ) -> Dict[str, Any]:
        """
        Run complete training pipeline.

        Args:
            dataset: Training dataset
            train_basic: Whether to train BASIC model
            train_advanced: Whether to train ADVANCED model
            train_anomaly: Whether to train anomaly detector

        Returns:
            Dictionary with all trained models and metrics
        """
        results = {
            'trained_at': datetime.now().isoformat(),
            'dataset_size': len(dataset),
            'models': {}
        }

        # Train BASIC model
        if train_basic:
            try:
                basic_result = self.trainer.train_basic_model(dataset)
                results['models']['basic'] = basic_result

                # Save model
                model_path = os.path.join(self.output_dir, 'basic_model.pkl')
                joblib.dump(basic_result, model_path)
                print(f"BASIC model saved to {model_path}")
            except Exception as e:
                print(f"Error training BASIC model: {e}")
                results['models']['basic'] = {'error': str(e)}

        # Train ADVANCED model
        if train_advanced:
            try:
                advanced_result = self.trainer.train_advanced_model(
                    dataset, model_type='gradient_boosting'
                )
                results['models']['advanced'] = advanced_result

                # Save model
                model_path = os.path.join(self.output_dir, 'advanced_model.pkl')
                joblib.dump(advanced_result, model_path)
                print(f"ADVANCED model saved to {model_path}")
            except Exception as e:
                print(f"Error training ADVANCED model: {e}")
                results['models']['advanced'] = {'error': str(e)}

        # Train anomaly detector
        if train_anomaly:
            try:
                anomaly_result = self.trainer.train_anomaly_detector(dataset)
                results['models']['anomaly'] = anomaly_result

                # Save model
                model_path = os.path.join(self.output_dir, 'anomaly_detector.pkl')
                joblib.dump(anomaly_result, model_path)
                print(f"Anomaly detector saved to {model_path}")
            except Exception as e:
                print(f"Error training anomaly detector: {e}")
                results['models']['anomaly'] = {'error': str(e)}

        # Save metadata
        metadata = {
            'version': '1.0.0',
            'created': results['trained_at'],
            'dataset_size': results['dataset_size'],
            'models': {}
        }

        for model_name, model_result in results['models'].items():
            if 'error' not in model_result:
                metadata['models'][model_name] = {
                    'model_type': model_result.get('model_type'),
                    'model_tier': model_result.get('model_tier'),
                    'n_samples': model_result.get('n_samples'),
                    'metrics': model_result.get('metrics'),
                    'trained_at': model_result.get('trained_at')
                }

        metadata_path = os.path.join(self.output_dir, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata saved to {metadata_path}")

        return results

    def evaluate_model(
        self,
        model_path: str,
        test_dataset: TrainingDataset
    ) -> Dict[str, float]:
        """
        Evaluate a trained model on test data.

        Args:
            model_path: Path to saved model
            test_dataset: Test dataset

        Returns:
            Dictionary of evaluation metrics
        """
        # Load model
        model_data = joblib.load(model_path)
        model = model_data['model']
        scaler = model_data['scaler']
        feature_names = model_data['feature_names']
        model_tier = ModelTier(model_data['model_tier'])

        # Prepare test data
        X_test, y_test, _ = self.trainer.prepare_training_data(test_dataset, model_tier)

        if len(X_test) == 0:
            raise ValueError("No test samples available")

        # Scale and predict
        X_test_scaled = scaler.transform(X_test)
        y_pred = model.predict(X_test_scaled)

        # Calculate metrics
        metrics = {
            'mae': mean_absolute_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'r2': r2_score(y_test, y_pred),
            'n_samples': len(y_test)
        }

        print(f"Evaluation - MAE: {metrics['mae']:.2f}h, RMSE: {metrics['rmse']:.2f}h, R²: {metrics['r2']:.3f}")

        return metrics
