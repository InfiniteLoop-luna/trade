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
        """Resolve hostname to IPv4 address to avoid IPv6 issues in GitHub Actions"""
        try:
            # Get all addresses for the hostname
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
            if addr_info:
                # Return the first IPv4 address
                ipv4_addr = addr_info[0][4][0]
                logger.info(f"Resolved {hostname} to IPv4: {ipv4_addr}")
                return ipv4_addr
        except socket.gaierror as e:
            logger.warning(f"Failed to resolve {hostname} to IPv4: {e}, using hostname as-is")
        return hostname

    def connect(self):
        """Initialize database connection"""
        try:
            # Resolve hostname to IPv4 to avoid IPv6 connectivity issues in GitHub Actions
            ipv4_host = self._resolve_ipv4(self.config.DB_HOST)

            # Build database URL with resolved IPv4 address
            from urllib.parse import quote_plus
            encoded_password = quote_plus(self.config.DB_PASSWORD) if self.config.DB_PASSWORD else ''
            database_url = f"postgresql://{self.config.DB_USER}:{encoded_password}@{ipv4_host}:{self.config.DB_PORT}/{self.config.DB_NAME}?sslmode={self.config.DB_SSLMODE}&sslrootcert=system&target_session_attrs=read-write"

            # Connection arguments for Supabase with SSL
            # Add options to improve connectivity in GitHub Actions
            connect_args = {
                "sslmode": self.config.DB_SSLMODE,
                "connect_timeout": 30,
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5
            }

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
