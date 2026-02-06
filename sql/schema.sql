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
