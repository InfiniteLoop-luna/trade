from abc import ABC, abstractmethod
from src.database import Database
from src.tushare_client import TushareClient
from src.logger import setup_logger

logger = setup_logger(__name__)

class BaseCollector(ABC):
    """Base class for data collectors"""

    def __init__(self, db: Database, client: TushareClient):
        self.db = db
        self.client = client

    @abstractmethod
    def collect_full(self):
        """Full data collection"""
        pass

    @abstractmethod
    def collect_incremental(self):
        """Incremental data collection"""
        pass
