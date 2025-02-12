from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from src.db_connection import DuckDBConnection
from src.parquet_parser import ParquetParser
from src.logger_config import setup_logging, get_logger
from typing import List, Optional, Tuple
import logging
import os
from datetime import datetime
from contextlib import asynccontextmanager

# Create runs directory if it doesn't exist
os.makedirs('runs', exist_ok=True)

logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Handles startup (database connections, loading data) and shutdown (cleanup) events.
    """
    try:
        # Initialize DuckDB connection
        db = DuckDBConnection(db_file="interview.db")
        app.state.conn = db.connect()  # Store in app state

        # Initialize Parquet parser
        app.state.parser = ParquetParser(app.state.conn,logger=logger)

        # Load parquet files
        parquet_files = app.state.parser.get_parquet_files()
        logger.info(f"Found {len(parquet_files)} parquet files")

        for file in parquet_files:
            app.state.parser.process_file(file)

        # Create table
        app.state.table_name = app.state.parser.create_interview_table()

        if app.state.table_name:
            # Fetch table metadata
            row_count = app.state.conn.execute(f"SELECT COUNT(*) FROM {app.state.table_name}").fetchone()[0]
            logger.info(f"Table '{app.state.table_name}' created with {row_count} rows")

        yield  # Server is running and ready to accept requests

    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise
    finally:
        # Cleanup code (runs during shutdown)
        if hasattr(app.state, 'conn'):
            app.state.conn.close()

app = FastAPI(lifespan=lifespan)


def get_table_name() -> str:
    """Get the current table name from app state."""
    if not hasattr(app.state, "table_name") or not app.state.table_name:
        raise HTTPException(status_code=500, detail="Table name not initialized")
    return app.state.table_name

def get_vehicle_types() -> List[str]:
    """Get unique vehicle types from the database."""
    try:
        table_name = get_table_name()
        query = f"SELECT DISTINCT vehicle_type FROM {table_name} ORDER BY vehicle_type"
        result = app.state.conn.execute(query).fetchall()
        return [r[0] for r in result if r[0] is not None]
    except Exception as e:
        logger.error(f"Error fetching vehicle types: {e}", exc_info=True)
        return []

def generate_default_bins() -> List[Tuple[int, int]]:
    """Generate default bins from 1 to 100 in steps of 10."""
    return [(i, i + 9) for i in range(1, 101, 10)]

@app.get("/stats/")
async def get_stats():
    """Returns parquet processing statistics."""
    try:
        stats = app.state.parser.get_stats()
        logger.info("Stats retrieved successfully")
        return {
            "successful_files": stats["successful_files"],
            "failed_files": stats["failed_files"],
            "failed_details": [{"file": file, "error": error} for file, error in stats["failed_details"]],
        }
    except Exception as e:
        logger.error(f"Error retrieving stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class DetectionRateRequest(BaseModel):
    """Pydantic model to validate input parameters"""
    bins: Optional[List[Tuple[int, int]]] = None  # Will use generate_default_bins() if None
    vehicle_types: Optional[List[str]] = None  # Will use get_vehicle_types() if None

@app.post("/detection_rate/")
async def get_detection_rate(request: DetectionRateRequest):
    """
    Returns detection success rates per vehicle type within given distance bins.
    """
    try:
        if not hasattr(app.state, "conn") or app.state.conn is None:
            logger.error("Database connection is missing or was not initialized")
            raise HTTPException(status_code=500, detail="Database connection failed")

        # Get dynamic table name
        table_name = get_table_name()
        
        # Set default bins if not provided
        bins = request.bins if request.bins is not None else generate_default_bins()
        
        # Set default vehicle types if not provided
        vehicle_types = request.vehicle_types if request.vehicle_types is not None else get_vehicle_types()
        
        # Validate vehicle types exist in the table
        valid_types = get_vehicle_types()
        invalid_types = [vt for vt in vehicle_types if vt not in valid_types]
        if invalid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid vehicle types: {invalid_types}. Valid types are: {valid_types}"
            )

        # Build CASE statement for distance bins
        case_parts = []
        for start, end in bins:
            case_parts.append(f"WHEN distance BETWEEN {start} AND {end} THEN '{start}-{end}'")
        case_statement = " ".join(case_parts)

        # Build vehicle type filter
        vehicle_type_filter = ""
        if vehicle_types:
            vehicle_list = ", ".join(f"'{vt}'" for vt in vehicle_types)
            vehicle_type_filter = f"AND vehicle_type IN ({vehicle_list})"

        # Construct the full SQL query
        sql_query = f"""
        WITH BinnedData AS (
            SELECT 
                vehicle_type,
                distance,
                detection,
                CASE {case_statement} END as distance_bin
            FROM {table_name}
            WHERE distance BETWEEN {min(b[0] for b in bins)} AND {max(b[1] for b in bins)}
            {vehicle_type_filter}
        )
        SELECT 
            distance_bin,
            vehicle_type,
            ROUND(SUM(detection)::FLOAT / COUNT(*) * 100, 2) AS detection_success_rate
        FROM BinnedData
        WHERE distance_bin IS NOT NULL
        GROUP BY distance_bin, vehicle_type
        ORDER BY vehicle_type, distance_bin
        """

        logger.info(f"Executing SQL Query:\n{sql_query}")

        # Execute query in DuckDB
        df = app.state.conn.execute(sql_query).fetchdf()

        if df.empty:
            logger.warning("Query returned no results")
            return []

        logger.info(f"Detection rate query successful. Returned {len(df)} records")
        return df.to_dict(orient="records")
    
    except HTTPException:
        raise  # Re-raise HTTPException directly
    except Exception as e:
        logger.error(f"Error executing detection rate query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

### Start FastAPI with Uvicorn
def main():
    logger.info("Starting FastAPI application")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()