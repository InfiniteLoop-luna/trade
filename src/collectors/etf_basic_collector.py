import pandas as pd
from datetime import datetime
from sqlalchemy import select
from src.collectors.base_collector import BaseCollector
from src.models import ETFBasic
from src.logger import setup_logger

logger = setup_logger(__name__)

class ETFBasicCollector(BaseCollector):
    """ETF基础信息采集器"""

    def collect_full(self):
        """全量采集ETF基础信息"""
        logger.info("Starting full ETF basic info collection")

        try:
            # Fetch data from Tushare
            df = self.client.get_etf_basic(market='E')

            if df.empty:
                logger.warning("No ETF basic data fetched")
                return

            # Convert date columns
            date_columns = ['found_date', 'due_date', 'list_date', 'issue_date', 'delist_date']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], format='%Y%m%d', errors='coerce')

            # Replace NaT with None for database compatibility
            df = df.where(pd.notna(df), None)

            # Save to database
            with self.db.get_session() as session:
                # Delete existing records
                session.query(ETFBasic).delete()

                # Get valid column names from the model (excluding created_at and updated_at)
                valid_columns = {c.name for c in ETFBasic.__table__.columns
                                if c.name not in ('created_at', 'updated_at')}

                # Insert new records
                records = df.to_dict('records')
                for record in records:
                    # Filter record to only include valid columns
                    filtered_record = {k: v for k, v in record.items() if k in valid_columns}
                    etf = ETFBasic(**filtered_record)
                    session.add(etf)

                logger.info(f"Saved {len(records)} ETF basic records")

        except Exception as e:
            logger.error(f"Failed to collect ETF basic info: {e}")
            raise

    def collect_incremental(self):
        """增量采集 - ETF基础信息通常不需要增量更新"""
        logger.info("ETF basic info uses full update only")
        self.collect_full()
