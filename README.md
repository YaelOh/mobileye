```markdown
# Vehicle Detection Analysis API

A FastAPI-based application for analyzing vehicle detection data from parquet files. This API provides endpoints for querying detection rates, statistics, and custom SQL queries.

## 🚀 Features

- Parquet file processing and data aggregation
- Vehicle detection rate analysis with customizable distance bins
- Statistical analysis and reporting
- Custom SQL query support
- Comprehensive logging system
- Docker support for easy deployment

## 📋 Prerequisites

- Python 3.9+
- Docker (optional)
- Docker Compose (optional)

## 🛠️ Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/YaelOh/mobileye.git
cd <mobileye>
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### 🐳 Docker Deployment

1. Build and run using Docker Compose:
```bash
docker-compose up --build
```

## 📁 Project Structure

```
project/
├── client/
│   ├── __init__.py
│   ├── db_client.py
│   ├── examples_detection_analysis.py
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── db_connection.py
│   ├── parquet_parser.py
│   └── logger_config.py
├── data/
│   └── your_parquet_files.parquet
├── tests/
│   └── test_api.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🔧 Configuration

The application uses several configuration options that can be set via environment variables:

- `DATA_DIR`: Directory containing parquet files (default: `/data`)
- `DB_FILE`: DuckDB database file (default: `interview.db`)
- `HOST`: API host (default: `0.0.0.0`)
- `PORT`: API port (default: `8000`)

## 📌 API Endpoints

### GET `/stats/`
Returns processing statistics for parquet files.

### POST `/detection_rate/`
Calculate detection rates with customizable parameters.

Request body:
```json
{
    "bins": [[1, 10], [11, 20]],  // Optional
    "vehicle_types": ["car", "truck"]  // Optional
}
```

### POST `/query/`
Execute custom SQL queries against the database.

Request body:
```json
{
    "query": "SELECT * FROM interview_table LIMIT 5"
}
```

## 📊 Example Usage

```python
from db_client import DBClient

# Initialize client
client = DBClient()

# Get processing stats
stats = client.get_stats()

# Get detection rates
rates = client.get_detection_rate(
    bins=[(1, 10), (11, 20)],
    vehicle_types=["car", "truck"]
)
```

## 🧪 Running Tests

```bash
pytest tests/
```

## 📝 Logging

The application uses a centralized logging system that writes to both console and file:
- Log files are stored in the `runs/` directory
- Each run creates a new log file with timestamp
- Logs include timestamps, log levels, and detailed error information

## 🔒 Security

- Basic SQL injection prevention
- Table name validation
- Input validation using Pydantic models
- Error handling and logging


