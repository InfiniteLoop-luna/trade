import logging
import socket
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from config import Config
from src.models import Base

logger = logging.getLogger(__name__)

class Database:
    """Database connection manager"""

    def __init__(self, config: Config):
        self.config = config
        self.engine = None
        self.SessionLocal = None

    def _resolve_ipv4(self, hostname):
        """Resolve hostname to IPv4 address to avoid IPv6 issues in GitHub Actions

        Returns:
            tuple: (ipv4_address, success) where success is True if resolution succeeded
        """
        try:
            # Get all addresses for the hostname
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
            if addr_info:
                # Return the first IPv4 address
                ipv4_addr = addr_info[0][4][0]
                logger.info(f"Resolved {hostname} to IPv4: {ipv4_addr}")
                return ipv4_addr, True
        except socket.gaierror as e:
            logger.warning(f"Failed to resolve {hostname} to IPv4: {e}, will use hostname without hostaddr")
        return None, False

    def connect(self):
        """Initialize database connection"""
        try:
            # Build database URL with IPv4 resolution
            from urllib.parse import quote_plus
            encoded_password = quote_plus(self.config.DB_PASSWORD) if self.config.DB_PASSWORD else ''

            # Use connection pooler for CI environments (better IPv4 support)
            if self.config.USE_POOLER and self.config.DB_POOLER_HOST:
                # Try to resolve pooler hostname to IPv4
                pooler_ipv4, resolved = self._resolve_ipv4(self.config.DB_POOLER_HOST)

                # Extract project reference from DB_HOST for Supabase pooler username format
                project_ref = None
                if 'supabase.co' in self.config.DB_HOST:
                    parts = self.config.DB_HOST.split('.')
                    if len(parts) >= 3 and parts[0] == 'db':
                        project_ref = parts[1]

                # Format username as db-user.project-ref for Supabase pooler
                username = f"{self.config.DB_USER}.{project_ref}" if project_ref else self.config.DB_USER
                host = self.config.DB_POOLER_HOST  # Use hostname for SSL verification
                port = 6543

                # Only use hostaddr if IPv4 resolution succeeded
                connect_args = {
                    "sslmode": self.config.DB_SSLMODE,
                    "connect_timeout": 15
                }
                if resolved:
                    connect_args["hostaddr"] = pooler_ipv4  # Force IPv4 connection
                    logger.info(f"Using Supabase connection pooler: {self.config.DB_POOLER_HOST} (IPv4: {pooler_ipv4})")
                else:
                    logger.info(f"Using Supabase connection pooler: {self.config.DB_POOLER_HOST} (no IPv4 resolution)")
            else:
                # Use direct connection - try IPv4 resolution
                ipv4_addr, resolved = self._resolve_ipv4(self.config.DB_HOST)
                username = self.config.DB_USER
                host = self.config.DB_HOST  # Use hostname for SSL verification
                port = self.config.DB_PORT

                # Only use hostaddr if IPv4 resolution succeeded
                connect_args = {
                    "sslmode": self.config.DB_SSLMODE,
                    "connect_timeout": 30,
                    "keepalives": 1,
                    "keepalives_idle": 30,
                    "keepalives_interval": 10,
                    "keepalives_count": 5
                }
                if resolved:
                    connect_args["hostaddr"] = ipv4_addr  # Force IPv4 connection
                    logger.info(f"Using direct connection: {self.config.DB_HOST} (IPv4: {ipv4_addr})")
                else:
                    logger.info(f"Using direct connection: {self.config.DB_HOST} (no IPv4 resolution)")

            database_url = f"postgresql://{username}:{encoded_password}@{host}:{port}/{self.config.DB_NAME}?sslmode={self.config.DB_SSLMODE}&sslrootcert=system"

            self.engine = create_engine(
                database_url,
                poolclass=NullPool,
                echo=False,
                connect_args=connect_args,
                pool_pre_ping=True
            )
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def create_tables(self):
        """Create all tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    @contextmanager
    def get_session(self) -> Session:
        """Get database session with context manager"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")
