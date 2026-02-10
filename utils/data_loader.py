import streamlit as st
from sqlalchemy import func, or_
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from config import Config
from src.database import Database
from src.models import ETFBasic, ETFShareSize


@st.cache_resource
def get_database():
    """Initialize and cache database connection

    Returns:
        Database: Cached database instance
    """
    config = Config()
    db = Database(config)
    db.connect()
    return db


def fund_to_dict(fund: ETFBasic) -> Dict[str, Any]:
    """Convert ETFBasic model to dictionary

    Args:
        fund: ETFBasic model instance

    Returns:
        Dictionary with fund data
    """
    return {
        'ts_code': fund.ts_code,
        'name': fund.name,
        'management': fund.management,
        'custodian': fund.custodian,
        'fund_type': fund.fund_type,
        'found_date': fund.found_date,
        'due_date': fund.due_date,
        'list_date': fund.list_date,
        'issue_date': fund.issue_date,
        'delist_date': fund.delist_date,
        'issue_amount': fund.issue_amount,
        'market': fund.market,
        'created_at': fund.created_at,
        'updated_at': fund.updated_at
    }


@st.cache_data(ttl=300)
def get_fund_count() -> int:
    """Get total fund count (cached for 5 minutes)

    Returns:
        Total number of active (non-delisted) funds in database
    """
    db = get_database()
    with db.get_session() as session:
        return session.query(func.count(ETFBasic.ts_code)).filter(
            ETFBasic.delist_date.is_(None)
        ).scalar()


@st.cache_data(ttl=300)
def get_latest_update() -> Optional[datetime]:
    """Get latest data date (cached for 5 minutes)

    Returns:
        Latest trade date from share size data, or None if no data
    """
    db = get_database()
    with db.get_session() as session:
        result = session.query(func.max(ETFShareSize.trade_date)).scalar()
        return result if result else None


@st.cache_data(ttl=300)
def load_fund_list(
    filters: Optional[Dict[str, Any]] = None,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """Load paginated fund list with filters (cached for 5 minutes)

    Args:
        filters: Dictionary of filter criteria (fund_type, market, etc.)
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Dictionary with 'funds' list, 'total' count, and 'pages' count
    """
    db = get_database()
    with db.get_session() as session:
        query = session.query(ETFBasic)

        # Filter out delisted funds
        query = query.filter(ETFBasic.delist_date.is_(None))

        # Apply filters if provided
        if filters:
            if filters.get('fund_type'):
                query = query.filter(ETFBasic.fund_type == filters['fund_type'])
            if filters.get('market'):
                query = query.filter(ETFBasic.market == filters['market'])
            if filters.get('management'):
                query = query.filter(ETFBasic.management == filters['management'])

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        funds = query.order_by(ETFBasic.ts_code).offset(offset).limit(page_size).all()

        # Convert to dictionaries
        fund_list = [fund_to_dict(fund) for fund in funds]

        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size

        return {
            'funds': fund_list,
            'total': total,
            'pages': total_pages
        }


@st.cache_data(ttl=300)
def load_fund_detail(ts_code: str) -> Optional[Dict[str, Any]]:
    """Load single fund details (cached for 5 minutes)

    Args:
        ts_code: Fund TS code

    Returns:
        Dictionary with fund data, or None if not found
    """
    db = get_database()
    with db.get_session() as session:
        fund = session.query(ETFBasic).filter(ETFBasic.ts_code == ts_code).first()
        return fund_to_dict(fund) if fund else None


@st.cache_data(ttl=3600)
def load_share_size_data(ts_code: str, days: int = 30) -> List[Dict[str, Any]]:
    """Load share size data (cached for 1 hour)

    Args:
        ts_code: Fund TS code
        days: Number of days to look back

    Returns:
        List of dictionaries with trade_date and fund_share
    """
    db = get_database()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    with db.get_session() as session:
        shares = session.query(ETFShareSize).filter(
            ETFShareSize.ts_code == ts_code,
            ETFShareSize.trade_date >= start_date
        ).order_by(ETFShareSize.trade_date).all()

        return [{
            'trade_date': share.trade_date,
            'fund_share': share.fund_share
        } for share in shares]


def search_funds(query: str, all_funds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Search funds by code/name/manager (case-insensitive partial matching)

    Args:
        query: Search query string
        all_funds: List of all fund dictionaries to search

    Returns:
        Filtered list of funds matching the query
    """
    if not query:
        return all_funds

    query_lower = query.lower()
    results = []

    for fund in all_funds:
        # Search in ts_code, name, and management fields
        if (query_lower in (fund.get('ts_code') or '').lower() or
            query_lower in (fund.get('name') or '').lower() or
            query_lower in (fund.get('management') or '').lower()):
            results.append(fund)

    return results
