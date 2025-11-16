"""
Model Selection and Uncertainty Quantification

Determines which prediction model to use based on available sensors,
provides confidence scores, and implements fallback strategies.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass


class ModelTier(Enum):
    """Available model tiers based on sensor configuration."""
    MINIMAL = "minimal"      # Bubble count only
    BASIC = "basic"         # Bubble count + gravity
    ADVANCED = "advanced"   # All sensors


@dataclass
class PredictionResult:
    """
    Container for prediction results with uncertainty quantification.

    Attributes:
        value: Predicted value (e.g., hours until bottling)
        confidence: Confidence score (0-1)
        uncertainty_lower: Lower bound of prediction interval
        uncertainty_upper: Upper bound of prediction interval
        model_tier: Which model tier was used
        features_used: List of features used in prediction
        warnings: Any warnings about data quality or model limitations
    """
    value: float
    confidence: float
    uncertainty_lower: float
    uncertainty_upper: float
    model_tier: ModelTier
    features_used: List[str]
    warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'value': self.value,
            'confidence': self.confidence,
            'uncertainty_lower': self.uncertainty_lower,
            'uncertainty_upper': self.uncertainty_upper,
            'model_tier': self.model_tier.value,
            'features_used': self.features_used,
            'warnings': self.warnings
        }


class ModelSelector:
    """
    Selects appropriate model tier based on available sensors and data quality.

    The selector implements a decision tree:
    1. Check which sensors are available and have valid data
    2. Assess data quality (sufficient history, no anomalies)
    3. Select highest tier model that can be reliably used
    4. Provide fallback to simpler models if data quality is poor
    """

    def __init__(self, min_data_points: int = 10, min_fermentation_hours: int = 6):
        """
        Initialize model selector.

        Args:
            min_data_points: Minimum number of data points required
            min_fermentation_hours: Minimum fermentation time for reliable predictions
        """
        self.min_data_points = min_data_points
        self.min_fermentation_hours = min_fermentation_hours

    def select_model_tier(
        self,
        features: Dict[str, float],
        has_bubble: bool = True,
        has_gravity: bool = False,
        has_temperature: bool = False,
        has_ph: bool = False
    ) -> Tuple[ModelTier, List[str]]:
        """
        Select appropriate model tier based on available sensors and data quality.

        Args:
            features: Extracted features from current fermentation
            has_bubble: Bubble counter available
            has_gravity: Gravity sensor available
            has_temperature: Temperature sensor available
            has_ph: pH sensor available

        Returns:
            Tuple of (selected model tier, list of warnings)
        """
        warnings = []

        # Check data quality
        data_quality = self._assess_data_quality(features, warnings)

        # Sensor availability check
        if not has_bubble:
            warnings.append("No bubble counter data - cannot make predictions")
            return ModelTier.MINIMAL, warnings

        # Select tier based on sensors and data quality
        if has_bubble and has_gravity and has_temperature and has_ph and data_quality >= 0.8:
            return ModelTier.ADVANCED, warnings
        elif has_bubble and has_gravity and data_quality >= 0.6:
            return ModelTier.BASIC, warnings
        elif has_bubble:
            if data_quality < 0.4:
                warnings.append("Limited data quality - predictions may be unreliable")
            return ModelTier.MINIMAL, warnings
        else:
            warnings.append("Insufficient sensor data")
            return ModelTier.MINIMAL, warnings

    def _assess_data_quality(
        self,
        features: Dict[str, float],
        warnings: List[str]
    ) -> float:
        """
        Assess data quality based on multiple factors.

        Returns quality score from 0-1 where:
        - 1.0: Excellent data quality
        - 0.5: Moderate quality
        - 0.0: Poor quality

        Args:
            features: Extracted features
            warnings: List to append warnings to

        Returns:
            Quality score (0-1)
        """
        quality_score = 1.0

        # Check fermentation age
        age_hours = features.get('fermentation_age_hours', 0)
        if age_hours < self.min_fermentation_hours:
            quality_score *= 0.5
            warnings.append(f"Early fermentation ({age_hours:.1f}h) - predictions less reliable")

        # Check number of measurements
        measurement_count = features.get('measurement_count', 0)
        if measurement_count < self.min_data_points:
            quality_score *= 0.6
            warnings.append(f"Limited measurements ({measurement_count}) - need more data")

        # Check measurement interval consistency
        interval_std = features.get('measurement_interval_std', 0)
        interval_mean = features.get('measurement_interval_mean', 1)
        if interval_std / (interval_mean + 1e-6) > 0.5:
            quality_score *= 0.9
            warnings.append("Irregular measurement intervals detected")

        # Check bubble rate consistency (high CV indicates problems)
        bubble_cv = features.get('bubble_cv', 0)
        if bubble_cv > 1.0:
            quality_score *= 0.8
            warnings.append("High bubble rate variability - possible measurement issues")

        # Check if fermentation appears stuck (for gravity-enabled models)
        if 'gravity_recent_trend' in features:
            if abs(features['gravity_recent_trend']) < 0.0001 and age_hours > 24:
                quality_score *= 0.7
                warnings.append("Gravity trend is flat - possible stuck fermentation")

        # Check bubble decay model fit
        decay_r2 = features.get('bubble_decay_r2', 0)
        if decay_r2 < 0.5:
            quality_score *= 0.9
            warnings.append("Bubble rate doesn't fit expected decay pattern well")

        return max(0.0, min(1.0, quality_score))

    def calculate_confidence(
        self,
        model_tier: ModelTier,
        features: Dict[str, float],
        model_variance: float = 0.0
    ) -> float:
        """
        Calculate confidence score for prediction.

        Confidence based on:
        - Model tier (advanced models are more confident)
        - Data quality
        - Model fit quality (R² values)
        - Model variance (from ensemble or cross-validation)

        Args:
            model_tier: Selected model tier
            features: Extracted features
            model_variance: Variance from model (if available)

        Returns:
            Confidence score (0-1)
        """
        # Base confidence by tier
        tier_confidence = {
            ModelTier.MINIMAL: 0.6,
            ModelTier.BASIC: 0.75,
            ModelTier.ADVANCED: 0.85
        }
        confidence = tier_confidence[model_tier]

        # Adjust for data quality
        warnings = []
        data_quality = self._assess_data_quality(features, warnings)
        confidence *= (0.5 + 0.5 * data_quality)  # Scale from 50-100% of base

        # Adjust for model fit quality
        if model_tier == ModelTier.MINIMAL:
            # Use bubble decay R²
            decay_r2 = features.get('bubble_decay_r2', 0)
            confidence *= (0.7 + 0.3 * decay_r2)

        elif model_tier == ModelTier.BASIC:
            # Use both bubble and gravity fit
            decay_r2 = features.get('bubble_decay_r2', 0)
            gravity_r2 = features.get('gravity_poly_r2', 0)
            avg_r2 = (decay_r2 + gravity_r2) / 2
            confidence *= (0.7 + 0.3 * avg_r2)

        # Adjust for model variance (if provided)
        if model_variance > 0:
            # Higher variance means lower confidence
            variance_factor = np.exp(-model_variance / 10.0)  # Decay function
            confidence *= variance_factor

        # Ensure confidence is in [0, 1]
        return max(0.0, min(1.0, confidence))

    def calculate_uncertainty_bounds(
        self,
        prediction: float,
        confidence: float,
        model_tier: ModelTier
    ) -> Tuple[float, float]:
        """
        Calculate uncertainty bounds (prediction interval).

        Uses confidence score to determine interval width.
        Higher confidence = narrower interval.

        Args:
            prediction: Point prediction value
            confidence: Confidence score (0-1)
            model_tier: Model tier used

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        # Base uncertainty as percentage of prediction
        # Lower confidence = wider interval
        base_uncertainty = {
            ModelTier.MINIMAL: 0.30,    # ±30% for minimal
            ModelTier.BASIC: 0.20,      # ±20% for basic
            ModelTier.ADVANCED: 0.15    # ±15% for advanced
        }

        uncertainty_pct = base_uncertainty[model_tier]

        # Adjust by confidence (low confidence = wider interval)
        # confidence=1.0 -> use base uncertainty
        # confidence=0.5 -> double the uncertainty
        adjusted_uncertainty = uncertainty_pct / (confidence + 0.3)

        # Calculate bounds
        margin = prediction * adjusted_uncertainty
        lower = max(0.0, prediction - margin)
        upper = prediction + margin

        return lower, upper


class FallbackStrategy:
    """
    Implements fallback strategies when primary model fails or is unreliable.

    Fallback hierarchy:
    1. ADVANCED → BASIC (drop pH, temperature if unreliable)
    2. BASIC → MINIMAL (use only bubble count)
    3. MINIMAL → Rule-based heuristics
    """

    @staticmethod
    def get_rule_based_prediction(features: Dict[str, float]) -> PredictionResult:
        """
        Simple rule-based prediction when ML models cannot be used.

        Uses domain knowledge about Pet Nat fermentation:
        - Typically bottles at 1-3 bubbles/minute
        - Fermentation usually complete in 7-21 days
        - Exponential decay of CO2 production

        Args:
            features: Extracted features

        Returns:
            PredictionResult with rule-based estimate
        """
        bubble_current = features.get('bubble_current', 0)
        bubble_decay_rate = features.get('bubble_decay_rate', 0)
        age_hours = features.get('fermentation_age_hours', 0)

        warnings = ["Using rule-based fallback - ML model unavailable"]

        # Target: 1-2 bubbles/minute for Pet Nat bottling
        target_bubble_rate = 1.5

        if bubble_current <= target_bubble_rate:
            # Already at bottling point
            hours_to_bottle = 0
            warnings.append("Already at target bubble rate")
        elif bubble_decay_rate > 0:
            # Use exponential decay to estimate
            # bubble_current * exp(-decay_rate * t) = target
            # t = -ln(target / current) / decay_rate
            hours_to_bottle = -np.log(target_bubble_rate / bubble_current) / bubble_decay_rate
            hours_to_bottle = min(hours_to_bottle, 500)  # Cap at ~3 weeks
        else:
            # No decay detected, use linear approximation
            bubble_trend = features.get('bubble_recent_trend', 0)
            if bubble_trend < -0.01:  # Decreasing
                hours_to_bottle = (bubble_current - target_bubble_rate) / abs(bubble_trend)
                hours_to_bottle = min(hours_to_bottle, 500)
            else:
                # Stalled or increasing - can't predict
                hours_to_bottle = 999
                warnings.append("Fermentation not following expected pattern")

        # Conservative confidence for rule-based
        confidence = 0.4

        # Wide uncertainty bounds
        lower = max(0, hours_to_bottle * 0.5)
        upper = hours_to_bottle * 2.0

        return PredictionResult(
            value=hours_to_bottle,
            confidence=confidence,
            uncertainty_lower=lower,
            uncertainty_upper=upper,
            model_tier=ModelTier.MINIMAL,
            features_used=['bubble_current', 'bubble_decay_rate', 'bubble_recent_trend'],
            warnings=warnings
        )

    @staticmethod
    def create_prediction_result(
        prediction: float,
        model_tier: ModelTier,
        features: Dict[str, float],
        model_variance: float = 0.0,
        selector: Optional[ModelSelector] = None
    ) -> PredictionResult:
        """
        Create a complete PredictionResult with uncertainty quantification.

        Args:
            prediction: Raw prediction value
            model_tier: Model tier used
            features: Features used
            model_variance: Model uncertainty (if available)
            selector: ModelSelector instance for calculations

        Returns:
            Complete PredictionResult
        """
        if selector is None:
            selector = ModelSelector()

        # Calculate confidence
        confidence = selector.calculate_confidence(model_tier, features, model_variance)

        # Calculate uncertainty bounds
        lower, upper = selector.calculate_uncertainty_bounds(prediction, confidence, model_tier)

        # Extract feature names used
        features_used = list(features.keys())

        # Get warnings from data quality assessment
        warnings = []
        selector._assess_data_quality(features, warnings)

        return PredictionResult(
            value=prediction,
            confidence=confidence,
            uncertainty_lower=lower,
            uncertainty_upper=upper,
            model_tier=model_tier,
            features_used=features_used,
            warnings=warnings
        )
