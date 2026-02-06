import tushare as ts
import time
import pandas as pd
from retry import retry
from typing import Optional
from config import Config
from src.logger import setup_logger

logger = setup_logger(__name__)

class TushareClient:
    """Tushare API client with rate limiting and retry logic"""

    def __init__(self, config: Config):
        self.config = config
        ts.set_token(config.TUSHARE_TOKEN)
        self.pro = ts.pro_api()
        logger.info("Tushare client initialized")

    def _rate_limit(self):
        """Apply rate limiting between API calls"""
        time.sleep(self.config.API_CALL_INTERVAL)

    @retry(tries=3, delay=1, backoff=2, logger=logger)
    def get_etf_basic(self, market: str = '') -> pd.DataFrame:
        """
        获取ETF基础信息

        Args:
            market: 市场类型 (E=沪深交易所, O=场外)

        Returns:
            DataFrame with ETF basic information
        """
        try:
            self._rate_limit()
            df = self.pro.fund_basic(market=market)
            logger.info(f"Fetched {len(df)} ETF basic records")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch ETF basic info: {e}")
            raise

    @retry(tries=3, delay=1, backoff=2, logger=logger)
    def get_etf_share_size(
        self,
        ts_code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取ETF份额规模数据

        Args:
            ts_code: ETF代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            DataFrame with ETF share size data
        """
        try:
            self._rate_limit()
            df = self.pro.fund_share(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            logger.info(f"Fetched {len(df)} ETF share size records")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch ETF share size: {e}")
            raise

    @retry(tries=3, delay=1, backoff=2, logger=logger)
    def get_trade_calendar(
        self,
        exchange: str = 'SSE',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_open: str = '1'
    ) -> pd.DataFrame:
        """
        获取交易日历

        Args:
            exchange: 交易所 (SSE上交所, SZSE深交所)
            start_date: 开始日期
            end_date: 结束日期
            is_open: 是否交易 (1=是, 0=否)

        Returns:
            DataFrame with trade calendar
        """
        try:
            self._rate_limit()
            df = self.pro.trade_cal(
                exchange=exchange,
                start_date=start_date,
                end_date=end_date,
                is_open=is_open
            )
            logger.info(f"Fetched {len(df)} trade calendar records")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch trade calendar: {e}")
            raise
