"""
Example usage of the DBClient for detection analysis.
Shows various ways to query and analyze detection data.
"""

import requests
from rich import print
from typing import Optional
from db_client import DBClient

def print_stats(client: DBClient) -> None:
    """Print processing statistics."""
    try:
        stats = client.get_stats()
        print("\n📊 Processing Statistics:")
        print(f"✅ Successful files: {stats.successful_files}")
        print(f"❌ Failed files: {stats.failed_files}")
        if stats.failed_details:
            print("\n🚨 Failed file details:")
            for detail in stats.failed_details:
                print(f"❌ File: {detail['file']}, Error: {detail['error']}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error fetching stats: {e}")

def print_table_info(client: DBClient) -> Optional[str]:
    """Print basic table information and return table name if found."""
    try:
        table_name = client.get_table_info()
        if table_name:
            row_count = client.get_row_count(table_name)
            print(f"\n📌 Total rows in table: {row_count}")
            
            sample_df = client.get_sample_data(table_name)
            if not sample_df.empty:
                print("\n📌 Sample Data:")
                print(sample_df)
            return table_name
        print("\n⚠️ No tables found in database")
        return None
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error querying table info: {e}")
        return None

def print_detection_rates(client: DBClient) -> None:
    """Print various detection rate analyses."""
    try:
        # Default analysis
        print("\n🚗 Detection Success Rate (Default bins, all vehicles)")
        print(client.get_detection_rate())
        
        # Custom bins analysis
        print("\n🚛 Detection Success Rate (Custom bins, trucks only)")
        print(client.get_detection_rate(
            bins=[(0, 25), (26, 50), (51, 75)],
            vehicle_types=["truck"]
        ))
        
        # Specific vehicles analysis
        print("\n🚗 Detection Success Rate (Default bins, specific vehicles)")
        print(client.get_detection_rate(vehicle_types=["car", "truck"]))
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error fetching detection rate: {e}")

def run_examples() -> None:
    """Run all example analyses."""
    client = DBClient()
    print_stats(client)
    print_table_info(client)
    print_detection_rates(client)