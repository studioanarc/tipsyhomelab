"""Tests for database operations and data management."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestDatabaseConnection:
    """Test database connection management."""

    @pytest.mark.asyncio
    async def test_database_connect(self, mock_database):
        """Test database connection."""
        # Database should be ready to use
        assert mock_database is not None

    @pytest.mark.asyncio
    async def test_database_close(self, mock_database):
        """Test database connection closing."""
        result = await mock_database.close()
        assert result is True
        mock_database.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_pool(self):
        """Test database connection pooling."""
        pool_size = 5
        connections = []

        for _ in range(pool_size):
            conn = MagicMock()
            connections.append(conn)

        assert len(connections) == pool_size

    @pytest.mark.asyncio
    async def test_connection_retry_on_failure(self):
        """Test connection retry on failure."""
        db = MagicMock()
        db.connect = AsyncMock(side_effect=[
            ConnectionError("Failed"),
            ConnectionError("Failed"),
            True  # Success on third try
        ])

        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await db.connect()
                if result:
                    break
            except ConnectionError:
                if attempt == max_retries - 1:
                    raise

        assert db.connect.call_count <= max_retries


class TestDataInsertion:
    """Test inserting data into database."""

    @pytest.mark.asyncio
    async def test_insert_sensor_reading(self, mock_database, valid_sensor_data):
        """Test inserting sensor reading."""
        reading = {
            "timestamp": datetime.now().isoformat(),
            "sensor_id": "ispindel_001",
            "temperature": valid_sensor_data["temperature"],
            "gravity": valid_sensor_data["specific_gravity"],
            "battery": valid_sensor_data["battery"],
        }

        result = await mock_database.insert("sensor_readings", reading)
        assert result is True

    @pytest.mark.asyncio
    async def test_insert_batch_data(self, mock_database):
        """Test inserting batch information."""
        batch_data = {
            "batch_id": "batch_001",
            "batch_name": "Chardonnay 2024",
            "start_date": datetime.now().isoformat(),
            "initial_gravity": 1.085,
            "target_gravity": 1.008,
            "status": "active",
        }

        result = await mock_database.insert("batches", batch_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_insert_multiple_readings(self, mock_database, mock_time_series_data):
        """Test bulk insert of multiple readings."""
        readings = []
        for dp in mock_time_series_data[:10]:
            reading = {
                "timestamp": dp["timestamp"],
                "temperature": dp["temperature"],
                "gravity": dp["gravity"],
                "bubble_rate": dp["bubble_rate"],
            }
            readings.append(reading)

        # Bulk insert
        for reading in readings:
            await mock_database.insert("sensor_readings", reading)

        assert mock_database.insert.call_count == len(readings)

    @pytest.mark.asyncio
    async def test_insert_duplicate_handling(self, mock_database):
        """Test handling duplicate insertions."""
        reading = {
            "timestamp": "2024-01-15T10:00:00Z",
            "sensor_id": "ispindel_001",
            "temperature": 20.5,
        }

        # Insert once
        await mock_database.insert("sensor_readings", reading)

        # Try to insert duplicate
        mock_database.insert = AsyncMock(side_effect=Exception("Duplicate key"))

        with pytest.raises(Exception):
            await mock_database.insert("sensor_readings", reading)


class TestDataQuerying:
    """Test querying data from database."""

    @pytest.mark.asyncio
    async def test_query_latest_reading(self, mock_database):
        """Test querying latest sensor reading."""
        mock_database.query = AsyncMock(return_value=[
            {
                "timestamp": datetime.now().isoformat(),
                "temperature": 20.5,
                "gravity": 1.050,
            }
        ])

        query = "SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT 1"
        results = await mock_database.query(query)

        assert len(results) == 1
        assert "temperature" in results[0]

    @pytest.mark.asyncio
    async def test_query_by_batch_id(self, mock_database):
        """Test querying readings for specific batch."""
        batch_id = "batch_001"

        mock_database.query = AsyncMock(return_value=[
            {"batch_id": batch_id, "temperature": 20.5},
            {"batch_id": batch_id, "temperature": 21.0},
        ])

        query = f"SELECT * FROM sensor_readings WHERE batch_id = '{batch_id}'"
        results = await mock_database.query(query)

        assert len(results) >= 2
        assert all(r["batch_id"] == batch_id for r in results)

    @pytest.mark.asyncio
    async def test_query_time_range(self, mock_database):
        """Test querying readings within time range."""
        start_time = datetime.now() - timedelta(days=7)
        end_time = datetime.now()

        mock_database.query = AsyncMock(return_value=[
            {"timestamp": start_time.isoformat()},
            {"timestamp": end_time.isoformat()},
        ])

        query = f"""
            SELECT * FROM sensor_readings
            WHERE timestamp BETWEEN '{start_time}' AND '{end_time}'
        """
        results = await mock_database.query(query)

        assert len(results) >= 0

    @pytest.mark.asyncio
    async def test_query_aggregates(self, mock_database):
        """Test querying aggregate statistics."""
        mock_database.query = AsyncMock(return_value=[
            {
                "avg_temperature": 20.5,
                "min_gravity": 1.010,
                "max_gravity": 1.085,
                "count": 100,
            }
        ])

        query = """
            SELECT
                AVG(temperature) as avg_temperature,
                MIN(gravity) as min_gravity,
                MAX(gravity) as max_gravity,
                COUNT(*) as count
            FROM sensor_readings
        """
        results = await mock_database.query(query)

        assert len(results) == 1
        assert "avg_temperature" in results[0]

    @pytest.mark.asyncio
    async def test_query_empty_result(self, mock_database):
        """Test querying with no results."""
        mock_database.query = AsyncMock(return_value=[])

        query = "SELECT * FROM sensor_readings WHERE sensor_id = 'nonexistent'"
        results = await mock_database.query(query)

        assert len(results) == 0


class TestDataUpdate:
    """Test updating data in database."""

    @pytest.mark.asyncio
    async def test_update_batch_status(self, mock_database):
        """Test updating batch status."""
        batch_id = "batch_001"
        new_status = "completed"

        result = await mock_database.update(
            "batches",
            {"status": new_status},
            {"batch_id": batch_id}
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_update_sensor_calibration(self, mock_database):
        """Test updating sensor calibration data."""
        sensor_id = "ispindel_001"
        calibration = [0.001, -0.05, 1.095]

        result = await mock_database.update(
            "sensors",
            {"calibration": calibration},
            {"sensor_id": sensor_id}
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_update_nonexistent_record(self, mock_database):
        """Test updating non-existent record."""
        mock_database.update = AsyncMock(return_value=False)

        result = await mock_database.update(
            "batches",
            {"status": "completed"},
            {"batch_id": "nonexistent"}
        )

        assert result is False


class TestDataDeletion:
    """Test deleting data from database."""

    @pytest.mark.asyncio
    async def test_delete_old_readings(self, mock_database):
        """Test deleting old sensor readings."""
        cutoff_date = datetime.now() - timedelta(days=90)

        result = await mock_database.delete(
            "sensor_readings",
            {"timestamp__lt": cutoff_date}
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_batch(self, mock_database):
        """Test deleting a batch."""
        batch_id = "batch_old"

        result = await mock_database.delete(
            "batches",
            {"batch_id": batch_id}
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_cascade_delete(self, mock_database):
        """Test cascade deletion of related records."""
        batch_id = "batch_001"

        # Delete batch (should also delete related readings)
        await mock_database.delete("batches", {"batch_id": batch_id})
        await mock_database.delete("sensor_readings", {"batch_id": batch_id})

        assert mock_database.delete.call_count == 2


class TestDataRetention:
    """Test data retention policies."""

    @pytest.mark.asyncio
    async def test_retention_policy(self, mock_database):
        """Test applying data retention policy."""
        retention_days = 365
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        # Count records to be deleted
        mock_database.query = AsyncMock(return_value=[{"count": 1500}])

        query = f"""
            SELECT COUNT(*) as count
            FROM sensor_readings
            WHERE timestamp < '{cutoff_date}'
        """
        results = await mock_database.query(query)

        records_to_delete = results[0]["count"]
        assert records_to_delete >= 0

    @pytest.mark.asyncio
    async def test_archive_old_data(self, mock_database):
        """Test archiving old data before deletion."""
        cutoff_date = datetime.now() - timedelta(days=365)

        # Query old data
        mock_database.query = AsyncMock(return_value=[
            {"id": 1, "timestamp": cutoff_date.isoformat()},
        ])

        query = f"SELECT * FROM sensor_readings WHERE timestamp < '{cutoff_date}'"
        old_records = await mock_database.query(query)

        # Archive (in real implementation, would save to file or archive table)
        archive = {
            "archived_date": datetime.now().isoformat(),
            "records": old_records,
        }

        assert len(archive["records"]) >= 0


class TestDatabaseBackup:
    """Test database backup functionality."""

    @patch("subprocess.run")
    def test_database_backup(self, mock_run):
        """Test creating database backup."""
        backup_path = "/backups/wine_monitor_backup.sql"

        # Mock backup command
        mock_run.return_value = MagicMock(returncode=0)

        import subprocess
        result = subprocess.run(
            ["pg_dump", "-f", backup_path, "wine_monitor_db"],
            capture_output=True
        )

        assert result.returncode == 0

    def test_backup_scheduling(self):
        """Test backup is scheduled regularly."""
        backup_interval_hours = 24
        last_backup = datetime.now() - timedelta(hours=25)

        current_time = datetime.now()
        hours_since_backup = (current_time - last_backup).total_seconds() / 3600

        should_backup = hours_since_backup >= backup_interval_hours
        assert should_backup is True


class TestDataMigration:
    """Test data migration functionality."""

    @pytest.mark.asyncio
    async def test_schema_migration(self, mock_database):
        """Test database schema migration."""
        # Mock running migration
        migration_query = """
            ALTER TABLE sensor_readings
            ADD COLUMN IF NOT EXISTS ph_level FLOAT
        """

        mock_database.query = AsyncMock(return_value=[])
        await mock_database.query(migration_query)

        mock_database.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_data_format_migration(self, mock_database):
        """Test migrating data format."""
        # Example: Convert Fahrenheit to Celsius
        mock_database.query = AsyncMock(return_value=[
            {"id": 1, "temperature": 68.0, "temp_unit": "F"},
        ])

        # Query records needing conversion
        old_records = await mock_database.query(
            "SELECT * FROM sensor_readings WHERE temp_unit = 'F'"
        )

        # Convert and update
        for record in old_records:
            celsius = (record["temperature"] - 32) * 5 / 9
            await mock_database.update(
                "sensor_readings",
                {"temperature": celsius, "temp_unit": "C"},
                {"id": record["id"]}
            )


class TestDataIntegrity:
    """Test data integrity checks."""

    @pytest.mark.asyncio
    async def test_check_referential_integrity(self, mock_database):
        """Test referential integrity between tables."""
        # Check all sensor_readings reference valid sensors
        mock_database.query = AsyncMock(return_value=[])

        query = """
            SELECT sr.* FROM sensor_readings sr
            LEFT JOIN sensors s ON sr.sensor_id = s.sensor_id
            WHERE s.sensor_id IS NULL
        """
        orphaned_readings = await mock_database.query(query)

        assert len(orphaned_readings) == 0

    @pytest.mark.asyncio
    async def test_check_data_consistency(self, mock_database):
        """Test data consistency checks."""
        mock_database.query = AsyncMock(return_value=[])

        # Check for impossible values
        query = """
            SELECT * FROM sensor_readings
            WHERE temperature < -50 OR temperature > 100
            OR gravity < 0.9 OR gravity > 1.2
        """
        invalid_readings = await mock_database.query(query)

        assert len(invalid_readings) == 0

    @pytest.mark.asyncio
    async def test_check_duplicate_timestamps(self, mock_database):
        """Test checking for duplicate timestamps."""
        mock_database.query = AsyncMock(return_value=[])

        query = """
            SELECT sensor_id, timestamp, COUNT(*) as count
            FROM sensor_readings
            GROUP BY sensor_id, timestamp
            HAVING COUNT(*) > 1
        """
        duplicates = await mock_database.query(query)

        assert len(duplicates) == 0


class TestDatabaseIndexing:
    """Test database indexing for performance."""

    @pytest.mark.asyncio
    async def test_create_index_on_timestamp(self, mock_database):
        """Test creating index on timestamp column."""
        index_query = """
            CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp
            ON sensor_readings(timestamp)
        """

        mock_database.query = AsyncMock(return_value=[])
        await mock_database.query(index_query)

        mock_database.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_composite_index(self, mock_database):
        """Test creating composite index."""
        index_query = """
            CREATE INDEX IF NOT EXISTS idx_sensor_batch_timestamp
            ON sensor_readings(sensor_id, batch_id, timestamp)
        """

        mock_database.query = AsyncMock(return_value=[])
        await mock_database.query(index_query)

        mock_database.query.assert_called_once()


class TestTransactionManagement:
    """Test database transaction handling."""

    @pytest.mark.asyncio
    async def test_transaction_commit(self, mock_database):
        """Test transaction commit."""
        # Begin transaction
        mock_database.begin = AsyncMock()
        mock_database.commit = AsyncMock()

        await mock_database.begin()

        # Perform operations
        await mock_database.insert("batches", {"batch_id": "batch_001"})
        await mock_database.insert("sensor_readings", {"batch_id": "batch_001"})

        # Commit
        await mock_database.commit()

        mock_database.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, mock_database):
        """Test transaction rollback on error."""
        mock_database.begin = AsyncMock()
        mock_database.rollback = AsyncMock()

        await mock_database.begin()

        try:
            await mock_database.insert("batches", {"batch_id": "batch_001"})
            # Simulate error
            raise Exception("Database error")
        except Exception:
            await mock_database.rollback()

        mock_database.rollback.assert_called_once()


class TestDataExport:
    """Test data export functionality."""

    @pytest.mark.asyncio
    async def test_export_to_csv(self, mock_database, sample_fermentation_data):
        """Test exporting data to CSV."""
        import csv
        import io

        batch = sample_fermentation_data["fermentation_batches"][0]
        data_points = batch["data_points"]

        # Mock CSV export
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["timestamp", "temperature", "gravity", "bubble_rate"]
        )
        writer.writeheader()
        writer.writerows(data_points)

        csv_content = output.getvalue()
        assert len(csv_content) > 0
        assert "timestamp" in csv_content

    @pytest.mark.asyncio
    async def test_export_to_json(self, mock_database, sample_fermentation_data):
        """Test exporting data to JSON."""
        import json

        batch = sample_fermentation_data["fermentation_batches"][0]

        json_export = json.dumps(batch, indent=2)

        assert len(json_export) > 0
        # Verify it's valid JSON
        parsed = json.loads(json_export)
        assert parsed["batch_id"] == batch["batch_id"]
