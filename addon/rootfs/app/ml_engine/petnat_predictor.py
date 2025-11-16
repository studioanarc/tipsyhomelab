"""
Pet Nat Bottling Time Predictor

Implements three-tier prediction models for determining optimal Pet Nat bottling time:
- MINIMAL: Bubble count only (CO2 production curve fitting)
- BASIC: Bubble count + gravity (polynomial regression, correlation analysis)
- ADVANCED: All sensors (ensemble methods, multi-variate analysis)

Target: Predict hours until fermentation reaches ideal bottling point (1-2 bubbles/min, ~1.002 SG)
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
import joblib
import os

from .feature_engineering import FeatureEngineer
from .models import ModelTier, ModelSelector, PredictionResult, FallbackStrategy


class MinimalModel:
    """
    MINIMAL tier model - uses ONLY bubble count data.

    Algorithm:
    1. Exponential decay curve fitting: bubble_rate(t) = A * exp(-k*t) + C
    2. Extrapolate to target bubble rate (1-2 bubbles/min)
    3. Rule-based thresholds for safety checks
    4. Simple trend analysis

    Advantages:
    - Works with minimal sensors
    - Fast and interpretable
    - No training data required

    Disadvantages:
    - Lower accuracy
    - Doesn't account for temperature, gravity
    - Assumes ideal exponential decay
    """

    def __init__(self, target_bubble_rate: float = 1.5):
        """
        Initialize minimal model.

        Args:
            target_bubble_rate: Target bubble rate for bottling (bubbles/minute)
        """
        self.target_bubble_rate = target_bubble_rate
        self.feature_engineer = FeatureEngineer()

    def predict(
        self,
        timestamps: np.ndarray,
        bubble_counts: np.ndarray
    ) -> PredictionResult:
        """
        Predict hours until bottling using bubble count only.

        Args:
            timestamps: Array of timestamps
            bubble_counts: Bubble count rates (bubbles/minute)

        Returns:
            PredictionResult with prediction and uncertainty
        """
        # Extract features
        features = self.feature_engineer.extract_all_features(
            timestamps=timestamps,
            bubble_counts=bubble_counts
        )

        # Get current bubble rate
        current_rate = features['bubble_current']

        # If already at or below target, bottle immediately
        if current_rate <= self.target_bubble_rate:
            return PredictionResult(
                value=0.0,
                confidence=0.8,
                uncertainty_lower=0.0,
                uncertainty_upper=6.0,  # Within 6 hours
                model_tier=ModelTier.MINIMAL,
                features_used=['bubble_current'],
                warnings=['Already at target bubble rate - ready for bottling']
            )

        # Method 1: Exponential decay model
        decay_rate = features['bubble_decay_rate']
        decay_r2 = features['bubble_decay_r2']

        if decay_rate > 0.001 and decay_r2 > 0.3:
            # Good exponential fit
            # current * exp(-k * t) = target
            # t = -ln(target / current) / k
            hours_exp = -np.log(self.target_bubble_rate / current_rate) / decay_rate
            hours_exp = max(0, min(hours_exp, 500))  # Cap at ~3 weeks

            # Confidence based on R²
            confidence = 0.5 + 0.3 * decay_r2
        else:
            # Poor exponential fit, use linear trend
            trend = features['bubble_recent_trend']
            if trend < -0.01:  # Decreasing
                hours_exp = (current_rate - self.target_bubble_rate) / abs(trend)
                hours_exp = max(0, min(hours_exp, 500))
                confidence = 0.4
            else:
                # Not decreasing properly - anomaly
                hours_exp = 999
                confidence = 0.2

        # Method 2: Time-based estimate from decay model
        hours_from_feature = features['bubble_time_to_threshold']

        # Combine estimates (weighted average if both reasonable)
        if hours_exp < 500 and hours_from_feature < 500:
            prediction = (hours_exp * 0.6 + hours_from_feature * 0.4)
        elif hours_exp < 500:
            prediction = hours_exp
        elif hours_from_feature < 500:
            prediction = hours_from_feature
        else:
            prediction = 999  # Unable to predict

        # Uncertainty bounds
        selector = ModelSelector()
        lower, upper = selector.calculate_uncertainty_bounds(
            prediction, confidence, ModelTier.MINIMAL
        )

        # Warnings
        warnings = []
        if decay_r2 < 0.5:
            warnings.append("Bubble rate doesn't fit exponential decay well")
        if features['bubble_cv'] > 1.0:
            warnings.append("High bubble rate variability")
        if prediction > 300:
            warnings.append("Prediction is far in future - may be unreliable")

        return PredictionResult(
            value=prediction,
            confidence=confidence,
            uncertainty_lower=lower,
            uncertainty_upper=upper,
            model_tier=ModelTier.MINIMAL,
            features_used=['bubble_current', 'bubble_decay_rate', 'bubble_recent_trend'],
            warnings=warnings
        )


class BasicModel:
    """
    BASIC tier model - uses bubble count + gravity data.

    Algorithm:
    1. Polynomial regression on gravity curve (2nd degree)
    2. CO2 vs gravity correlation analysis
    3. Multi-objective prediction (both bubble rate AND gravity targets)
    4. Ridge regression to combine signals

    Advantages:
    - Much better accuracy than minimal
    - Accounts for actual fermentation progress (gravity)
    - Can detect stuck fermentation

    Disadvantages:
    - Requires iSpindel or manual gravity readings
    - Still doesn't account for temperature effects
    """

    def __init__(
        self,
        target_bubble_rate: float = 1.5,
        target_gravity: float = 1.002
    ):
        """
        Initialize basic model.

        Args:
            target_bubble_rate: Target bubble rate for bottling
            target_gravity: Target specific gravity for bottling
        """
        self.target_bubble_rate = target_bubble_rate
        self.target_gravity = target_gravity
        self.feature_engineer = FeatureEngineer()
        self.scaler = StandardScaler()
        self.model = Ridge(alpha=1.0)
        self.is_fitted = False

    def predict(
        self,
        timestamps: np.ndarray,
        bubble_counts: np.ndarray,
        gravity: np.ndarray
    ) -> PredictionResult:
        """
        Predict hours until bottling using bubble count and gravity.

        Args:
            timestamps: Array of timestamps
            bubble_counts: Bubble count rates
            gravity: Specific gravity readings

        Returns:
            PredictionResult with prediction and uncertainty
        """
        # Extract features
        features = self.feature_engineer.extract_all_features(
            timestamps=timestamps,
            bubble_counts=bubble_counts,
            gravity=gravity
        )

        # Check if already at target
        current_bubble = features['bubble_current']
        current_gravity = features['gravity_current']

        if current_bubble <= self.target_bubble_rate and current_gravity <= self.target_gravity + 0.001:
            return PredictionResult(
                value=0.0,
                confidence=0.9,
                uncertainty_lower=0.0,
                uncertainty_upper=3.0,
                model_tier=ModelTier.BASIC,
                features_used=['bubble_current', 'gravity_current'],
                warnings=['At target conditions - ready for bottling']
            )

        # Estimate hours from bubble rate (exponential decay)
        bubble_decay = features['bubble_decay_rate']
        if bubble_decay > 0.001 and current_bubble > self.target_bubble_rate:
            hours_from_bubbles = -np.log(self.target_bubble_rate / current_bubble) / bubble_decay
            hours_from_bubbles = max(0, min(hours_from_bubbles, 500))
        else:
            hours_from_bubbles = 999

        # Estimate hours from gravity (linear extrapolation)
        gravity_rate = features['gravity_rate']
        if gravity_rate < -0.0001 and current_gravity > self.target_gravity:
            hours_from_gravity = (current_gravity - self.target_gravity) / abs(gravity_rate)
            hours_from_gravity = max(0, min(hours_from_gravity, 500))
        else:
            # Use polynomial prediction
            hours_from_gravity = features.get('hours_to_target_gravity', 999)

        # Combine estimates using correlation
        correlation = features.get('bubble_gravity_correlation', -0.8)

        if hours_from_bubbles < 500 and hours_from_gravity < 500:
            # Both estimates valid
            # Weight by correlation strength and R² values
            bubble_weight = 0.4 + 0.2 * features['bubble_decay_r2']
            gravity_weight = 0.4 + 0.2 * features['gravity_poly_r2']

            # Normalize weights
            total_weight = bubble_weight + gravity_weight
            bubble_weight /= total_weight
            gravity_weight /= total_weight

            prediction = bubble_weight * hours_from_bubbles + gravity_weight * hours_from_gravity

            # If estimates disagree significantly, lower confidence
            estimate_diff = abs(hours_from_bubbles - hours_from_gravity)
            if estimate_diff > 48:  # More than 2 days difference
                confidence = 0.5
            else:
                confidence = 0.7 + 0.1 * (1 - estimate_diff / 48)

        elif hours_from_bubbles < 500:
            prediction = hours_from_bubbles
            confidence = 0.6
        elif hours_from_gravity < 500:
            prediction = hours_from_gravity
            confidence = 0.6
        else:
            # Can't predict - use fallback
            prediction = 999
            confidence = 0.3

        # Adjust confidence based on data quality
        selector = ModelSelector()
        warnings = []
        data_quality = selector._assess_data_quality(features, warnings)
        confidence *= (0.7 + 0.3 * data_quality)

        # Uncertainty bounds
        lower, upper = selector.calculate_uncertainty_bounds(
            prediction, confidence, ModelTier.BASIC
        )

        # Additional warnings
        if abs(correlation) < 0.3:
            warnings.append("Weak bubble-gravity correlation - unusual fermentation")
        if estimate_diff > 48 and hours_from_bubbles < 500 and hours_from_gravity < 500:
            warnings.append(f"Bubble and gravity estimates differ by {estimate_diff:.1f} hours")

        return PredictionResult(
            value=prediction,
            confidence=confidence,
            uncertainty_lower=lower,
            uncertainty_upper=upper,
            model_tier=ModelTier.BASIC,
            features_used=[
                'bubble_current', 'bubble_decay_rate', 'gravity_current',
                'gravity_rate', 'bubble_gravity_correlation'
            ],
            warnings=warnings
        )


class AdvancedModel:
    """
    ADVANCED tier model - uses all available sensors.

    Algorithm:
    1. Gradient Boosting Regressor (ensemble of decision trees)
    2. Temperature compensation for fermentation rate
    3. pH consideration for yeast health
    4. Multi-variate time series features
    5. Cross-validation for uncertainty estimation

    Advantages:
    - Highest accuracy
    - Accounts for all environmental factors
    - Robust to outliers
    - Provides uncertainty estimates

    Disadvantages:
    - Requires all sensors
    - Needs training data
    - More computationally intensive
    - Less interpretable (black box)
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        target_bubble_rate: float = 1.5,
        target_gravity: float = 1.002
    ):
        """
        Initialize advanced model.

        Args:
            model_path: Path to pre-trained model (optional)
            target_bubble_rate: Target bubble rate
            target_gravity: Target gravity
        """
        self.target_bubble_rate = target_bubble_rate
        self.target_gravity = target_gravity
        self.feature_engineer = FeatureEngineer()
        self.scaler = StandardScaler()

        # Gradient Boosting model for robust predictions
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            min_samples_split=5,
            min_samples_leaf=3,
            subsample=0.8,
            random_state=42,
            loss='huber'  # Robust to outliers
        )

        self.is_fitted = False

        # Load pre-trained model if available
        if model_path and os.path.exists(model_path):
            try:
                saved_data = joblib.load(model_path)
                self.model = saved_data['model']
                self.scaler = saved_data['scaler']
                self.is_fitted = True
            except Exception as e:
                print(f"Warning: Could not load model from {model_path}: {e}")

    def predict(
        self,
        timestamps: np.ndarray,
        bubble_counts: np.ndarray,
        gravity: np.ndarray,
        temperature: np.ndarray,
        ph: Optional[np.ndarray] = None
    ) -> PredictionResult:
        """
        Predict hours until bottling using all sensors.

        Args:
            timestamps: Array of timestamps
            bubble_counts: Bubble count rates
            gravity: Specific gravity readings
            temperature: Temperature readings
            ph: pH readings (optional)

        Returns:
            PredictionResult with prediction and uncertainty
        """
        # Extract all features
        features = self.feature_engineer.extract_all_features(
            timestamps=timestamps,
            bubble_counts=bubble_counts,
            gravity=gravity,
            temperature=temperature,
            ph=ph
        )

        # Check if already at target
        if features['bubble_current'] <= self.target_bubble_rate and \
           features['gravity_current'] <= self.target_gravity + 0.001:
            return PredictionResult(
                value=0.0,
                confidence=0.95,
                uncertainty_lower=0.0,
                uncertainty_upper=2.0,
                model_tier=ModelTier.ADVANCED,
                features_used=list(features.keys()),
                warnings=['At target conditions - ready for bottling']
            )

        # If model is fitted (pre-trained), use it
        if self.is_fitted:
            prediction, confidence = self._predict_with_model(features)
        else:
            # Fallback to sophisticated rule-based approach
            prediction, confidence = self._predict_rule_based_advanced(features)

        # Uncertainty bounds
        selector = ModelSelector()
        warnings = []
        data_quality = selector._assess_data_quality(features, warnings)
        confidence *= (0.8 + 0.2 * data_quality)

        lower, upper = selector.calculate_uncertainty_bounds(
            prediction, confidence, ModelTier.ADVANCED
        )

        # Advanced warnings
        self._add_advanced_warnings(features, warnings)

        return PredictionResult(
            value=prediction,
            confidence=confidence,
            uncertainty_lower=lower,
            uncertainty_upper=upper,
            model_tier=ModelTier.ADVANCED,
            features_used=list(features.keys()),
            warnings=warnings
        )

    def _predict_with_model(self, features: Dict[str, float]) -> Tuple[float, float]:
        """Use trained ML model for prediction."""
        # Select features for model
        feature_names = self._get_model_features()
        X = np.array([features.get(f, 0.0) for f in feature_names]).reshape(1, -1)

        # Scale features
        X_scaled = self.scaler.transform(X)

        # Predict
        prediction = self.model.predict(X_scaled)[0]
        prediction = max(0, min(prediction, 500))

        # Estimate confidence from model's staged predictions (boosting stages)
        # Get predictions from different stages to estimate variance
        staged_predictions = list(self.model.staged_predict(X_scaled))
        if len(staged_predictions) > 10:
            # Use last 10 stages for variance estimation
            recent_predictions = [p[0] for p in staged_predictions[-10:]]
            variance = np.var(recent_predictions)
            # Higher variance = lower confidence
            confidence = 0.85 * np.exp(-variance / 100)
        else:
            confidence = 0.8

        return prediction, confidence

    def _predict_rule_based_advanced(
        self,
        features: Dict[str, float]
    ) -> Tuple[float, float]:
        """
        Advanced rule-based prediction using all features.

        Uses temperature compensation and multi-signal fusion.
        """
        # Temperature-compensated bubble estimate
        bubble_compensated = features.get('bubble_temp_compensated', features['bubble_current'])
        temp_factor = features.get('bubble_temp_compensation_factor', 1.0)

        decay_rate = features['bubble_decay_rate']
        if decay_rate > 0.001:
            # Adjust decay rate for temperature
            adjusted_decay = decay_rate * temp_factor
            hours_from_bubbles = -np.log(self.target_bubble_rate / bubble_compensated) / adjusted_decay
            hours_from_bubbles = max(0, min(hours_from_bubbles, 500))
        else:
            hours_from_bubbles = 999

        # Gravity estimate
        hours_from_gravity = features.get('hours_to_target_gravity', 999)

        # Combine with weighted average based on R² values
        bubble_r2 = features['bubble_decay_r2']
        gravity_r2 = features.get('gravity_poly_r2', 0)

        if hours_from_bubbles < 500 and hours_from_gravity < 500:
            # Weight by model fit quality
            bubble_weight = bubble_r2
            gravity_weight = gravity_r2
            total_weight = bubble_weight + gravity_weight + 1e-6

            prediction = (
                bubble_weight * hours_from_bubbles +
                gravity_weight * hours_from_gravity
            ) / total_weight

            confidence = 0.75 + 0.1 * min(bubble_r2, gravity_r2)
        elif hours_from_bubbles < 500:
            prediction = hours_from_bubbles
            confidence = 0.7
        elif hours_from_gravity < 500:
            prediction = hours_from_gravity
            confidence = 0.7
        else:
            prediction = 999
            confidence = 0.3

        return prediction, confidence

    def _get_model_features(self) -> List[str]:
        """Get list of features used by ML model."""
        return [
            'bubble_current', 'bubble_mean', 'bubble_std', 'bubble_decay_rate',
            'bubble_rate_change', 'co2_cumulative', 'bubble_recent_trend',
            'gravity_current', 'gravity_delta', 'apparent_attenuation',
            'gravity_rate', 'temp_current', 'temp_mean', 'temp_std',
            'bubble_gravity_correlation', 'bubble_temp_correlation',
            'fermentation_age_hours', 'measurement_count'
        ]

    def _add_advanced_warnings(
        self,
        features: Dict[str, float],
        warnings: List[str]
    ):
        """Add advanced warnings based on multi-variate analysis."""
        # Temperature warnings
        temp_current = features.get('temp_current', 20)
        if temp_current < 15:
            warnings.append(f"Low temperature ({temp_current:.1f}°C) - fermentation may be slow")
        elif temp_current > 25:
            warnings.append(f"High temperature ({temp_current:.1f}°C) - risk of stressed yeast")

        # pH warnings (if available)
        if 'ph_current' in features:
            ph = features['ph_current']
            if ph < 3.0:
                warnings.append(f"Very low pH ({ph:.2f}) - possible infection or stuck fermentation")
            elif ph > 4.0:
                warnings.append(f"High pH ({ph:.2f}) - unusual for wine fermentation")

        # Attenuation warnings
        attenuation = features.get('apparent_attenuation', 0)
        if attenuation > 90:
            warnings.append("Very high attenuation - verify gravity readings")
        elif attenuation < 20 and features['fermentation_age_hours'] > 48:
            warnings.append("Low attenuation for fermentation age - may be stuck")

        # Cross-correlation warnings
        if abs(features.get('bubble_temp_correlation', 0)) > 0.7:
            warnings.append("Strong temperature-bubble correlation - temperature effects significant")


class PetNatPredictor:
    """
    Main predictor class that selects and uses appropriate model tier.

    Automatically selects MINIMAL, BASIC, or ADVANCED model based on
    available sensor data and data quality.
    """

    def __init__(self, model_dir: Optional[str] = None):
        """
        Initialize Pet Nat predictor.

        Args:
            model_dir: Directory containing pre-trained models
        """
        self.model_dir = model_dir
        self.selector = ModelSelector()

        # Initialize all models
        self.minimal_model = MinimalModel()
        self.basic_model = BasicModel()

        # Load advanced model if available
        advanced_model_path = None
        if model_dir:
            advanced_model_path = os.path.join(model_dir, 'advanced_model.pkl')

        self.advanced_model = AdvancedModel(model_path=advanced_model_path)

    def predict(
        self,
        timestamps: np.ndarray,
        bubble_counts: Optional[np.ndarray] = None,
        gravity: Optional[np.ndarray] = None,
        temperature: Optional[np.ndarray] = None,
        ph: Optional[np.ndarray] = None
    ) -> PredictionResult:
        """
        Predict hours until bottling using best available model.

        Args:
            timestamps: Array of timestamps
            bubble_counts: Bubble count rates (required)
            gravity: Specific gravity readings (optional)
            temperature: Temperature readings (optional)
            ph: pH readings (optional)

        Returns:
            PredictionResult with prediction, confidence, and uncertainty
        """
        if bubble_counts is None or len(bubble_counts) == 0:
            # No data - return fallback
            return FallbackStrategy.get_rule_based_prediction({})

        # Extract features for model selection
        feature_engineer = FeatureEngineer()
        features = feature_engineer.extract_all_features(
            timestamps=timestamps,
            bubble_counts=bubble_counts,
            gravity=gravity,
            temperature=temperature,
            ph=ph
        )

        # Select model tier
        has_bubble = bubble_counts is not None and len(bubble_counts) > 0
        has_gravity = gravity is not None and len(gravity) > 0
        has_temperature = temperature is not None and len(temperature) > 0
        has_ph = ph is not None and len(ph) > 0

        model_tier, tier_warnings = self.selector.select_model_tier(
            features=features,
            has_bubble=has_bubble,
            has_gravity=has_gravity,
            has_temperature=has_temperature,
            has_ph=has_ph
        )

        # Use selected model
        try:
            if model_tier == ModelTier.ADVANCED:
                result = self.advanced_model.predict(
                    timestamps, bubble_counts, gravity, temperature, ph
                )
            elif model_tier == ModelTier.BASIC:
                result = self.basic_model.predict(
                    timestamps, bubble_counts, gravity
                )
            else:  # MINIMAL
                result = self.minimal_model.predict(
                    timestamps, bubble_counts
                )

            # Add tier selection warnings
            result.warnings.extend(tier_warnings)
            return result

        except Exception as e:
            # Fallback on error
            fallback_result = FallbackStrategy.get_rule_based_prediction(features)
            fallback_result.warnings.append(f"Model failed: {str(e)}")
            return fallback_result
