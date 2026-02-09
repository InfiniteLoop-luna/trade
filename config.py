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
    # Optional: Supabase connection pooler host (e.g., aws-0-us-east-1.pooler.supabase.com)
    DB_POOLER_HOST = os.getenv('DB_POOLER_HOST')
    try:
        DB_PORT = int(os.getenv('DB_PORT', 5432))
    except (ValueError, TypeError):
        DB_PORT = 5432
    DB_NAME = os.getenv('DB_NAME', 'postgres')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_SSLMODE = os.getenv('DB_SSLMODE', 'verify-full')
    # Use connection pooler for better IPv4 support in CI environments
    # Set to 'true' to use Supabase connection pooler (port 6543)
    USE_POOLER = os.getenv('USE_POOLER', 'false').lower() == 'true'

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

        # Use connection pooler for CI environments (better IPv4 support)
        if self.USE_POOLER and self.DB_POOLER_HOST:
            # Use provided pooler hostname
            # Supabase pooler format: postgres://[db-user].[project-ref]:[password]@[pooler-host]:6543/postgres
            # Extract project reference from DB_HOST (e.g., db.xxx.supabase.co -> xxx)
            project_ref = None
            if 'supabase.co' in self.DB_HOST:
                parts = self.DB_HOST.split('.')
                if len(parts) >= 3 and parts[0] == 'db':
                    project_ref = parts[1]

            # Format username as db-user.project-ref for Supabase pooler
            username = f"{self.DB_USER}.{project_ref}" if project_ref else self.DB_USER
            host = self.DB_POOLER_HOST
            port = 6543
        else:
            # Use direct connection
            username = self.DB_USER
            host = self.DB_HOST
            port = self.DB_PORT

        # Add sslmode and connection parameters for reliability
        return f"postgresql://{username}:{encoded_password}@{host}:{port}/{self.DB_NAME}?sslmode={self.DB_SSLMODE}&sslrootcert=system"

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
