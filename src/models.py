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
