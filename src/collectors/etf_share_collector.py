import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import select, func
from src.collectors.base_collector import BaseCollector
from src.models import ETFBasic, ETFShareSize
from src.logger import setup_logger

logger = setup_logger(__name__)

class ETFShareCollector(BaseCollector):
    """ETF份额规模采集器"""

    def get_latest_date(self) -> str:
        """获取数据库中最新的交易日期"""
        with self.db.get_session() as session:
            result = session.query(func.max(ETFShareSize.trade_date)).scalar()
            if result:
                return result.strftime('%Y%m%d')
            return None

    def get_etf_list(self) -> list:
        """获取所有ETF代码列表"""
        with self.db.get_session() as session:
            etfs = session.query(ETFBasic.ts_code).all()
            return [etf[0] for etf in etfs]

    def collect_full(self, start_date: str = '20200101'):
        """
        全量采集ETF份额规模数据

        Args:
            start_date: 开始日期 (YYYYMMDD)
        """
        logger.info(f"Starting full ETF share size collection from {start_date}")

        try:
            etf_list = self.get_etf_list()
            logger.info(f"Found {len(etf_list)} ETFs to collect")

            end_date = datetime.now().strftime('%Y%m%d')
            total_records = 0

            for ts_code in etf_list:
                try:
                    df = self.client.get_etf_share_size(
                        ts_code=ts_code,
                        start_date=start_date,
                        end_date=end_date
                    )

                    if df.empty:
                        continue

                    # Convert date column
                    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')

                    # Save to database
                    with self.db.get_session() as session:
                        # Get valid column names from the model (excluding id and created_at)
                        valid_columns = {c.name for c in ETFShareSize.__table__.columns
                                        if c.name not in ('id', 'created_at')}

                        records = df.to_dict('records')
                        for record in records:
                            # Filter record to only include valid columns
                            filtered_record = {k: v for k, v in record.items() if k in valid_columns}
                            share = ETFShareSize(**filtered_record)
                            session.merge(share)

                        total_records += len(records)
                        logger.info(f"Saved {len(records)} records for {ts_code}")

                except Exception as e:
                    logger.error(f"Failed to collect {ts_code}: {e}")
                    continue

            logger.info(f"Full collection completed. Total records: {total_records}")

        except Exception as e:
            logger.error(f"Failed to collect ETF share size: {e}")
            raise

    def collect_incremental(self):
        """增量采集ETF份额规模数据"""
        logger.info("Starting incremental ETF share size collection")

        try:
            latest_date = self.get_latest_date()

            if not latest_date:
                logger.warning("No existing data found, running full collection")
                self.collect_full()
                return

            # Calculate start date (next day after latest)
            latest_dt = datetime.strptime(latest_date, '%Y%m%d')
            start_dt = latest_dt + timedelta(days=1)
            start_date = start_dt.strftime('%Y%m%d')
            end_date = datetime.now().strftime('%Y%m%d')

            logger.info(f"Collecting data from {start_date} to {end_date}")

            etf_list = self.get_etf_list()
            total_records = 0

            for ts_code in etf_list:
                try:
                    df = self.client.get_etf_share_size(
                        ts_code=ts_code,
                        start_date=start_date,
                        end_date=end_date
                    )

                    if df.empty:
                        continue

                    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')

                    with self.db.get_session() as session:
                        # Get valid column names from the model (excluding id and created_at)
                        valid_columns = {c.name for c in ETFShareSize.__table__.columns
                                        if c.name not in ('id', 'created_at')}

                        records = df.to_dict('records')
                        for record in records:
                            # Filter record to only include valid columns
                            filtered_record = {k: v for k, v in record.items() if k in valid_columns}
                            share = ETFShareSize(**filtered_record)
                            session.merge(share)

                        total_records += len(records)

                except Exception as e:
                    logger.error(f"Failed to collect {ts_code}: {e}")
                    continue

            logger.info(f"Incremental collection completed. New records: {total_records}")

        except Exception as e:
            logger.error(f"Failed incremental collection: {e}")
            raise
