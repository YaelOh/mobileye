# src/logger_config.py
import logging
from pathlib import Path
from datetime import datetime

def setup_logging(runs_dir: str = "runs") -> logging.Logger:
    """
    Configure and set up logging for the application.
    
    Args:
        runs_dir: Directory where log files will be stored
        
    Returns:
        logging.Logger: Configured root logger
    """
    # Create runs directory if it doesn't exist
    runs_path = Path(runs_dir)
    runs_path.mkdir(exist_ok=True)

    # Configure logging with timestamp
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = runs_path / f'app_{current_time}.log'

    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove any existing handlers to avoid duplication
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create handlers
    file_handler = logging.FileHandler(str(log_file))
    console_handler = logging.StreamHandler()

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging configured. Log file: {log_file}")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Name for the logger
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)