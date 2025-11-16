"""
Feature Engineering Module for Wine Production ML

Extracts meaningful features from time-series sensor data for fermentation monitoring.
Handles variable sensor configurations and missing data gracefully.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from scipy import stats, signal
from scipy.interpolate import interp1d


class FeatureEngineer:
    """
    Extracts features from time-series fermentation data.

    Supports multiple sensor types:
    - Bubble counter (CO2 production)
    - Gravity sensor (iSpindel)
    - Temperature sensor
    - pH sensor

    Features include statistical, temporal, and domain-specific metrics.
    """

    def __init__(self, window_hours: int = 24):
        """
        Initialize feature engineer.

        Args:
            window_hours: Time window for rolling statistics (default 24h)
        """
        self.window_hours = window_hours

    def extract_all_features(
        self,
        timestamps: np.ndarray,
        bubble_counts: Optional[np.ndarray] = None,
        gravity: Optional[np.ndarray] = None,
        temperature: Optional[np.ndarray] = None,
        ph: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Extract all available features from sensor data.

        Args:
            timestamps: Array of datetime objects or unix timestamps
            bubble_counts: Bubble count rates (bubbles/minute)
            gravity: Specific gravity readings
            temperature: Temperature readings (Celsius)
            ph: pH readings

        Returns:
            Dictionary of feature names to values
        """
        features = {}

        # Convert timestamps to hours since start
        time_hours = self._normalize_timestamps(timestamps)

        # Bubble count features (core sensor)
        if bubble_counts is not None:
            features.update(self._extract_bubble_features(time_hours, bubble_counts))

        # Gravity features
        if gravity is not None:
            features.update(self._extract_gravity_features(time_hours, gravity))

        # Temperature features
        if temperature is not None:
            features.update(self._extract_temperature_features(time_hours, temperature))

        # pH features
        if ph is not None:
            features.update(self._extract_ph_features(time_hours, ph))

        # Cross-sensor features
        if bubble_counts is not None and gravity is not None:
            features.update(self._extract_bubble_gravity_correlation(
                time_hours, bubble_counts, gravity
            ))

        if bubble_counts is not None and temperature is not None:
            features.update(self._extract_bubble_temperature_correlation(
                time_hours, bubble_counts, temperature
            ))

        # Temporal features
        features.update(self._extract_temporal_features(time_hours))

        return features

    def _normalize_timestamps(self, timestamps: np.ndarray) -> np.ndarray:
        """Convert timestamps to hours since fermentation start."""
        if len(timestamps) == 0:
            return np.array([])

        # Handle datetime objects
        if isinstance(timestamps[0], (datetime, np.datetime64)):
            start_time = timestamps[0]
            hours = np.array([
                (ts - start_time).total_seconds() / 3600
                for ts in timestamps
            ])
        else:
            # Assume unix timestamps
            start_time = timestamps[0]
            hours = (timestamps - start_time) / 3600

        return hours

    def _extract_bubble_features(
        self,
        time_hours: np.ndarray,
        bubble_counts: np.ndarray
    ) -> Dict[str, float]:
        """
        Extract features from bubble count data.

        Features:
        - Current rate and recent statistics
        - Rate of change (acceleration)
        - Cumulative CO2 production
        - Exponential decay fitting
        - Peak detection
        """
        features = {}

        # Basic statistics
        features['bubble_current'] = bubble_counts[-1]
        features['bubble_mean'] = np.mean(bubble_counts)
        features['bubble_std'] = np.std(bubble_counts)
        features['bubble_max'] = np.max(bubble_counts)
        features['bubble_min'] = np.min(bubble_counts)

        # Recent window statistics (last 24h or window_hours)
        window_mask = time_hours >= (time_hours[-1] - self.window_hours)
        if np.sum(window_mask) > 1:
            recent_bubbles = bubble_counts[window_mask]
            features['bubble_recent_mean'] = np.mean(recent_bubbles)
            features['bubble_recent_std'] = np.std(recent_bubbles)
            features['bubble_recent_trend'] = self._calculate_trend(
                time_hours[window_mask], recent_bubbles
            )
        else:
            features['bubble_recent_mean'] = features['bubble_current']
            features['bubble_recent_std'] = 0.0
            features['bubble_recent_trend'] = 0.0

        # Rate of change (first derivative approximation)
        if len(bubble_counts) > 2:
            bubble_gradient = np.gradient(bubble_counts, time_hours)
            features['bubble_rate_change'] = bubble_gradient[-1]
            features['bubble_acceleration'] = np.gradient(bubble_gradient, time_hours)[-1]
        else:
            features['bubble_rate_change'] = 0.0
            features['bubble_acceleration'] = 0.0

        # Cumulative CO2 production (integral of bubble rate)
        features['co2_cumulative'] = np.trapz(bubble_counts, time_hours)

        # Exponential decay fitting (Pet Nat characteristic)
        if len(bubble_counts) > 5:
            decay_params = self._fit_exponential_decay(time_hours, bubble_counts)
            features['bubble_decay_rate'] = decay_params['decay_rate']
            features['bubble_decay_r2'] = decay_params['r2']
            features['bubble_time_to_threshold'] = self._estimate_time_to_threshold(
                bubble_counts[-1], decay_params, threshold=1.0
            )
        else:
            features['bubble_decay_rate'] = 0.0
            features['bubble_decay_r2'] = 0.0
            features['bubble_time_to_threshold'] = 999.0

        # Peak detection
        if len(bubble_counts) > 10:
            peaks, _ = signal.find_peaks(bubble_counts, prominence=0.5)
            features['bubble_peak_count'] = len(peaks)
            features['bubble_time_since_peak'] = time_hours[-1] - time_hours[peaks[-1]] if len(peaks) > 0 else 999.0
        else:
            features['bubble_peak_count'] = 0
            features['bubble_time_since_peak'] = 0.0

        # Coefficient of variation (volatility)
        features['bubble_cv'] = features['bubble_std'] / (features['bubble_mean'] + 1e-6)

        return features

    def _extract_gravity_features(
        self,
        time_hours: np.ndarray,
        gravity: np.ndarray
    ) -> Dict[str, float]:
        """
        Extract features from gravity (specific gravity) data.

        Features:
        - Current gravity and statistics
        - Attenuation metrics
        - Polynomial curve fitting
        - Predicted final gravity
        """
        features = {}

        # Basic statistics
        features['gravity_current'] = gravity[-1]
        features['gravity_start'] = gravity[0]
        features['gravity_min'] = np.min(gravity)
        features['gravity_delta'] = gravity[0] - gravity[-1]

        # Attenuation (fermentation progress)
        # Apparent attenuation = (OG - CG) / (OG - 1.000) * 100
        og = gravity[0]
        cg = gravity[-1]
        features['apparent_attenuation'] = ((og - cg) / (og - 1.000)) * 100 if og > 1.000 else 0.0

        # Rate of gravity drop
        if len(gravity) > 2:
            gravity_gradient = np.gradient(gravity, time_hours)
            features['gravity_rate'] = gravity_gradient[-1]
            features['gravity_acceleration'] = np.gradient(gravity_gradient, time_hours)[-1]
        else:
            features['gravity_rate'] = 0.0
            features['gravity_acceleration'] = 0.0

        # Recent window statistics
        window_mask = time_hours >= (time_hours[-1] - self.window_hours)
        if np.sum(window_mask) > 1:
            recent_gravity = gravity[window_mask]
            features['gravity_recent_mean'] = np.mean(recent_gravity)
            features['gravity_recent_std'] = np.std(recent_gravity)
            features['gravity_recent_trend'] = self._calculate_trend(
                time_hours[window_mask], recent_gravity
            )
        else:
            features['gravity_recent_mean'] = features['gravity_current']
            features['gravity_recent_std'] = 0.0
            features['gravity_recent_trend'] = 0.0

        # Polynomial fitting for prediction
        if len(gravity) > 5:
            poly_params = self._fit_polynomial(time_hours, gravity, degree=2)
            features['gravity_poly_r2'] = poly_params['r2']
            # Predict gravity in 24h
            predicted_gravity = np.polyval(poly_params['coeffs'], time_hours[-1] + 24)
            features['gravity_predicted_24h'] = max(1.000, predicted_gravity)
        else:
            features['gravity_poly_r2'] = 0.0
            features['gravity_predicted_24h'] = gravity[-1]

        # Estimate time to target gravity (e.g., 1.002 for Pet Nat)
        if features['gravity_rate'] < -0.001:  # Still dropping
            hours_to_target = (gravity[-1] - 1.002) / abs(features['gravity_rate'])
            features['hours_to_target_gravity'] = max(0, hours_to_target)
        else:
            features['hours_to_target_gravity'] = 999.0

        return features

    def _extract_temperature_features(
        self,
        time_hours: np.ndarray,
        temperature: np.ndarray
    ) -> Dict[str, float]:
        """Extract features from temperature data."""
        features = {}

        features['temp_current'] = temperature[-1]
        features['temp_mean'] = np.mean(temperature)
        features['temp_std'] = np.std(temperature)
        features['temp_max'] = np.max(temperature)
        features['temp_min'] = np.min(temperature)
        features['temp_range'] = features['temp_max'] - features['temp_min']

        # Recent trend
        window_mask = time_hours >= (time_hours[-1] - self.window_hours)
        if np.sum(window_mask) > 1:
            recent_temp = temperature[window_mask]
            features['temp_recent_mean'] = np.mean(recent_temp)
            features['temp_recent_std'] = np.std(recent_temp)
            features['temp_recent_trend'] = self._calculate_trend(
                time_hours[window_mask], recent_temp
            )
        else:
            features['temp_recent_mean'] = features['temp_current']
            features['temp_recent_std'] = 0.0
            features['temp_recent_trend'] = 0.0

        # Temperature variability (important for fermentation control)
        features['temp_cv'] = features['temp_std'] / (features['temp_mean'] + 1e-6)

        return features

    def _extract_ph_features(
        self,
        time_hours: np.ndarray,
        ph: np.ndarray
    ) -> Dict[str, float]:
        """Extract features from pH data."""
        features = {}

        features['ph_current'] = ph[-1]
        features['ph_start'] = ph[0]
        features['ph_delta'] = ph[0] - ph[-1]
        features['ph_mean'] = np.mean(ph)
        features['ph_std'] = np.std(ph)

        # Recent trend
        window_mask = time_hours >= (time_hours[-1] - self.window_hours)
        if np.sum(window_mask) > 1:
            recent_ph = ph[window_mask]
            features['ph_recent_trend'] = self._calculate_trend(
                time_hours[window_mask], recent_ph
            )
        else:
            features['ph_recent_trend'] = 0.0

        return features

    def _extract_bubble_gravity_correlation(
        self,
        time_hours: np.ndarray,
        bubble_counts: np.ndarray,
        gravity: np.ndarray
    ) -> Dict[str, float]:
        """Extract correlation features between bubble rate and gravity."""
        features = {}

        # Correlation coefficient
        if len(bubble_counts) > 2 and len(gravity) > 2:
            # Ensure same length by interpolation if needed
            if len(bubble_counts) != len(gravity):
                # Interpolate to common time grid
                common_time = np.linspace(
                    time_hours[0], time_hours[-1],
                    min(len(bubble_counts), len(gravity))
                )
                bubble_interp = np.interp(common_time, time_hours, bubble_counts)
                gravity_interp = np.interp(common_time, time_hours, gravity)
            else:
                bubble_interp = bubble_counts
                gravity_interp = gravity

            corr, _ = stats.pearsonr(bubble_interp, gravity_interp)
            features['bubble_gravity_correlation'] = corr if not np.isnan(corr) else 0.0

            # CO2 production per gravity point
            gravity_delta = gravity[0] - gravity[-1]
            co2_total = np.trapz(bubble_counts, time_hours)
            features['co2_per_gravity_point'] = co2_total / (gravity_delta + 1e-6)
        else:
            features['bubble_gravity_correlation'] = 0.0
            features['co2_per_gravity_point'] = 0.0

        return features

    def _extract_bubble_temperature_correlation(
        self,
        time_hours: np.ndarray,
        bubble_counts: np.ndarray,
        temperature: np.ndarray
    ) -> Dict[str, float]:
        """Extract correlation features between bubble rate and temperature."""
        features = {}

        if len(bubble_counts) > 2 and len(temperature) > 2:
            # Temperature-compensated bubble rate
            # Assumption: fermentation rate doubles per 10°C (Q10 = 2)
            ref_temp = 20.0  # Reference temperature
            temp_factor = 2.0 ** ((temperature - ref_temp) / 10.0)
            bubble_compensated = bubble_counts / temp_factor

            features['bubble_temp_compensated'] = bubble_compensated[-1]
            features['bubble_temp_compensation_factor'] = temp_factor[-1]

            # Correlation
            if len(bubble_counts) != len(temperature):
                common_time = np.linspace(
                    time_hours[0], time_hours[-1],
                    min(len(bubble_counts), len(temperature))
                )
                bubble_interp = np.interp(common_time, time_hours, bubble_counts)
                temp_interp = np.interp(common_time, time_hours, temperature)
            else:
                bubble_interp = bubble_counts
                temp_interp = temperature

            corr, _ = stats.pearsonr(bubble_interp, temp_interp)
            features['bubble_temp_correlation'] = corr if not np.isnan(corr) else 0.0
        else:
            features['bubble_temp_compensated'] = bubble_counts[-1] if len(bubble_counts) > 0 else 0.0
            features['bubble_temp_compensation_factor'] = 1.0
            features['bubble_temp_correlation'] = 0.0

        return features

    def _extract_temporal_features(self, time_hours: np.ndarray) -> Dict[str, float]:
        """Extract time-based features."""
        features = {}

        features['fermentation_age_hours'] = time_hours[-1]
        features['fermentation_age_days'] = time_hours[-1] / 24.0
        features['measurement_count'] = len(time_hours)

        # Measurement frequency
        if len(time_hours) > 1:
            time_diffs = np.diff(time_hours)
            features['measurement_interval_mean'] = np.mean(time_diffs)
            features['measurement_interval_std'] = np.std(time_diffs)
        else:
            features['measurement_interval_mean'] = 0.0
            features['measurement_interval_std'] = 0.0

        return features

    def _calculate_trend(self, x: np.ndarray, y: np.ndarray) -> float:
        """Calculate linear trend (slope) of data."""
        if len(x) < 2:
            return 0.0
        slope, _, _, _, _ = stats.linregress(x, y)
        return slope

    def _fit_exponential_decay(
        self,
        time_hours: np.ndarray,
        values: np.ndarray
    ) -> Dict[str, float]:
        """
        Fit exponential decay model: y = a * exp(-b * t) + c

        Returns:
            Dictionary with 'decay_rate' (b), 'r2', and coefficients
        """
        try:
            # Log transform for linear regression (simplified fitting)
            # y = a * exp(-b * t) => ln(y) = ln(a) - b * t

            # Handle zeros and negatives
            values_positive = np.maximum(values, 1e-6)
            log_values = np.log(values_positive)

            # Linear regression on log-transformed data
            slope, intercept, r_value, _, _ = stats.linregress(time_hours, log_values)

            return {
                'decay_rate': -slope,  # b (positive value)
                'amplitude': np.exp(intercept),  # a
                'r2': r_value ** 2
            }
        except Exception:
            return {
                'decay_rate': 0.0,
                'amplitude': 0.0,
                'r2': 0.0
            }

    def _estimate_time_to_threshold(
        self,
        current_value: float,
        decay_params: Dict[str, float],
        threshold: float
    ) -> float:
        """
        Estimate hours until value reaches threshold using exponential decay model.

        y(t) = a * exp(-b * t)
        threshold = current_value * exp(-b * delta_t)
        delta_t = -ln(threshold / current_value) / b
        """
        try:
            b = decay_params['decay_rate']
            if b <= 0 or current_value <= threshold:
                return 999.0

            delta_t = -np.log(threshold / current_value) / b
            return max(0.0, delta_t)
        except Exception:
            return 999.0

    def _fit_polynomial(
        self,
        x: np.ndarray,
        y: np.ndarray,
        degree: int = 2
    ) -> Dict[str, any]:
        """Fit polynomial and return coefficients and R²."""
        try:
            coeffs = np.polyfit(x, y, degree)
            y_pred = np.polyval(coeffs, x)

            # Calculate R²
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r2 = 1 - (ss_res / (ss_tot + 1e-6))

            return {
                'coeffs': coeffs,
                'r2': r2
            }
        except Exception:
            return {
                'coeffs': np.zeros(degree + 1),
                'r2': 0.0
            }
