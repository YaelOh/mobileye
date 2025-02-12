import requests
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class ProcessingStats:
    successful_files: int
    failed_files: int
    failed_details: List[Dict[str, str]]

class QueryRequest(BaseModel):
    query: str

class DBClient:
    """Client for interacting with the detection analysis API."""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        """Initialize client with API endpoint configuration."""
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()
    
    def get_stats(self) -> ProcessingStats:
        """Fetch processing statistics from the API."""
        response = self._make_request("GET", "/stats/")
        return ProcessingStats(**response)
    
    def get_table_info(self) -> Optional[str]:
        """Get the current table name from the database."""
        query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'BASE TABLE'"
        tables_df = self.run_query(query)
        return tables_df['table_name'].iloc[0] if not tables_df.empty else None

    def get_row_count(self, table_name: str) -> int:
        """Get total number of rows in the specified table."""
        query = f"SELECT COUNT(*) as total FROM {table_name}"
        count_df = self.run_query(query)
        return count_df['total'].iloc[0] if not count_df.empty else 0

    def get_sample_data(self, table_name: str, limit: int = 3) -> pd.DataFrame:
        """Get sample rows from the specified table."""
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return self.run_query(query)
    
    def run_query(self, query: str) -> pd.DataFrame:
        """Execute a custom SQL query."""
        print(f"Running query: {query}")
        response = self._make_request(
            "POST", "/query/", json={"query": query}
        )
        return pd.DataFrame(response)

    def get_detection_rate(
        self, 
        bins: Optional[List[Tuple[int, int]]] = None,
        vehicle_types: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get detection success rates for vehicle types within distance bins.
        
        Args:
            bins: List of (start, end) distance ranges. Defaults to 1-100 in steps of 10.
            vehicle_types: List of vehicle types to analyze. Defaults to all types.
        
        Returns:
            DataFrame with columns: distance_bin, vehicle_type, detection_success_rate
        """
        payload = {k: v for k, v in {
            "bins": bins,
            "vehicle_types": vehicle_types
        }.items() if v is not None}

        response = self._make_request("POST", "/detection_rate/", json=payload)
        return pd.DataFrame(response)

    ## this can be hold also in the generic client
    # def run_step_2_create_sql_query_over_data(self) -> Dict[str, Any]:
    #     """Execute the step 2 analysis pipeline."""
    #     return self._make_request("POST", "/step_2_create_sql_query_over_data/")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make HTTP request to API endpoint with error handling."""
        url = f"{self.base_url}{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

def main():
    """Entry point for command line usage."""
    from examples_detection_analysis import run_examples
    run_examples()

if __name__ == "__main__":
    main()