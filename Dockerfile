FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the source code
COPY ./src ./src

# Add the current directory to PYTHONPATH
ENV PYTHONPATH=/app

EXPOSE 8000

# Run from the src directory
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]