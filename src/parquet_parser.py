import os
import logging
from typing import List, Tuple, Optional

class ParquetParser:
    def __init__(self, conn, data_dir: str = '/data', logger=None):
        self.conn = conn
        self.data_dir = data_dir
        self.successful_queries = []
        self.failed_files = []
        self.logger = logger or logging.getLogger(__name__)

    def get_parquet_files(self) -> List[str]:
        """Get list of parquet files in the data directory."""
        files = [f for f in os.listdir(self.data_dir) if f.endswith('.parquet')]
        self.logger.info(f"Found {len(files)} parquet files in {self.data_dir}")
        return files

    def process_file(self, file: str) -> bool:
        """Process a single parquet file and add it to successful queries if valid."""
        try:
            self.logger.info(f"Processing file: {file}")
            test_query = f"SELECT * FROM parquet_scan('{self.data_dir}/{file}') LIMIT 1"
            self.conn.execute(test_query)
            self.successful_queries.append(f"SELECT * FROM parquet_scan('{self.data_dir}/{file}')")
            self.logger.info(f"✓ Successfully processed {file}")
            return True
        except Exception as e:
            self.failed_files.append((file, str(e)))
            self.logger.error(f"✗ Error processing {file}: {str(e)}", exc_info=True)
            return False

    def create_interview_table(self) -> Optional[str]:
        """Create a table from all successfully processed parquet files."""
        if not self.successful_queries:
            self.logger.warning("No successful queries to create table from")
            return None
        
        try:
            # Create the table from the union of all successful parquet files
            union_query = " UNION ALL ".join(self.successful_queries)
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS interview_table AS 
            {union_query}
            """
            self.conn.execute(create_table_query)
            self.logger.info("Successfully created interview_table")
            return "interview_table"
        except Exception as e:
            self.logger.error(f"Error creating interview_table: {str(e)}", exc_info=True)
            return None

    def get_stats(self) -> dict:
        """Get statistics about processed files."""
        stats = {
            "successful_files": len(self.successful_queries),
            "failed_files": len(self.failed_files),
            "failed_details": self.failed_files
        }
        self.logger.debug(f"Returning stats: {stats}")
        return stats