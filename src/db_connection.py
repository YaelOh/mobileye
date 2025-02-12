# db_connection.py
import duckdb

class DuckDBConnection:
    def __init__(self, db_file: str = ':memory:'):
        self.db_file = db_file
        self.conn = None
    
    def connect(self):
        self.conn = duckdb.connect(self.db_file)
        return self.conn
    
    def close(self):
        if self.conn:
            self.conn.close()