import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

class Config:
    """Configuration class for ETF data collection system"""

    # Tushare Configuration
    TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN')

    # Database Configuration
    DB_HOST = os.getenv('DB_HOST')
    try:
        DB_PORT = int(os.getenv('DB_PORT', 5432))
    except (ValueError, TypeError):
        DB_PORT = 5432
    DB_NAME = os.getenv('DB_NAME', 'postgres')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_SSLMODE = os.getenv('DB_SSLMODE', 'verify-full')

    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/etf_collector.log')

    # API Rate Limiting
    API_RETRY_TIMES = 3
    API_RETRY_DELAY = 1  # seconds
    API_CALL_INTERVAL = 0.2  # seconds between calls

    @property
    def database_url(self):
        """Generate SQLAlchemy database URL"""
        encoded_password = quote_plus(self.DB_PASSWORD) if self.DB_PASSWORD else ''
        # Add sslmode and target_session_attrs for better connectivity in GitHub Actions
        # target_session_attrs=read-write helps with connection reliability
        return f"postgresql://{self.DB_USER}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?sslmode={self.DB_SSLMODE}&sslrootcert=system&target_session_attrs=read-write"

    def validate(self):
        """Validate required configuration"""
        required = ['TUSHARE_TOKEN', 'DB_HOST', 'DB_PASSWORD']
        missing = [key for key in required if not getattr(self, key)]
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")

        # Validate numeric values are positive
        if self.API_RETRY_TIMES <= 0:
            raise ValueError("API_RETRY_TIMES must be a positive number")
        if self.API_RETRY_DELAY <= 0:
            raise ValueError("API_RETRY_DELAY must be a positive number")
        if self.API_CALL_INTERVAL <= 0:
            raise ValueError("API_CALL_INTERVAL must be a positive number")
