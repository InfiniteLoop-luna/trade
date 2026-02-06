# ETF Data Collection and Management System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a production-ready ETF data collection system that fetches ETF basic info and share size data from Tushare Pro, stores in Supabase PostgreSQL, supports full/incremental updates, and deploys on Streamlit Cloud.

**Architecture:** OOP design with separate modules for database operations, Tushare API client, data collectors, and Streamlit UI. Incremental updates detect latest date in DB and fetch only missing data. Rate limiting and retry logic handle API constraints.

**Tech Stack:** Python 3.11+, Tushare Pro SDK, SQLAlchemy, psycopg2, Supabase PostgreSQL, Streamlit, Docker, GitHub Actions

---

## Task 1: Project Structure and Environment Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `README.md`
- Create: `config.py`

**Step 1: Create requirements.txt**

```txt
tushare>=1.4.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
streamlit>=1.30.0
pandas>=2.0.0
retry>=0.9.2
```

**Step 2: Create .env.example**

```env
# Tushare Configuration
TUSHARE_TOKEN=your_tushare_token_here

# Supabase PostgreSQL Configuration
DB_HOST=your_supabase_host.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_SSLMODE=require

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/etf_collector.log
```

**Step 3: Create .gitignore**

```gitignore
# Environment
.env
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# Data
data/
*.csv
*.db

# Streamlit
.streamlit/secrets.toml
```

**Step 4: Create README.md**

```markdown
# ETF Data Collection and Management System

A production-ready system for collecting and managing ETF data from Tushare Pro API.

## Features

- Fetch ETF basic information and share size data
- Full and incremental data updates
- Supabase PostgreSQL storage with SSL
- Rate limiting and retry logic
- Streamlit dashboard for monitoring
- Docker containerization
- Automated updates via GitHub Actions

## Setup

1. Clone repository
2. Copy `.env.example` to `.env` and configure
3. Install dependencies: `pip install -r requirements.txt`
4. Initialize database: `python src/init_db.py`
5. Run collector: `python src/main.py`
6. Launch dashboard: `streamlit run app.py`

## Environment Variables

See `.env.example` for required configuration.

## Deployment

Deploy to Streamlit Cloud with GitHub Actions for automated data updates.
```

**Step 5: Create config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for ETF data collection system"""

    # Tushare Configuration
    TUSHARE_TOKEN = os.getenv('TUSHARE_TOKEN')

    # Database Configuration
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_NAME = os.getenv('DB_NAME', 'postgres')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_SSLMODE = os.getenv('DB_SSLMODE', 'require')

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
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?sslmode={self.DB_SSLMODE}"

    def validate(self):
        """Validate required configuration"""
        required = ['TUSHARE_TOKEN', 'DB_HOST', 'DB_PASSWORD']
        missing = [key for key in required if not getattr(self, key)]
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")
```

**Step 6: Verify files created**

Run: `ls -la`
Expected: See requirements.txt, .env.example, .gitignore, README.md, config.py

---

## Task 2: Database Models and Schema

**Files:**
- Create: `src/models.py`
- Create: `src/database.py`
- Create: `src/init_db.py`
- Create: `sql/schema.sql`

**Step 1: Create src/models.py**

```python
from sqlalchemy import Column, String, Date, Float, Integer, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ETFBasic(Base):
    """ETF基础信息表"""
    __tablename__ = 'etf_basic'

    ts_code = Column(String(20), primary_key=True, comment='TS代码')
    name = Column(String(100), comment='简称')
    management = Column(String(100), comment='管理人')
    custodian = Column(String(100), comment='托管人')
    fund_type = Column(String(50), comment='投资类型')
    found_date = Column(Date, comment='成立日期')
    due_date = Column(Date, comment='到期日期')
    list_date = Column(Date, comment='上市时间')
    issue_date = Column(Date, comment='发行日期')
    delist_date = Column(Date, comment='退市日期')
    issue_amount = Column(Float, comment='发行份额(亿)')
    market = Column(String(10), comment='市场')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    def __repr__(self):
        return f"<ETFBasic(ts_code='{self.ts_code}', name='{self.name}')>"


class ETFShareSize(Base):
    """ETF份额规模表"""
    __tablename__ = 'etf_share_size'
    __table_args__ = (
        Index('idx_ts_code_trade_date', 'ts_code', 'trade_date', unique=True),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), index=True, comment='TS代码')
    trade_date = Column(Date, index=True, comment='交易日期')
    fund_share = Column(Float, comment='基金份额(亿份)')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    def __repr__(self):
        return f"<ETFShareSize(ts_code='{self.ts_code}', trade_date='{self.trade_date}')>"
```

**Step 2: Create src/database.py**

```python
import logging
from sqlalchemy import create_engine
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

    def connect(self):
        """Initialize database connection"""
        try:
            self.engine = create_engine(
                self.config.database_url,
                poolclass=NullPool,
                echo=False
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
```

**Step 3: Create src/init_db.py**

```python
import logging
from config import Config
from src.database import Database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Initialize database tables"""
    config = Config()
    config.validate()

    db = Database(config)
    db.connect()
    db.create_tables()
    db.close()

    print("Database initialized successfully!")

if __name__ == "__main__":
    main()
```

**Step 4: Create sql/schema.sql (for reference)**

```sql
-- ETF基础信息表
CREATE TABLE IF NOT EXISTS etf_basic (
    ts_code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    management VARCHAR(100),
    custodian VARCHAR(100),
    fund_type VARCHAR(50),
    found_date DATE,
    due_date DATE,
    list_date DATE,
    issue_date DATE,
    delist_date DATE,
    issue_amount FLOAT,
    market VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ETF份额规模表
CREATE TABLE IF NOT EXISTS etf_share_size (
    id SERIAL PRIMARY KEY,
    ts_code VARCHAR(20),
    trade_date DATE,
    fund_share FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ts_code, trade_date)
);

CREATE INDEX idx_etf_share_ts_code ON etf_share_size(ts_code);
CREATE INDEX idx_etf_share_trade_date ON etf_share_size(trade_date);
```

**Step 5: Create src/__init__.py**

```python
# Empty file to make src a package
```

**Step 6: Verify database module structure**

Run: `ls -la src/`
Expected: See models.py, database.py, init_db.py, __init__.py

---

## Task 3: Tushare API Client with Rate Limiting

**Files:**

- Create: `src/tushare_client.py`
- Create: `src/logger.py`

**Step 1: Create src/logger.py**

```python
import logging
import os
from config import Config

def setup_logger(name: str = __name__) -> logging.Logger:
    """Setup logger with file and console handlers"""
    config = Config()

    # Create logs directory if not exists
    log_dir = os.path.dirname(config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)

    # File handler
    file_handler = logging.FileHandler(config.LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
```

**Step 2: Create src/tushare_client.py**

```python
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
```

**Step 3: Verify Tushare client created**

Run: `ls -la src/`
Expected: See tushare_client.py and logger.py

---

## Task 4: Data Collectors with Incremental Update Logic

**Files:**

- Create: `src/collectors/base_collector.py`
- Create: `src/collectors/etf_basic_collector.py`
- Create: `src/collectors/etf_share_collector.py`
- Create: `src/collectors/__init__.py`

**Step 1: Create src/collectors/__init__.py**

```python
from .etf_basic_collector import ETFBasicCollector
from .etf_share_collector import ETFShareCollector

__all__ = ['ETFBasicCollector', 'ETFShareCollector']
```

**Step 2: Create src/collectors/base_collector.py**

```python
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
```

**Step 3: Create src/collectors/etf_basic_collector.py**

```python
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

            # Save to database
            with self.db.get_session() as session:
                # Delete existing records
                session.query(ETFBasic).delete()

                # Insert new records
                records = df.to_dict('records')
                for record in records:
                    etf = ETFBasic(**record)
                    session.add(etf)

                logger.info(f"Saved {len(records)} ETF basic records")

        except Exception as e:
            logger.error(f"Failed to collect ETF basic info: {e}")
            raise

    def collect_incremental(self):
        """增量采集 - ETF基础信息通常不需要增量更新"""
        logger.info("ETF basic info uses full update only")
        self.collect_full()
```

**Step 4: Create src/collectors/etf_share_collector.py**

```python
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
                        records = df.to_dict('records')
                        for record in records:
                            share = ETFShareSize(**record)
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
                        records = df.to_dict('records')
                        for record in records:
                            share = ETFShareSize(**record)
                            session.merge(share)

                        total_records += len(records)

                except Exception as e:
                    logger.error(f"Failed to collect {ts_code}: {e}")
                    continue

            logger.info(f"Incremental collection completed. New records: {total_records}")

        except Exception as e:
            logger.error(f"Failed incremental collection: {e}")
            raise
```

**Step 5: Verify collectors created**

Run: `ls -la src/collectors/`
Expected: See __init__.py, base_collector.py, etf_basic_collector.py, etf_share_collector.py

---

## Task 5: Main Script and CLI

**Files:**

- Create: `src/main.py`

**Step 1: Create src/main.py**

```python
import argparse
from config import Config
from src.database import Database
from src.tushare_client import TushareClient
from src.collectors import ETFBasicCollector, ETFShareCollector
from src.logger import setup_logger

logger = setup_logger(__name__)

def main():
    """Main entry point for ETF data collection"""
    parser = argparse.ArgumentParser(description='ETF Data Collection System')
    parser.add_argument(
        '--mode',
        choices=['full', 'incremental'],
        default='incremental',
        help='Collection mode: full or incremental'
    )
    parser.add_argument(
        '--data-type',
        choices=['basic', 'share', 'all'],
        default='all',
        help='Data type to collect: basic, share, or all'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        default='20200101',
        help='Start date for full collection (YYYYMMDD)'
    )

    args = parser.parse_args()

    try:
        # Initialize configuration
        config = Config()
        config.validate()
        logger.info("Configuration validated")

        # Initialize database
        db = Database(config)
        db.connect()
        logger.info("Database connected")

        # Initialize Tushare client
        client = TushareClient(config)

        # Collect ETF basic info
        if args.data_type in ['basic', 'all']:
            logger.info("Collecting ETF basic information")
            basic_collector = ETFBasicCollector(db, client)

            if args.mode == 'full':
                basic_collector.collect_full()
            else:
                basic_collector.collect_incremental()

        # Collect ETF share size
        if args.data_type in ['share', 'all']:
            logger.info("Collecting ETF share size data")
            share_collector = ETFShareCollector(db, client)

            if args.mode == 'full':
                share_collector.collect_full(start_date=args.start_date)
            else:
                share_collector.collect_incremental()

        logger.info("Data collection completed successfully")

    except Exception as e:
        logger.error(f"Data collection failed: {e}")
        raise
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main()
```

**Step 2: Test main script structure**

Run: `python src/main.py --help`
Expected: See help message with arguments

---

## Task 6: Streamlit Dashboard

**Files:**

- Create: `app.py`
- Create: `.streamlit/config.toml`

**Step 1: Create app.py**

```python
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from config import Config
from src.database import Database
from src.models import ETFBasic, ETFShareSize
from sqlalchemy import func

st.set_page_config(
    page_title="ETF Data Dashboard",
    page_icon="📊",
    layout="wide"
)

@st.cache_resource
def get_database():
    """Initialize database connection"""
    config = Config()
    db = Database(config)
    db.connect()
    return db

def get_etf_count(db):
    """Get total ETF count"""
    with db.get_session() as session:
        return session.query(func.count(ETFBasic.ts_code)).scalar()

def get_latest_update(db):
    """Get latest update date"""
    with db.get_session() as session:
        result = session.query(func.max(ETFShareSize.trade_date)).scalar()
        return result if result else None

def get_etf_basic_data(db, limit=100):
    """Get ETF basic information"""
    with db.get_session() as session:
        etfs = session.query(ETFBasic).limit(limit).all()
        data = [{
            'TS代码': etf.ts_code,
            '名称': etf.name,
            '管理人': etf.management,
            '类型': etf.fund_type,
            '上市日期': etf.list_date,
            '发行份额': etf.issue_amount
        } for etf in etfs]
        return pd.DataFrame(data)

def get_etf_share_data(db, ts_code, days=30):
    """Get ETF share size data"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    with db.get_session() as session:
        shares = session.query(ETFShareSize).filter(
            ETFShareSize.ts_code == ts_code,
            ETFShareSize.trade_date >= start_date
        ).order_by(ETFShareSize.trade_date).all()

        data = [{
            '交易日期': share.trade_date,
            '份额(亿份)': share.fund_share
        } for share in shares]
        return pd.DataFrame(data)

def main():
    st.title("📊 ETF数据管理系统")
    st.markdown("---")

    try:
        db = get_database()

        # Metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            etf_count = get_etf_count(db)
            st.metric("ETF总数", f"{etf_count:,}")

        with col2:
            latest_date = get_latest_update(db)
            if latest_date:
                st.metric("最新数据日期", latest_date.strftime('%Y-%m-%d'))
            else:
                st.metric("最新数据日期", "无数据")

        with col3:
            st.metric("数据库状态", "✅ 已连接")

        st.markdown("---")

        # ETF Basic Info
        st.subheader("ETF基础信息")
        df_basic = get_etf_basic_data(db, limit=100)
        st.dataframe(df_basic, use_container_width=True)

        st.markdown("---")

        # ETF Share Size Chart
        st.subheader("ETF份额规模趋势")

        etf_codes = df_basic['TS代码'].tolist()
        selected_etf = st.selectbox("选择ETF", etf_codes)

        if selected_etf:
            days = st.slider("显示天数", 7, 90, 30)
            df_share = get_etf_share_data(db, selected_etf, days)

            if not df_share.empty:
                st.line_chart(df_share.set_index('交易日期'))
            else:
                st.info("该ETF暂无份额数据")

    except Exception as e:
        st.error(f"数据库连接失败: {e}")
        st.info("请检查环境变量配置")

if __name__ == "__main__":
    main()
```

**Step 2: Create .streamlit/config.toml**

```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
port = 8501
```

**Step 3: Test Streamlit app locally**

Run: `streamlit run app.py`
Expected: App opens in browser

---

## Task 7: Docker Configuration

**Files:**

- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

**Step 1: Create Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "src/main.py", "--mode", "incremental"]
```

**Step 2: Create docker-compose.yml**

```yaml
version: '3.8'

services:
  etf-collector:
    build: .
    container_name: etf-collector
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
    command: python src/main.py --mode incremental --data-type all
    restart: unless-stopped

  streamlit-app:
    build: .
    container_name: etf-dashboard
    env_file:
      - .env
    ports:
      - "8501:8501"
    volumes:
      - ./logs:/app/logs
    command: streamlit run app.py
    restart: unless-stopped
```

**Step 3: Create .dockerignore**

```dockerignore
.env
.git
.gitignore
__pycache__
*.pyc
*.pyo
*.pyd
.Python
venv/
logs/
data/
.vscode/
.idea/
*.md
docs/
```

**Step 4: Test Docker build**

Run: `docker build -t etf-collector .`
Expected: Image builds successfully

---

## Task 8: GitHub Actions for Automated Updates

**Files:**

- Create: `.github/workflows/daily-update.yml`
- Create: `.github/workflows/weekly-full-update.yml`

**Step 1: Create .github/workflows/daily-update.yml**

```yaml
name: Daily ETF Data Update

on:
  schedule:
    # Run at 18:00 UTC (02:00 Beijing Time) every weekday
    - cron: '0 18 * * 1-5'
  workflow_dispatch:  # Allow manual trigger

jobs:
  update-data:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run incremental update
        env:
          TUSHARE_TOKEN: ${{ secrets.TUSHARE_TOKEN }}
          DB_HOST: ${{ secrets.DB_HOST }}
          DB_PORT: ${{ secrets.DB_PORT }}
          DB_NAME: ${{ secrets.DB_NAME }}
          DB_USER: ${{ secrets.DB_USER }}
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
          DB_SSLMODE: require
        run: |
          python src/main.py --mode incremental --data-type all

      - name: Upload logs
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: update-logs
          path: logs/
          retention-days: 7
```

**Step 2: Create .github/workflows/weekly-full-update.yml**

```yaml
name: Weekly Full ETF Data Update

on:
  schedule:
    # Run at 02:00 UTC every Sunday
    - cron: '0 2 * * 0'
  workflow_dispatch:

jobs:
  full-update:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run full update
        env:
          TUSHARE_TOKEN: ${{ secrets.TUSHARE_TOKEN }}
          DB_HOST: ${{ secrets.DB_HOST }}
          DB_PORT: ${{ secrets.DB_PORT }}
          DB_NAME: ${{ secrets.DB_NAME }}
          DB_USER: ${{ secrets.DB_USER }}
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
          DB_SSLMODE: require
        run: |
          python src/main.py --mode full --data-type all --start-date 20200101

      - name: Upload logs
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: full-update-logs
          path: logs/
          retention-days: 30
```

**Step 3: Verify GitHub Actions files**

Run: `ls -la .github/workflows/`
Expected: See daily-update.yml and weekly-full-update.yml

---

## Task 9: Documentation and Deployment Guide

**Files:**

- Create: `docs/DEPLOYMENT.md`
- Create: `docs/API.md`

**Step 1: Create docs/DEPLOYMENT.md**

```markdown
# Deployment Guide

## Prerequisites

1. Tushare Pro account with token (积分要求: ETF基础信息8000分, 份额规模8000分)
2. Supabase account with PostgreSQL database
3. GitHub account (for automated updates)
4. Streamlit Cloud account (for dashboard deployment)

## Local Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd trade
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values.

### 5. Initialize Database

```bash
python src/init_db.py
```

### 6. Run Data Collection

Full update:
```bash
python src/main.py --mode full --data-type all --start-date 20200101
```

Incremental update:
```bash
python src/main.py --mode incremental --data-type all
```

### 7. Launch Dashboard

```bash
streamlit run app.py
```

## Docker Deployment

### Build and Run

```bash
docker-compose up -d
```

### View Logs

```bash
docker-compose logs -f
```

### Stop Services

```bash
docker-compose down
```

## Streamlit Cloud Deployment

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repo-url>
git push -u origin main
```

### 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your repository
4. Set main file path: `app.py`
5. Add secrets in Advanced settings:

```toml
TUSHARE_TOKEN = "your_token"
DB_HOST = "your_host.supabase.co"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "your_password"
DB_SSLMODE = "require"
```

6. Click "Deploy"

## GitHub Actions Setup

### 1. Add Repository Secrets

Go to Settings > Secrets and variables > Actions, add:

- `TUSHARE_TOKEN`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

### 2. Enable Workflows

Workflows will run automatically:
- Daily incremental update: Weekdays at 02:00 Beijing Time
- Weekly full update: Sundays at 10:00 Beijing Time

### 3. Manual Trigger

Go to Actions tab, select workflow, click "Run workflow"

## Monitoring

### Check Logs

Local:
```bash
tail -f logs/etf_collector.log
```

Docker:
```bash
docker-compose logs -f etf-collector
```

### Database Queries

```sql
-- Check ETF count
SELECT COUNT(*) FROM etf_basic;

-- Check latest data date
SELECT MAX(trade_date) FROM etf_share_size;

-- Check data completeness
SELECT ts_code, COUNT(*) as record_count
FROM etf_share_size
GROUP BY ts_code
ORDER BY record_count DESC;
```

## Troubleshooting

### Tushare API Rate Limiting

If you encounter rate limiting errors:
1. Increase `API_CALL_INTERVAL` in config.py
2. Reduce batch size in collectors
3. Check your Tushare account points

### Database Connection Issues

1. Verify SSL mode is set to `require`
2. Check firewall rules in Supabase
3. Verify credentials in .env file

### GitHub Actions Failures

1. Check workflow logs in Actions tab
2. Verify all secrets are set correctly
3. Ensure repository has necessary permissions
```

**Step 2: Create docs/API.md**

```markdown
# API Reference

## Tushare API Interfaces Used

### 1. fund_basic - ETF基础信息

**积分要求:** 8000分

**接口:** `pro.fund_basic(market='E')`

**返回字段:**
- ts_code: TS代码
- name: 简称
- management: 管理人
- custodian: 托管人
- fund_type: 投资类型
- found_date: 成立日期
- list_date: 上市时间
- issue_amount: 发行份额

### 2. fund_share - ETF份额规模

**积分要求:** 8000分

**接口:** `pro.fund_share(ts_code, start_date, end_date)`

**参数:**
- ts_code: ETF代码
- start_date: 开始日期 (YYYYMMDD)
- end_date: 结束日期 (YYYYMMDD)

**返回字段:**
- ts_code: TS代码
- trade_date: 交易日期
- fund_share: 基金份额(亿份)

### 3. trade_cal - 交易日历

**积分要求:** 2000分

**接口:** `pro.trade_cal(exchange, start_date, end_date, is_open)`

**参数:**
- exchange: 交易所 (SSE/SZSE)
- is_open: 是否交易 (1=是)

## Database Schema

### etf_basic Table

```sql
CREATE TABLE etf_basic (
    ts_code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100),
    management VARCHAR(100),
    custodian VARCHAR(100),
    fund_type VARCHAR(50),
    found_date DATE,
    due_date DATE,
    list_date DATE,
    issue_date DATE,
    delist_date DATE,
    issue_amount FLOAT,
    market VARCHAR(10),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### etf_share_size Table

```sql
CREATE TABLE etf_share_size (
    id SERIAL PRIMARY KEY,
    ts_code VARCHAR(20),
    trade_date DATE,
    fund_share FLOAT,
    created_at TIMESTAMP,
    UNIQUE(ts_code, trade_date)
);
```

## Python API

### Configuration

```python
from config import Config

config = Config()
config.validate()
```

### Database Operations

```python
from src.database import Database

db = Database(config)
db.connect()

with db.get_session() as session:
    # Your database operations
    pass

db.close()
```

### Data Collection

```python
from src.tushare_client import TushareClient
from src.collectors import ETFBasicCollector, ETFShareCollector

client = TushareClient(config)

# Collect ETF basic info
basic_collector = ETFBasicCollector(db, client)
basic_collector.collect_full()

# Collect ETF share size
share_collector = ETFShareCollector(db, client)
share_collector.collect_incremental()
```
```

**Step 3: Verify documentation created**

Run: `ls -la docs/`
Expected: See DEPLOYMENT.md and API.md

---

## Task 10: Final Testing and Verification

**Step 1: Run full test suite**

```bash
# Test configuration
python -c "from config import Config; c = Config(); c.validate(); print('Config OK')"

# Test database connection
python src/init_db.py

# Test data collection (dry run with small dataset)
python src/main.py --mode full --data-type basic

# Test Streamlit app
streamlit run app.py
```

**Step 2: Verify all files exist**

Run: `find . -type f -name "*.py" -o -name "*.yml" -o -name "*.md" | sort`
Expected: See all created files

**Step 3: Create final README update**

Update README.md with complete usage instructions and examples.

---

## Execution Complete

All tasks completed. The ETF data collection system is ready for deployment with:

- ✅ OOP architecture with separate modules
- ✅ Full and incremental update support
- ✅ Supabase PostgreSQL with SSL
- ✅ Rate limiting and retry logic
- ✅ Comprehensive logging
- ✅ Streamlit dashboard
- ✅ Docker containerization
- ✅ GitHub Actions automation
- ✅ Complete documentation
