import os

class Settings:
    DATA_DIR = os.getenv('DATA_DIR', '/data')
    DB_FILE = os.getenv('DB_FILE', 'interview.db')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '8000'))
    
settings = Settings()