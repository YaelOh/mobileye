# tests/test_api.py

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app, get_vehicle_types, get_table_name, generate_default_bins
import pandas as pd
import os

# Constants
TEST_TABLE_NAME = "test_table"
MOCK_VEHICLE_TYPES = ["car", "truck", "bus"]
MOCK_DETECTION_DATA = {
    "distance_bin": ["1-10", "11-20", "21-30"],
    "vehicle_type": ["car", "car", "car"],
    "detection_success_rate": [85.5, 75.2, 65.8]
}

@pytest.fixture
def mock_app_state():
    with patch("src.main.app.state") as mock_state:
        mock_state.conn = MagicMock()
        mock_state.parser = MagicMock()
        mock_state.table_name = TEST_TABLE_NAME
        mock_state.db_client = MagicMock()  # Mock DBClient
        yield mock_state

@pytest.fixture
def mock_parquet_parser():
    with patch("src.main.ParquetParser") as MockParser:
        parser_instance = MockParser.return_value
        parser_instance.get_parquet_files.return_value = ["test.parquet"]
        parser_instance.create_interview_table.return_value = TEST_TABLE_NAME
        yield parser_instance

class TestAppLifespan:
    @pytest.mark.asyncio
    async def test_lifespan_initialization(self, mock_parquet_parser):
        with patch("src.main.DuckDBConnection") as MockDB:
            db_instance = MockDB.return_value
            db_instance.connect.return_value = MagicMock()
            
            async with app.router.lifespan_context(app):
                assert hasattr(app.state, "conn")
                assert hasattr(app.state, "parser")
                assert hasattr(app.state, "table_name")
                assert app.state.table_name == TEST_TABLE_NAME

    @pytest.mark.asyncio
    async def test_lifespan_cleanup(self, mock_parquet_parser):
        """Test cleanup on application shutdown."""
        with patch("src.main.DuckDBConnection") as MockDB:
            db_instance = MockDB.return_value
            conn_mock = MagicMock()
            db_instance.connect.return_value = conn_mock
            
            async with app.router.lifespan_context(app):
                pass
            
            conn_mock.close.assert_called_once()

class TestStatsEndpoint:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_stats_success(self, mock_app_state, client):
        """Test successful stats retrieval."""
        mock_app_state.parser.get_stats.return_value = {
            "successful_files": 3,
            "failed_files": 1,
            "failed_details": [("bad.parquet", "error")]
        }

        response = client.get("/stats/")
        assert response.status_code == 200
        assert response.json() == {
            "successful_files": 3,
            "failed_files": 1,
            "failed_details": [{"file": "bad.parquet", "error": "error"}]
        }

    def test_get_stats_error(self, mock_app_state, client):
        """Test error handling in stats retrieval."""
        mock_app_state.parser.get_stats.side_effect = Exception("Database error")
        response = client.get("/stats/")
        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]

class TestDetectionRateEndpoint:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def mock_db_response(self):
        return pd.DataFrame(MOCK_DETECTION_DATA)

    @pytest.fixture
    def mock_get_vehicle_types(self):
        with patch("src.main.get_vehicle_types", autospec=True) as mock:
            mock.side_effect = lambda: MOCK_VEHICLE_TYPES
            yield mock

    def test_default_parameters(self, mock_app_state, client, mock_db_response, mock_get_vehicle_types):
        """Test endpoint with default parameters."""
        with patch("src.main.app.state.conn.execute") as mock_execute:
            mock_execute.return_value.fetchdf.return_value = mock_db_response
            response = client.post("/detection_rate/", json={})
            assert response.status_code == 200
            assert len(response.json()) > 0

    def test_custom_bins(self, mock_app_state, client, mock_db_response, mock_get_vehicle_types):
        """Test endpoint with custom distance bins."""
        custom_bins = [(0, 50), (51, 100)]
        with patch("src.main.app.state.conn.execute") as mock_execute:
            mock_execute.return_value.fetchdf.return_value = mock_db_response
            response = client.post("/detection_rate/", json={"bins": custom_bins})
            assert response.status_code == 200

    def test_custom_vehicle_types(self, mock_app_state, client, mock_db_response, mock_get_vehicle_types):
        """Test endpoint with specific vehicle types."""
        with patch("src.main.app.state.conn.execute") as mock_execute:
            mock_execute.return_value.fetchdf.return_value = mock_db_response
            response = client.post("/detection_rate/", 
                                 json={"vehicle_types": ["car", "truck"]})
            assert response.status_code == 200

    def test_invalid_vehicle_type(self, mock_app_state, client, mock_get_vehicle_types):
        """Test handling of invalid vehicle types."""
        response = client.post("/detection_rate/", 
                             json={"vehicle_types": ["invalid_type"]})
        assert response.status_code == 400
        assert "Invalid vehicle types" in response.json()["detail"]

    def test_empty_result(self, mock_app_state, client, mock_get_vehicle_types):
        """Test handling of empty query results."""
        with patch("src.main.app.state.conn.execute") as mock_execute:
            mock_execute.return_value.fetchdf.return_value = pd.DataFrame()
            response = client.post("/detection_rate/", json={})
            assert response.status_code == 200
            assert response.json() == []

class TestUtilityFunctions:
    def test_generate_default_bins(self):
        """Test default bin generation."""
        bins = generate_default_bins()
        assert len(bins) == 10
        assert bins[0] == (1, 10)
        assert bins[-1] == (91, 100)

    def test_get_table_name_success(self, mock_app_state):
        """Test successful table name retrieval."""
        assert get_table_name() == TEST_TABLE_NAME

    def test_get_table_name_not_initialized(self):
        """Test table name retrieval when not initialized."""
        with patch("src.main.app.state") as mock_state:
            mock_state.table_name = None
            with pytest.raises(HTTPException) as exc:
                get_table_name()
            assert exc.value.status_code == 500

    def test_get_vehicle_types_success(self, mock_app_state):
        """Test successful vehicle types retrieval."""
        mock_app_state.conn.execute.return_value.fetchall.return_value = [
            ("car",), ("truck",), ("bus",)
        ]
        with patch("src.main.get_table_name", return_value=TEST_TABLE_NAME):
            result = get_vehicle_types()
            assert result == MOCK_VEHICLE_TYPES
            mock_app_state.conn.execute.assert_called_once()

class TestErrorHandling:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_missing_db_connection(self, client):
        """Test handling of missing database connection."""
        with patch("src.main.app.state") as mock_state:
            if hasattr(mock_state, "conn"):
                delattr(mock_state, "conn")
            response = client.post("/detection_rate/", json={})
            assert response.status_code == 500
            assert "Database connection failed" in response.json()["detail"]

    def test_database_query_error(self, mock_app_state, client):
        """Test handling of database query errors."""
        with patch("src.main.app.state.conn.execute") as mock_execute:
            mock_execute.side_effect = Exception("Database query failed")
            response = client.post("/detection_rate/", json={})
            assert response.status_code == 500
            assert "Internal Server Error" in response.json()["detail"]