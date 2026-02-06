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
