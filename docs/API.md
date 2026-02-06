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
