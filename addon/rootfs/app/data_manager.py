"""
Data Manager

Time-series data storage and management using SQLite.
Handles sensor data persistence, aggregation, and retrieval for ML models.
"""

import sqlite3
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import threading
from contextlib import contextmanager


class DataManager:
    """
    Manages persistent storage of sensor data using SQLite.

    Features:
    - Time-series data storage with proper indexing
    - Data aggregation and preprocessing
    - Batch retrieval for ML models
    - Data retention policies
    - Export functionality
    - Thread-safe operations
    """

    # Default retention periods
    DEFAULT_RAW_RETENTION_DAYS = 90
    DEFAULT_AGGREGATED_RETENTION_DAYS = 365

    def __init__(self, db_path: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize data manager.

        Args:
            db_path: Path to SQLite database file
            config: Optional configuration dictionary
        """
        self.db_path = db_path
        self.config = config or {}
        self.logger = logging.getLogger("data_manager")

        # Thread safety
        self._lock = threading.RLock()

        # Retention settings
        self.raw_retention_days = config.get('raw_retention_days', self.DEFAULT_RAW_RETENTION_DAYS)
        self.aggregated_retention_days = config.get('aggregated_retention_days', self.DEFAULT_AGGREGATED_RETENTION_DAYS)

        # Auto-aggregation settings
        self.auto_aggregate = config.get('auto_aggregate', True)
        self.aggregation_interval_minutes = config.get('aggregation_interval_minutes', 60)

        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        self.logger.info(f"Initialized DataManager with database: {db_path}")

    @contextmanager
    def _get_connection(self):
        """
        Get a thread-safe database connection.

        Yields:
            sqlite3.Connection
        """
        with self._lock:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            try:
                yield conn
            finally:
                conn.close()

    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Sensor data table (raw measurements)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sensor_id TEXT NOT NULL,
                    sensor_type TEXT NOT NULL,
                    measurements TEXT NOT NULL,
                    metadata TEXT,
                    data_quality TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Indexes for efficient queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sensor_data_timestamp
                ON sensor_data(timestamp)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sensor_data_sensor_id
                ON sensor_data(sensor_id, timestamp)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_sensor_data_sensor_type
                ON sensor_data(sensor_type, timestamp)
            ''')

            # Aggregated data table (hourly/daily summaries)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS aggregated_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    period_type TEXT NOT NULL,
                    sensor_id TEXT NOT NULL,
                    sensor_type TEXT NOT NULL,
                    measurement_name TEXT NOT NULL,
                    count INTEGER,
                    min_value REAL,
                    max_value REAL,
                    avg_value REAL,
                    sum_value REAL,
                    stddev_value REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_aggregated_data_period
                ON aggregated_data(period_start, period_type, sensor_id, measurement_name)
            ''')

            # Predictions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    prediction_type TEXT NOT NULL,
                    predicted_value REAL,
                    confidence REAL,
                    model_version TEXT,
                    input_data TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_predictions_timestamp
                ON predictions(timestamp, prediction_type)
            ''')

            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    sensor_id TEXT,
                    message TEXT NOT NULL,
                    details TEXT,
                    acknowledged INTEGER DEFAULT 0,
                    acknowledged_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alerts_timestamp
                ON alerts(timestamp)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged
                ON alerts(acknowledged, timestamp)
            ''')

            # Events table (fermentation stages, user actions, etc.)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    description TEXT,
                    data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_timestamp
                ON events(timestamp, event_type)
            ''')

            conn.commit()
            self.logger.info("Database schema initialized")

    def store_sensor_data(self, data: Dict[str, Any]) -> bool:
        """
        Store sensor data.

        Args:
            data: Sensor data dictionary from sensor.process_message()

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO sensor_data (
                        timestamp, sensor_id, sensor_type, measurements, metadata, data_quality
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('timestamp'),
                    data.get('sensor_id'),
                    data.get('sensor_type'),
                    json.dumps(data.get('measurements', {})),
                    json.dumps(data.get('metadata', {})),
                    data.get('data_quality'),
                ))

                conn.commit()
                return True

        except Exception as e:
            self.logger.error(f"Error storing sensor data: {e}", exc_info=True)
            return False

    def get_sensor_data(
        self,
        sensor_id: Optional[str] = None,
        sensor_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        quality_filter: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve sensor data.

        Args:
            sensor_id: Filter by sensor ID
            sensor_type: Filter by sensor type
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of records
            quality_filter: Filter by data quality levels

        Returns:
            List of sensor data dictionaries
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Build query
                query = 'SELECT * FROM sensor_data WHERE 1=1'
                params = []

                if sensor_id:
                    query += ' AND sensor_id = ?'
                    params.append(sensor_id)

                if sensor_type:
                    query += ' AND sensor_type = ?'
                    params.append(sensor_type)

                if start_time:
                    query += ' AND timestamp >= ?'
                    params.append(start_time.isoformat())

                if end_time:
                    query += ' AND timestamp <= ?'
                    params.append(end_time.isoformat())

                if quality_filter:
                    placeholders = ','.join('?' * len(quality_filter))
                    query += f' AND data_quality IN ({placeholders})'
                    params.extend(quality_filter)

                query += ' ORDER BY timestamp DESC'

                if limit:
                    query += ' LIMIT ?'
                    params.append(limit)

                cursor.execute(query, params)
                rows = cursor.fetchall()

                # Convert to dictionaries
                results = []
                for row in rows:
                    results.append({
                        'id': row['id'],
                        'timestamp': row['timestamp'],
                        'sensor_id': row['sensor_id'],
                        'sensor_type': row['sensor_type'],
                        'measurements': json.loads(row['measurements']),
                        'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                        'data_quality': row['data_quality'],
                        'created_at': row['created_at'],
                    })

                return results

        except Exception as e:
            self.logger.error(f"Error retrieving sensor data: {e}", exc_info=True)
            return []

    def get_latest_value(self, sensor_id: str, measurement_name: str) -> Optional[Tuple[datetime, float]]:
        """
        Get latest value for a specific measurement.

        Args:
            sensor_id: Sensor identifier
            measurement_name: Name of measurement

        Returns:
            Tuple of (timestamp, value) or None
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT timestamp, measurements
                    FROM sensor_data
                    WHERE sensor_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                ''', (sensor_id,))

                row = cursor.fetchone()
                if not row:
                    return None

                measurements = json.loads(row['measurements'])
                if measurement_name not in measurements:
                    return None

                timestamp = datetime.fromisoformat(row['timestamp'])
                value = measurements[measurement_name]

                return timestamp, float(value)

        except Exception as e:
            self.logger.error(f"Error getting latest value: {e}", exc_info=True)
            return None

    def get_time_series(
        self,
        sensor_id: str,
        measurement_name: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
    ) -> List[Tuple[datetime, float]]:
        """
        Get time series data for a specific measurement.

        Args:
            sensor_id: Sensor identifier
            measurement_name: Name of measurement
            start_time: Start of time range
            end_time: End of time range (default: now)

        Returns:
            List of (timestamp, value) tuples
        """
        if end_time is None:
            end_time = datetime.now()

        data = self.get_sensor_data(
            sensor_id=sensor_id,
            start_time=start_time,
            end_time=end_time,
        )

        time_series = []
        for record in data:
            measurements = record['measurements']
            if measurement_name in measurements:
                timestamp = datetime.fromisoformat(record['timestamp'])
                value = float(measurements[measurement_name])
                time_series.append((timestamp, value))

        # Sort by timestamp (ascending)
        time_series.sort(key=lambda x: x[0])

        return time_series

    def aggregate_data(
        self,
        start_time: datetime,
        end_time: datetime,
        period_type: str = 'hourly',
    ) -> bool:
        """
        Aggregate raw sensor data into summaries.

        Args:
            start_time: Start of aggregation period
            end_time: End of aggregation period
            period_type: Type of aggregation ('hourly' or 'daily')

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get all sensor/measurement combinations
                cursor.execute('''
                    SELECT DISTINCT sensor_id, sensor_type
                    FROM sensor_data
                    WHERE timestamp >= ? AND timestamp < ?
                ''', (start_time.isoformat(), end_time.isoformat()))

                sensors = cursor.fetchall()

                for sensor in sensors:
                    sensor_id = sensor['sensor_id']
                    sensor_type = sensor['sensor_type']

                    # Get all measurements for this sensor
                    cursor.execute('''
                        SELECT measurements
                        FROM sensor_data
                        WHERE sensor_id = ? AND timestamp >= ? AND timestamp < ?
                        LIMIT 1
                    ''', (sensor_id, start_time.isoformat(), end_time.isoformat()))

                    row = cursor.fetchone()
                    if not row:
                        continue

                    measurements = json.loads(row['measurements'])

                    # Aggregate each measurement
                    for measurement_name in measurements.keys():
                        self._aggregate_measurement(
                            conn,
                            sensor_id,
                            sensor_type,
                            measurement_name,
                            start_time,
                            end_time,
                            period_type,
                        )

                conn.commit()
                self.logger.info(f"Aggregated data from {start_time} to {end_time} ({period_type})")
                return True

        except Exception as e:
            self.logger.error(f"Error aggregating data: {e}", exc_info=True)
            return False

    def _aggregate_measurement(
        self,
        conn: sqlite3.Connection,
        sensor_id: str,
        sensor_type: str,
        measurement_name: str,
        start_time: datetime,
        end_time: datetime,
        period_type: str,
    ):
        """Aggregate a single measurement."""
        cursor = conn.cursor()

        # Extract values
        cursor.execute('''
            SELECT measurements
            FROM sensor_data
            WHERE sensor_id = ? AND timestamp >= ? AND timestamp < ?
        ''', (sensor_id, start_time.isoformat(), end_time.isoformat()))

        values = []
        for row in cursor.fetchall():
            measurements = json.loads(row['measurements'])
            if measurement_name in measurements:
                try:
                    values.append(float(measurements[measurement_name]))
                except (ValueError, TypeError):
                    pass

        if not values:
            return

        # Calculate statistics
        count = len(values)
        min_val = min(values)
        max_val = max(values)
        avg_val = sum(values) / count
        sum_val = sum(values)

        # Calculate standard deviation
        if count > 1:
            variance = sum((x - avg_val) ** 2 for x in values) / (count - 1)
            stddev_val = variance ** 0.5
        else:
            stddev_val = 0.0

        # Check if record already exists
        cursor.execute('''
            SELECT id FROM aggregated_data
            WHERE period_start = ? AND period_type = ? AND sensor_id = ? AND measurement_name = ?
        ''', (start_time.isoformat(), period_type, sensor_id, measurement_name))

        existing = cursor.fetchone()

        if existing:
            # Update existing record
            cursor.execute('''
                UPDATE aggregated_data
                SET count = ?, min_value = ?, max_value = ?, avg_value = ?, sum_value = ?, stddev_value = ?
                WHERE id = ?
            ''', (count, min_val, max_val, avg_val, sum_val, stddev_val, existing['id']))
        else:
            # Insert new record
            cursor.execute('''
                INSERT INTO aggregated_data (
                    period_start, period_end, period_type, sensor_id, sensor_type,
                    measurement_name, count, min_value, max_value, avg_value, sum_value, stddev_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                start_time.isoformat(),
                end_time.isoformat(),
                period_type,
                sensor_id,
                sensor_type,
                measurement_name,
                count,
                min_val,
                max_val,
                avg_val,
                sum_val,
                stddev_val,
            ))

    def get_aggregated_data(
        self,
        sensor_id: str,
        measurement_name: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        period_type: str = 'hourly',
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated data.

        Args:
            sensor_id: Sensor identifier
            measurement_name: Name of measurement
            start_time: Start of time range
            end_time: End of time range (default: now)
            period_type: Type of aggregation

        Returns:
            List of aggregated data records
        """
        if end_time is None:
            end_time = datetime.now()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM aggregated_data
                    WHERE sensor_id = ? AND measurement_name = ? AND period_type = ?
                    AND period_start >= ? AND period_start < ?
                    ORDER BY period_start
                ''', (sensor_id, measurement_name, period_type, start_time.isoformat(), end_time.isoformat()))

                rows = cursor.fetchall()

                results = []
                for row in rows:
                    results.append({
                        'period_start': row['period_start'],
                        'period_end': row['period_end'],
                        'period_type': row['period_type'],
                        'count': row['count'],
                        'min': row['min_value'],
                        'max': row['max_value'],
                        'avg': row['avg_value'],
                        'sum': row['sum_value'],
                        'stddev': row['stddev_value'],
                    })

                return results

        except Exception as e:
            self.logger.error(f"Error getting aggregated data: {e}", exc_info=True)
            return []

    def store_prediction(self, prediction: Dict[str, Any]) -> bool:
        """
        Store ML model prediction.

        Args:
            prediction: Prediction dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO predictions (
                        timestamp, prediction_type, predicted_value, confidence,
                        model_version, input_data, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    prediction.get('timestamp', datetime.now().isoformat()),
                    prediction.get('prediction_type'),
                    prediction.get('predicted_value'),
                    prediction.get('confidence'),
                    prediction.get('model_version'),
                    json.dumps(prediction.get('input_data', {})),
                    json.dumps(prediction.get('metadata', {})),
                ))

                conn.commit()
                return True

        except Exception as e:
            self.logger.error(f"Error storing prediction: {e}", exc_info=True)
            return False

    def store_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Store alert.

        Args:
            alert: Alert dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO alerts (
                        timestamp, alert_type, severity, sensor_id, message, details
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    alert.get('timestamp', datetime.now().isoformat()),
                    alert.get('alert_type'),
                    alert.get('severity'),
                    alert.get('sensor_id'),
                    alert.get('message'),
                    json.dumps(alert.get('details', {})),
                ))

                conn.commit()
                return True

        except Exception as e:
            self.logger.error(f"Error storing alert: {e}", exc_info=True)
            return False

    def cleanup_old_data(self):
        """Clean up old data based on retention policies."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Clean up raw data
                raw_cutoff = datetime.now() - timedelta(days=self.raw_retention_days)
                cursor.execute('''
                    DELETE FROM sensor_data
                    WHERE timestamp < ?
                ''', (raw_cutoff.isoformat(),))

                raw_deleted = cursor.rowcount

                # Clean up aggregated data
                agg_cutoff = datetime.now() - timedelta(days=self.aggregated_retention_days)
                cursor.execute('''
                    DELETE FROM aggregated_data
                    WHERE period_start < ?
                ''', (agg_cutoff.isoformat(),))

                agg_deleted = cursor.rowcount

                conn.commit()

                if raw_deleted > 0 or agg_deleted > 0:
                    self.logger.info(f"Cleaned up {raw_deleted} raw records and {agg_deleted} aggregated records")

        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}", exc_info=True)

    def export_data(
        self,
        output_path: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        format: str = 'json',
    ) -> bool:
        """
        Export data to file.

        Args:
            output_path: Path to output file
            start_time: Start of time range
            end_time: End of time range
            format: Export format ('json' or 'csv')

        Returns:
            True if successful, False otherwise
        """
        try:
            data = self.get_sensor_data(start_time=start_time, end_time=end_time)

            if format == 'json':
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2)
            elif format == 'csv':
                import csv
                with open(output_path, 'w', newline='') as f:
                    if data:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())
                        writer.writeheader()
                        writer.writerows(data)
            else:
                raise ValueError(f"Unsupported export format: {format}")

            self.logger.info(f"Exported {len(data)} records to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting data: {e}", exc_info=True)
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with statistics
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                stats = {}

                # Count records
                cursor.execute('SELECT COUNT(*) as count FROM sensor_data')
                stats['total_sensor_records'] = cursor.fetchone()['count']

                cursor.execute('SELECT COUNT(*) as count FROM aggregated_data')
                stats['total_aggregated_records'] = cursor.fetchone()['count']

                cursor.execute('SELECT COUNT(*) as count FROM predictions')
                stats['total_predictions'] = cursor.fetchone()['count']

                cursor.execute('SELECT COUNT(*) as count FROM alerts')
                stats['total_alerts'] = cursor.fetchone()['count']

                # Get date ranges
                cursor.execute('SELECT MIN(timestamp) as first, MAX(timestamp) as last FROM sensor_data')
                row = cursor.fetchone()
                stats['data_start'] = row['first']
                stats['data_end'] = row['last']

                # Get database size
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                stats['database_size_bytes'] = cursor.fetchone()['size']

                return stats

        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}", exc_info=True)
            return {}
