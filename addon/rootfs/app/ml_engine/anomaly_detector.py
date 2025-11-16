"""
Fermentation Anomaly Detection

Detects various anomalies in fermentation process:
- Stuck fermentation (flat bubble rate, flat gravity)
- Too fast fermentation (excessive bubble rate, temp spike)
- Temperature anomalies (too hot, too cold, unstable)
- pH anomalies (infection, bacterial contamination)
- Statistical outliers (isolation forest)
- Pattern-based anomalies (unusual trends)

Provides severity scores and actionable recommendations.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from sklearn.ensemble import IsolationForest
from scipy import stats

from .feature_engineering import FeatureEngineer


class AnomalySeverity(Enum):
    """Anomaly severity levels."""
    NORMAL = "normal"           # No anomaly
    INFO = "info"               # Informational, no action needed
    WARNING = "warning"         # Potential issue, monitor closely
    CRITICAL = "critical"       # Serious issue, action required


class AnomalyType(Enum):
    """Types of fermentation anomalies."""
    STUCK_FERMENTATION = "stuck_fermentation"
    FAST_FERMENTATION = "fast_fermentation"
    TEMPERATURE_HIGH = "temperature_high"
    TEMPERATURE_LOW = "temperature_low"
    TEMPERATURE_UNSTABLE = "temperature_unstable"
    PH_LOW = "ph_low"
    PH_HIGH = "ph_high"
    PH_RAPID_CHANGE = "ph_rapid_change"
    BUBBLE_RATE_SPIKE = "bubble_rate_spike"
    BUBBLE_RATE_FLATLINE = "bubble_rate_flatline"
    GRAVITY_FLATLINE = "gravity_flatline"
    GRAVITY_INCREASE = "gravity_increase"
    STATISTICAL_OUTLIER = "statistical_outlier"
    UNUSUAL_PATTERN = "unusual_pattern"


@dataclass
class Anomaly:
    """
    Container for detected anomaly.

    Attributes:
        anomaly_type: Type of anomaly detected
        severity: Severity level
        score: Anomaly score (0-1, higher = more anomalous)
        description: Human-readable description
        recommendation: Suggested action
        affected_sensors: List of sensors showing the anomaly
        timestamp: When anomaly was detected (hours since start)
    """
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    score: float
    description: str
    recommendation: str
    affected_sensors: List[str]
    timestamp: float

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'type': self.anomaly_type.value,
            'severity': self.severity.value,
            'score': self.score,
            'description': self.description,
            'recommendation': self.recommendation,
            'affected_sensors': self.affected_sensors,
            'timestamp': self.timestamp
        }


class AnomalyDetector:
    """
    Detects fermentation anomalies using multiple detection strategies.

    Detection methods:
    1. Rule-based detection (domain knowledge)
    2. Statistical outlier detection (Isolation Forest)
    3. Pattern-based detection (trend analysis)
    4. Multi-variate correlation analysis
    """

    def __init__(
        self,
        stuck_threshold_hours: int = 24,
        temp_min: float = 12.0,
        temp_max: float = 28.0,
        ph_min: float = 2.8,
        ph_max: float = 4.2
    ):
        """
        Initialize anomaly detector.

        Args:
            stuck_threshold_hours: Hours of no change before flagging stuck fermentation
            temp_min: Minimum safe temperature (°C)
            temp_max: Maximum safe temperature (°C)
            ph_min: Minimum safe pH
            ph_max: Maximum safe pH
        """
        self.stuck_threshold_hours = stuck_threshold_hours
        self.temp_min = temp_min
        self.temp_max = temp_max
        self.ph_min = ph_min
        self.ph_max = ph_max
        self.feature_engineer = FeatureEngineer()

        # Isolation Forest for statistical outlier detection
        self.outlier_detector = IsolationForest(
            contamination=0.1,  # Expect 10% outliers
            random_state=42,
            n_estimators=100
        )
        self.outlier_fitted = False

    def detect_anomalies(
        self,
        timestamps: np.ndarray,
        bubble_counts: Optional[np.ndarray] = None,
        gravity: Optional[np.ndarray] = None,
        temperature: Optional[np.ndarray] = None,
        ph: Optional[np.ndarray] = None
    ) -> List[Anomaly]:
        """
        Detect all anomalies in fermentation data.

        Args:
            timestamps: Array of timestamps
            bubble_counts: Bubble count rates
            gravity: Specific gravity readings
            temperature: Temperature readings
            ph: pH readings

        Returns:
            List of detected anomalies, sorted by severity
        """
        anomalies = []

        # Extract features
        features = self.feature_engineer.extract_all_features(
            timestamps=timestamps,
            bubble_counts=bubble_counts,
            gravity=gravity,
            temperature=temperature,
            ph=ph
        )

        time_hours = self.feature_engineer._normalize_timestamps(timestamps)
        current_time = time_hours[-1] if len(time_hours) > 0 else 0

        # Rule-based detections
        if bubble_counts is not None:
            anomalies.extend(self._detect_bubble_anomalies(
                time_hours, bubble_counts, features, current_time
            ))

        if gravity is not None:
            anomalies.extend(self._detect_gravity_anomalies(
                time_hours, gravity, features, current_time
            ))

        if temperature is not None:
            anomalies.extend(self._detect_temperature_anomalies(
                time_hours, temperature, features, current_time
            ))

        if ph is not None:
            anomalies.extend(self._detect_ph_anomalies(
                time_hours, ph, features, current_time
            ))

        # Cross-sensor anomalies
        if bubble_counts is not None and gravity is not None:
            anomalies.extend(self._detect_stuck_fermentation(
                time_hours, bubble_counts, gravity, features, current_time
            ))

        # Statistical outlier detection
        if len(time_hours) > 10:
            anomalies.extend(self._detect_statistical_outliers(
                features, current_time
            ))

        # Sort by severity (critical first)
        severity_order = {
            AnomalySeverity.CRITICAL: 0,
            AnomalySeverity.WARNING: 1,
            AnomalySeverity.INFO: 2,
            AnomalySeverity.NORMAL: 3
        }
        anomalies.sort(key=lambda a: (severity_order[a.severity], -a.score))

        return anomalies

    def _detect_bubble_anomalies(
        self,
        time_hours: np.ndarray,
        bubble_counts: np.ndarray,
        features: Dict[str, float],
        current_time: float
    ) -> List[Anomaly]:
        """Detect anomalies in bubble count data."""
        anomalies = []

        bubble_current = features['bubble_current']
        bubble_mean = features['bubble_mean']
        bubble_std = features['bubble_std']
        bubble_trend = features['bubble_recent_trend']

        # Bubble rate spike (sudden increase)
        if bubble_current > bubble_mean + 3 * bubble_std and bubble_current > 20:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.BUBBLE_RATE_SPIKE,
                severity=AnomalySeverity.WARNING,
                score=min(1.0, (bubble_current - bubble_mean) / (bubble_mean + 1)),
                description=f"Bubble rate spike detected: {bubble_current:.1f} bubbles/min (avg: {bubble_mean:.1f})",
                recommendation="Check for temperature spike or vigorous fermentation. Monitor closely for next 6 hours.",
                affected_sensors=['bubble_counter'],
                timestamp=current_time
            ))

        # Bubble rate flatline (no change for extended period)
        if len(time_hours) > 10:
            # Check last N hours for flatness
            window_hours = min(self.stuck_threshold_hours, current_time / 2)
            window_mask = time_hours >= (current_time - window_hours)
            recent_bubbles = bubble_counts[window_mask]

            if len(recent_bubbles) > 5:
                recent_std = np.std(recent_bubbles)
                recent_mean = np.mean(recent_bubbles)
                cv = recent_std / (recent_mean + 1e-6)

                # Very low variability AND non-zero rate
                if cv < 0.05 and recent_mean > 0.1 and window_hours >= self.stuck_threshold_hours / 2:
                    anomalies.append(Anomaly(
                        anomaly_type=AnomalyType.BUBBLE_RATE_FLATLINE,
                        severity=AnomalySeverity.WARNING,
                        score=1.0 - cv,  # Lower CV = higher score
                        description=f"Bubble rate unchanged for {window_hours:.1f} hours at {recent_mean:.1f} bubbles/min",
                        recommendation="Possible stuck fermentation. Check gravity and temperature. Consider rousing yeast gently.",
                        affected_sensors=['bubble_counter'],
                        timestamp=current_time
                    ))

        # Too fast fermentation (risky for Pet Nat)
        age_hours = features['fermentation_age_hours']
        co2_cumulative = features['co2_cumulative']

        # High CO2 production early in fermentation
        if age_hours < 48 and bubble_current > 30:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.FAST_FERMENTATION,
                severity=AnomalySeverity.WARNING,
                score=min(1.0, bubble_current / 50),
                description=f"Very fast fermentation: {bubble_current:.1f} bubbles/min at {age_hours:.1f}h",
                recommendation="Risk of over-carbonation. Monitor closely and consider earlier bottling. Check temperature.",
                affected_sensors=['bubble_counter'],
                timestamp=current_time
            ))

        return anomalies

    def _detect_gravity_anomalies(
        self,
        time_hours: np.ndarray,
        gravity: np.ndarray,
        features: Dict[str, float],
        current_time: float
    ) -> List[Anomaly]:
        """Detect anomalies in gravity data."""
        anomalies = []

        gravity_current = features['gravity_current']
        gravity_rate = features['gravity_rate']
        gravity_trend = features['gravity_recent_trend']

        # Gravity flatline (stuck fermentation indicator)
        if len(time_hours) > 10:
            window_hours = min(self.stuck_threshold_hours, current_time / 2)
            window_mask = time_hours >= (current_time - window_hours)
            recent_gravity = gravity[window_mask]

            if len(recent_gravity) > 5:
                gravity_change = recent_gravity[0] - recent_gravity[-1]
                age_hours = features['fermentation_age_hours']

                # No gravity change for extended period (and not finished)
                if abs(gravity_change) < 0.001 and gravity_current > 1.002 and window_hours >= self.stuck_threshold_hours / 2:
                    severity = AnomalySeverity.CRITICAL if window_hours >= self.stuck_threshold_hours else AnomalySeverity.WARNING

                    anomalies.append(Anomaly(
                        anomaly_type=AnomalyType.GRAVITY_FLATLINE,
                        severity=severity,
                        score=window_hours / self.stuck_threshold_hours,
                        description=f"Gravity unchanged at {gravity_current:.3f} for {window_hours:.1f} hours",
                        recommendation="Likely stuck fermentation. Check temperature, yeast health. Consider nutrient addition or re-pitch.",
                        affected_sensors=['gravity'],
                        timestamp=current_time
                    ))

        # Gravity increase (contamination or measurement error)
        if gravity_rate > 0.0001:  # Gravity increasing
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.GRAVITY_INCREASE,
                severity=AnomalySeverity.WARNING,
                score=min(1.0, gravity_rate * 1000),
                description=f"Gravity increasing: {gravity_current:.3f} (rate: +{gravity_rate:.5f}/hr)",
                recommendation="Unusual - verify iSpindel calibration. Could indicate infection producing polysaccharides.",
                affected_sensors=['gravity'],
                timestamp=current_time
            ))

        return anomalies

    def _detect_temperature_anomalies(
        self,
        time_hours: np.ndarray,
        temperature: np.ndarray,
        features: Dict[str, float],
        current_time: float
    ) -> List[Anomaly]:
        """Detect temperature-related anomalies."""
        anomalies = []

        temp_current = features['temp_current']
        temp_std = features['temp_std']
        temp_mean = features['temp_mean']

        # Temperature too high
        if temp_current > self.temp_max:
            severity = AnomalySeverity.CRITICAL if temp_current > self.temp_max + 3 else AnomalySeverity.WARNING
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.TEMPERATURE_HIGH,
                severity=severity,
                score=min(1.0, (temp_current - self.temp_max) / 10),
                description=f"Temperature too high: {temp_current:.1f}°C (max: {self.temp_max}°C)",
                recommendation="Cool fermentation immediately. Risk of stressed yeast, off-flavors, and stuck fermentation.",
                affected_sensors=['temperature'],
                timestamp=current_time
            ))

        # Temperature too low
        if temp_current < self.temp_min:
            severity = AnomalySeverity.WARNING
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.TEMPERATURE_LOW,
                severity=severity,
                score=min(1.0, (self.temp_min - temp_current) / 10),
                description=f"Temperature too low: {temp_current:.1f}°C (min: {self.temp_min}°C)",
                recommendation="Fermentation may slow or stall. Move to warmer location or use heat belt.",
                affected_sensors=['temperature'],
                timestamp=current_time
            ))

        # Temperature instability (high variance)
        if temp_std > 3.0 and features['fermentation_age_hours'] > 24:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.TEMPERATURE_UNSTABLE,
                severity=AnomalySeverity.INFO,
                score=min(1.0, temp_std / 5),
                description=f"Unstable temperature: {temp_mean:.1f}°C ±{temp_std:.1f}°C",
                recommendation="Temperature fluctuations can stress yeast. Try to maintain more stable environment.",
                affected_sensors=['temperature'],
                timestamp=current_time
            ))

        return anomalies

    def _detect_ph_anomalies(
        self,
        time_hours: np.ndarray,
        ph: np.ndarray,
        features: Dict[str, float],
        current_time: float
    ) -> List[Anomaly]:
        """Detect pH-related anomalies."""
        anomalies = []

        ph_current = features['ph_current']
        ph_delta = features['ph_delta']

        # pH too low (risk of stuck fermentation or infection)
        if ph_current < self.ph_min:
            severity = AnomalySeverity.CRITICAL if ph_current < 2.5 else AnomalySeverity.WARNING
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.PH_LOW,
                severity=severity,
                score=min(1.0, (self.ph_min - ph_current) / 1.0),
                description=f"pH very low: {ph_current:.2f} (min: {self.ph_min})",
                recommendation="Risk of stuck fermentation or bacterial infection. Monitor closely. May need pH adjustment.",
                affected_sensors=['ph'],
                timestamp=current_time
            ))

        # pH too high (unusual for wine)
        if ph_current > self.ph_max:
            severity = AnomalySeverity.WARNING
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.PH_HIGH,
                severity=severity,
                score=min(1.0, (ph_current - self.ph_max) / 1.0),
                description=f"pH high: {ph_current:.2f} (max: {self.ph_max})",
                recommendation="Unusual for wine fermentation. Verify sensor calibration. Monitor for infection.",
                affected_sensors=['ph'],
                timestamp=current_time
            ))

        # Rapid pH change
        if len(time_hours) > 10:
            ph_trend = features.get('ph_recent_trend', 0)
            age_hours = features['fermentation_age_hours']

            # pH dropping rapidly (more than 0.5 in 24h)
            if abs(ph_trend) > 0.02 and age_hours > 24:  # 0.02/hr = 0.48/day
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.PH_RAPID_CHANGE,
                    severity=AnomalySeverity.INFO,
                    score=min(1.0, abs(ph_trend) / 0.05),
                    description=f"Rapid pH change: {ph_trend:.3f} pH/hr",
                    recommendation="Monitor fermentation progress. Rapid pH changes can indicate bacterial activity.",
                    affected_sensors=['ph'],
                    timestamp=current_time
                ))

        return anomalies

    def _detect_stuck_fermentation(
        self,
        time_hours: np.ndarray,
        bubble_counts: np.ndarray,
        gravity: np.ndarray,
        features: Dict[str, float],
        current_time: float
    ) -> List[Anomaly]:
        """
        Detect stuck fermentation using multiple signals.

        Stuck fermentation indicators:
        - Flat bubble rate for extended period
        - Flat gravity for extended period
        - Both above conditions AND gravity > target
        - Low bubble-gravity correlation
        """
        anomalies = []

        # Already handled individually, but cross-check
        age_hours = features['fermentation_age_hours']
        bubble_trend = features['bubble_recent_trend']
        gravity_trend = features['gravity_recent_trend']
        gravity_current = features['gravity_current']

        # Both trends near zero, not finished, and been fermenting a while
        if (age_hours > self.stuck_threshold_hours and
            abs(bubble_trend) < 0.1 and
            abs(gravity_trend) < 0.0001 and
            gravity_current > 1.002):

            # Check if this wasn't already flagged
            existing_types = {AnomalyType.BUBBLE_RATE_FLATLINE, AnomalyType.GRAVITY_FLATLINE}
            if not any(a.anomaly_type in existing_types for a in anomalies):
                anomalies.append(Anomaly(
                    anomaly_type=AnomalyType.STUCK_FERMENTATION,
                    severity=AnomalySeverity.CRITICAL,
                    score=0.9,
                    description=f"Stuck fermentation detected: No progress for {age_hours:.1f}h at SG {gravity_current:.3f}",
                    recommendation="Fermentation has stalled. Actions: 1) Check temperature, 2) Rouse yeast gently, 3) Consider nutrient addition, 4) May need to re-pitch fresh yeast.",
                    affected_sensors=['bubble_counter', 'gravity'],
                    timestamp=current_time
                ))

        return anomalies

    def _detect_statistical_outliers(
        self,
        features: Dict[str, float],
        current_time: float
    ) -> List[Anomaly]:
        """
        Detect statistical outliers using Isolation Forest.

        Uses all available features to detect unusual patterns that
        don't fit specific rules but are statistically anomalous.
        """
        anomalies = []

        # Extract numerical features for outlier detection
        feature_vector = []
        feature_names = []

        for key, value in features.items():
            if isinstance(value, (int, float)) and not np.isnan(value) and not np.isinf(value):
                feature_vector.append(value)
                feature_names.append(key)

        if len(feature_vector) < 5:
            return anomalies  # Not enough features

        X = np.array(feature_vector).reshape(1, -1)

        # Fit and predict (in real deployment, would use historical data)
        # For now, use simple z-score method
        outlier_score = 0.0
        outlier_features = []

        for i, (name, value) in enumerate(zip(feature_names, feature_vector)):
            # Simple outlier detection based on expected ranges
            expected_ranges = {
                'bubble_current': (0, 50),
                'bubble_mean': (0, 30),
                'gravity_current': (0.990, 1.100),
                'temp_current': (5, 35),
                'ph_current': (2.5, 4.5),
                'apparent_attenuation': (0, 100),
            }

            if name in expected_ranges:
                min_val, max_val = expected_ranges[name]
                if value < min_val or value > max_val:
                    outlier_score += 0.2
                    outlier_features.append(name)

        if outlier_score > 0.3:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.STATISTICAL_OUTLIER,
                severity=AnomalySeverity.INFO,
                score=min(1.0, outlier_score),
                description=f"Statistical outliers detected in: {', '.join(outlier_features)}",
                recommendation="Some measurements are outside expected ranges. Verify sensor calibration and data quality.",
                affected_sensors=outlier_features,
                timestamp=current_time
            ))

        return anomalies

    def get_health_score(self, anomalies: List[Anomaly]) -> float:
        """
        Calculate overall fermentation health score (0-100).

        100 = Perfect, no anomalies
        75-99 = Good, minor issues
        50-74 = Fair, some concerns
        25-49 = Poor, significant issues
        0-24 = Critical, major problems

        Args:
            anomalies: List of detected anomalies

        Returns:
            Health score (0-100)
        """
        if not anomalies:
            return 100.0

        # Deduct points based on severity
        score = 100.0
        severity_penalties = {
            AnomalySeverity.INFO: 2,
            AnomalySeverity.WARNING: 10,
            AnomalySeverity.CRITICAL: 30
        }

        for anomaly in anomalies:
            penalty = severity_penalties[anomaly.severity]
            # Scale penalty by anomaly score
            score -= penalty * anomaly.score

        return max(0.0, min(100.0, score))

    def get_summary(self, anomalies: List[Anomaly]) -> Dict:
        """
        Get summary of anomaly detection results.

        Returns:
            Dictionary with summary statistics
        """
        if not anomalies:
            return {
                'health_score': 100.0,
                'status': 'healthy',
                'critical_count': 0,
                'warning_count': 0,
                'info_count': 0,
                'total_count': 0,
                'top_concerns': []
            }

        counts = {
            AnomalySeverity.CRITICAL: 0,
            AnomalySeverity.WARNING: 0,
            AnomalySeverity.INFO: 0
        }

        for anomaly in anomalies:
            counts[anomaly.severity] += 1

        health_score = self.get_health_score(anomalies)

        # Determine status
        if health_score >= 75:
            status = 'good'
        elif health_score >= 50:
            status = 'fair'
        elif health_score >= 25:
            status = 'poor'
        else:
            status = 'critical'

        # Top concerns (critical and high-score warnings)
        top_concerns = [
            {
                'type': a.anomaly_type.value,
                'description': a.description,
                'recommendation': a.recommendation
            }
            for a in anomalies
            if a.severity in [AnomalySeverity.CRITICAL, AnomalySeverity.WARNING]
        ][:3]  # Top 3

        return {
            'health_score': health_score,
            'status': status,
            'critical_count': counts[AnomalySeverity.CRITICAL],
            'warning_count': counts[AnomalySeverity.WARNING],
            'info_count': counts[AnomalySeverity.INFO],
            'total_count': len(anomalies),
            'top_concerns': top_concerns
        }
