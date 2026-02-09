# Fund Data Display Frontend Design

**Date:** 2026-02-09
**Status:** Approved
**Technology Stack:** Streamlit + Plotly + PostgreSQL

## Overview

Design for a comprehensive fund data display system that shows fund information, net value trends, and supports search functionality. Built as a Streamlit multi-page application with interactive Plotly charts.

## Requirements

### Functional Requirements
1. Display fund list with search and filter capabilities
2. Show detailed fund information including:
   - Basic information (code, name, manager, type, dates)
   - Net Asset Value (NAV) trends
   - Share size trends
   - Daily OHLC data
3. Interactive charts with zoom, pan, and time range selection
4. Support for future expansion with additional pages
5. Real-time search across fund code, name, and manager

### Non-Functional Requirements
1. Fast page load times (<2 seconds)
2. Responsive design for different screen sizes
3. Graceful error handling and loading states
4. Data caching to reduce database load
5. Professional financial UI aesthetic

## Architecture

### Project Structure

```
trade/
├── app.py                          # Main entry (redirect to pages)
├── pages/
│   ├── 1_📊_基金列表.py            # Fund list with search
│   ├── 2_📈_基金详情.py            # Fund details & charts
│   ├── 3_📉_数据分析.py            # Future: Analytics page
│   └── 4_⚙️_系统设置.py            # Future: Settings page
├── components/
│   ├── __init__.py
│   ├── fund_card.py               # Reusable fund card component
│   ├── nav_chart.py               # NAV trend chart component
│   └── search_bar.py              # Search component
└── utils/
    ├── __init__.py
    ├── data_loader.py             # Data fetching logic
    └── chart_builder.py           # Plotly chart builders
```

### Design Principles

1. **Modular Components**: Reusable UI components for consistency across pages
2. **Separation of Concerns**: Data logic separated from UI rendering
3. **Scalability**: Easy to add new pages for future features
4. **Performance**: Aggressive caching strategies for database queries

### Navigation Flow

- Streamlit's native multi-page app with sidebar navigation
- Each page is self-contained but shares common components
- State management via `st.session_state` for cross-page data sharing
- URL-based routing handled automatically by Streamlit

## Page Designs

### Page 1: 📊 基金列表 (Fund List)

**Purpose:** Main landing page for browsing and searching funds

**Features:**
- **Metrics Row** (top): Total funds, latest data date, database status
- **Search Bar**: Real-time search by fund code, name, or manager
- **Filter Panel** (sidebar):
  - Fund type dropdown (股票型, 债券型, 混合型, etc.)
  - Market selector (沪市, 深市, 全部)
  - Date range picker (listing date)
- **Fund Cards Grid**: Responsive grid layout (1-4 columns based on screen width)
  - Each card displays: code, name, manager, type, listing date, issue amount
  - Click card to navigate to detail page
  - Color-coded by fund type
- **Pagination**: Show 20-50 funds per page with page number selector

**Data Loading:**
```python
@st.cache_data(ttl=300)  # 5 minutes cache
def load_fund_list(filters, page, page_size):
    # Query database with filters
    # Return paginated results
```

**Search Implementation:**
- Execute on cached fund list for instant results
- Support partial matching (fuzzy search)
- Highlight matching terms in results

### Page 2: 📈 基金详情 (Fund Details)

**Purpose:** Deep dive into individual fund with comprehensive data visualization

**Layout:**
- **Fund Header**: Large display of fund name, code, and key metrics
  - Current NAV, change %, total assets, manager
- **Tab Navigation** within page:
  1. **净值走势 (NAV Trend)**: Interactive line chart
  2. **份额规模 (Share Size)**: Share size trend chart
  3. **日线行情 (Daily Data)**: OHLC candlestick chart
  4. **基本信息 (Basic Info)**: Detailed fund information table

**Chart Features** (Plotly):
- Time range selector buttons (1M, 3M, 6M, 1Y, All)
- Zoom and pan controls
- Crosshair cursor with hover tooltips
- Export chart as PNG
- Multiple series comparison (compare with other funds)

**Data Loading:**
```python
@st.cache_data(ttl=3600)  # 1 hour cache for historical data
def load_nav_data(ts_code, start_date, end_date):
    # Query NAV data from database
    # Return time series data
```

### Future Pages

**Page 3: 📉 数据分析 (Analytics)**
- Portfolio analysis
- Performance comparison
- Statistical metrics

**Page 4: ⚙️ 系统设置 (Settings)**
- Data refresh controls
- Display preferences
- Export options

## Component Design

### 1. Fund Card Component

**File:** `components/fund_card.py`

**Purpose:** Reusable card for displaying fund summary

**Props:**
- `fund_data`: Dictionary with fund information
- `clickable`: Boolean for navigation behavior

**Features:**
- Visual hierarchy: Code (large) > Name > Manager
- Color coding by fund type
- Hover effect with shadow
- Click to navigate to detail page

**Implementation:**
```python
def render_fund_card(fund_data, clickable=True):
    with st.container():
        st.markdown(f"### {fund_data['ts_code']}")
        st.write(f"**{fund_data['name']}**")
        st.caption(f"管理人: {fund_data['management']}")
        if clickable:
            if st.button("查看详情", key=fund_data['ts_code']):
                st.session_state['selected_fund'] = fund_data['ts_code']
                st.switch_page("pages/2_📈_基金详情.py")
```

### 2. NAV Chart Component

**File:** `components/nav_chart.py`

**Purpose:** Interactive Plotly chart for NAV trends

**Props:**
- `nav_data`: DataFrame with date and NAV columns
- `chart_type`: 'line' or 'area'
- `show_range_selector`: Boolean

**Features:**
- Time range selector buttons
- Crosshair cursor
- Tooltip showing date, NAV, change%
- Comparison mode (overlay multiple funds)

**Implementation:**
```python
import plotly.graph_objects as go

def render_nav_chart(nav_data, chart_type='line', show_range_selector=True):
    fig = go.Figure()

    if chart_type == 'line':
        fig.add_trace(go.Scatter(
            x=nav_data['date'],
            y=nav_data['nav'],
            mode='lines',
            name='单位净值'
        ))

    if show_range_selector:
        fig.update_xaxes(
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1M", step="month"),
                    dict(count=3, label="3M", step="month"),
                    dict(count=6, label="6M", step="month"),
                    dict(count=1, label="1Y", step="year"),
                    dict(step="all", label="All")
                ]
            )
        )

    st.plotly_chart(fig, use_container_width=True)
```

### 3. Search Bar Component

**File:** `components/search_bar.py`

**Purpose:** Real-time search with debouncing

**Features:**
- Search by code, name, or manager
- Shows result count
- Clear button
- Debouncing to avoid excessive queries

**Implementation:**
```python
def render_search_bar(placeholder="搜索基金..."):
    col1, col2 = st.columns([4, 1])

    with col1:
        query = st.text_input(
            "search",
            placeholder=placeholder,
            label_visibility="collapsed"
        )

    with col2:
        if st.button("清除"):
            st.session_state['search_query'] = ""
            st.rerun()

    return query
```

## Data Layer Design

### File: `utils/data_loader.py`

**Purpose:** Centralized data fetching with caching

**Key Functions:**

1. **load_fund_list(filters, page, page_size)**
   - Returns paginated fund list with filters applied
   - Cache TTL: 5 minutes
   - Supports filtering by type, market, date range

2. **load_fund_detail(ts_code)**
   - Returns complete fund information for single fund
   - Cache TTL: 5 minutes
   - Includes all basic info fields

3. **load_nav_data(ts_code, start_date, end_date)**
   - Returns NAV time series data
   - Cache TTL: 1 hour (historical data rarely changes)
   - Optimized query with date range filter

4. **load_daily_data(ts_code, start_date, end_date)**
   - Returns OHLC daily data
   - Cache TTL: 1 hour
   - Includes volume and turnover

5. **search_funds(query)**
   - Full-text search across code, name, manager
   - No cache (executes on cached fund list)
   - Returns matching funds with relevance score

**Implementation Pattern:**
```python
import streamlit as st
from src.database import Database
from config import Config

@st.cache_resource
def get_database():
    config = Config()
    db = Database(config)
    db.connect()
    return db

@st.cache_data(ttl=300)
def load_fund_list(filters=None, page=1, page_size=20):
    db = get_database()
    with db.get_session() as session:
        query = session.query(ETFBasic)

        # Apply filters
        if filters:
            if filters.get('fund_type'):
                query = query.filter(ETFBasic.fund_type == filters['fund_type'])
            if filters.get('market'):
                query = query.filter(ETFBasic.market == filters['market'])

        # Pagination
        offset = (page - 1) * page_size
        funds = query.offset(offset).limit(page_size).all()

        return [fund_to_dict(f) for f in funds]
```

## Database Schema Updates

### New Models Required

**1. FundNav Model** (for NAV data)
```python
class FundNav(Base):
    __tablename__ = 'fund_nav'
    __table_args__ = (
        Index('idx_ts_code_nav_date', 'ts_code', 'nav_date', unique=True),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), index=True, comment='TS代码')
    nav_date = Column(Date, index=True, comment='净值日期')
    unit_nav = Column(Float, comment='单位净值')
    accum_nav = Column(Float, comment='累计净值')
    accum_div = Column(Float, comment='累计分红')
    net_asset = Column(Float, comment='资产净值')
    total_netasset = Column(Float, comment='合计资产净值')
    adj_nav = Column(Float, comment='复权单位净值')
    created_at = Column(DateTime, default=datetime.now)
```

**2. FundDaily Model** (for OHLC data)
```python
class FundDaily(Base):
    __tablename__ = 'fund_daily'
    __table_args__ = (
        Index('idx_ts_code_trade_date', 'ts_code', 'trade_date', unique=True),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), index=True, comment='TS代码')
    trade_date = Column(Date, index=True, comment='交易日期')
    open = Column(Float, comment='开盘价')
    high = Column(Float, comment='最高价')
    low = Column(Float, comment='最低价')
    close = Column(Float, comment='收盘价')
    pre_close = Column(Float, comment='昨收价')
    change = Column(Float, comment='涨跌额')
    pct_chg = Column(Float, comment='涨跌幅')
    vol = Column(Float, comment='成交量(手)')
    amount = Column(Float, comment='成交额(千元)')
    created_at = Column(DateTime, default=datetime.now)
```

### Tushare Client Extensions

**File:** `src/tushare_client.py`

**New Methods:**

```python
@retry(tries=3, delay=1, backoff=2, logger=logger)
def get_fund_nav(
    self,
    ts_code: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """获取基金净值数据"""
    try:
        self._rate_limit()
        df = self.pro.fund_nav(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        )
        logger.info(f"Fetched {len(df)} fund NAV records")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch fund NAV: {e}")
        raise

@retry(tries=3, delay=1, backoff=2, logger=logger)
def get_fund_daily(
    self,
    ts_code: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """获取基金日线行情"""
    try:
        self._rate_limit()
        df = self.pro.fund_daily(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        )
        logger.info(f"Fetched {len(df)} fund daily records")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch fund daily data: {e}")
        raise
```

## UX & Styling

### Color Scheme (Financial Theme)

- **Primary**: `#1f77b4` (Blue) - Trust, stability
- **Success**: `#2ca02c` (Green) - Positive returns
- **Warning**: `#ff7f0e` (Orange) - Caution
- **Danger**: `#d62728` (Red) - Negative returns
- **Background**: `#f8f9fa` (Light gray) - Clean, professional
- **Text**: `#212529` (Dark gray) - High contrast

### Loading States

1. **Skeleton Loaders**: For fund cards while data loads
2. **Progress Bars**: For long-running queries (>2 seconds)
3. **Spinners**: For chart rendering
4. **Empty States**: "No data available" with helpful messages

### Error Handling

1. **Database Connection Errors**:
   - Show user-friendly message
   - Provide retry button
   - Log technical details for debugging

2. **Data Not Found**:
   - Clear message: "该基金暂无数据"
   - Suggest alternative actions

3. **API Rate Limits**:
   - Show waiting message with countdown
   - Automatic retry after cooldown

### Responsive Design

- **Desktop** (>1200px): 4-column fund card grid
- **Tablet** (768-1200px): 2-column grid
- **Mobile** (<768px): 1-column grid
- Charts automatically resize to container width
- Sidebar collapses on mobile

## Performance Optimization

### 1. Database Query Optimization

- **Indexes**: Already exist on `ts_code` and `trade_date`
- **Date Range Filters**: Always limit queries to specific date ranges
- **Pagination**: Load only visible page data (20-50 records)
- **Select Specific Columns**: Don't use `SELECT *` for large tables

### 2. Caching Strategy

| Data Type | Cache Method | TTL | Rationale |
|-----------|-------------|-----|-----------|
| Fund list | `@st.cache_data` | 5 min | Changes infrequently |
| Fund detail | `@st.cache_data` | 5 min | Basic info rarely updates |
| NAV data | `@st.cache_data` | 1 hour | Historical data is static |
| Daily data | `@st.cache_data` | 1 hour | Historical data is static |
| Database connection | `@st.cache_resource` | Forever | Reuse connection pool |

### 3. Lazy Loading

- Load charts only when tab is selected
- Defer loading of non-visible content
- Use `st.spinner()` for async operations

### 4. Code Splitting

- Separate page files prevent loading unused code
- Component files loaded only when needed
- Utility functions imported on-demand

## Implementation Roadmap

### Phase 1: Foundation (Priority: High)

**Tasks:**
1. Create directory structure (`pages/`, `components/`, `utils/`)
2. Update `requirements.txt` with new dependencies:
   - `plotly>=5.18.0`
   - `streamlit>=1.28.0`
3. Create `utils/data_loader.py` with all data fetching functions
4. Set up multi-page app structure

**Deliverables:**
- Project structure in place
- Data layer implemented and tested
- Dependencies installed

**Estimated Time:** 2-3 hours

### Phase 2: Main Pages (Priority: High)

**Tasks:**
1. Implement Fund List Page (`pages/1_📊_基金列表.py`):
   - Search and filter functionality
   - Fund cards grid with pagination
   - Navigation to detail page
2. Implement Fund Detail Page (`pages/2_📈_基金详情.py`):
   - Fund header with key metrics
   - Tab navigation (NAV, Share Size, Daily, Info)
   - Interactive Plotly charts

**Deliverables:**
- Two fully functional main pages
- Search and filter working
- Charts displaying correctly

**Estimated Time:** 3-4 hours

### Phase 3: Data Collection (Priority: Medium)

**Tasks:**
1. Add new models to `src/models.py`:
   - `FundNav` model
   - `FundDaily` model
2. Extend `src/tushare_client.py`:
   - Add `get_fund_nav()` method
   - Add `get_fund_daily()` method
3. Create collectors:
   - `src/collectors/fund_nav_collector.py`
   - `src/collectors/fund_daily_collector.py`
4. Run database migrations

**Deliverables:**
- New data models in database
- Data collection scripts working
- Historical data populated

**Estimated Time:** 2-3 hours

### Phase 4: Polish & Future Pages (Priority: Low)

**Tasks:**
1. UX enhancements:
   - Add loading states and error handling
   - Implement custom CSS styling
   - Add responsive design tweaks
2. Create placeholder pages:
   - Analytics page (basic structure)
   - Settings page (basic structure)
3. Testing and bug fixes

**Deliverables:**
- Polished UI with loading states
- Error handling in place
- Placeholder pages for future features

**Estimated Time:** 1-2 hours

### Total Estimated Timeline

**8-12 hours of development work**

## Dependencies

### New Python Packages

```txt
plotly>=5.18.0          # Interactive charts
streamlit>=1.28.0       # Multi-page app support
```

### Existing Dependencies (Already in project)

- `sqlalchemy` - Database ORM
- `pandas` - Data manipulation
- `tushare` - Data source API
- `psycopg2-binary` - PostgreSQL driver

## Testing Strategy

### Manual Testing Checklist

**Fund List Page:**
- [ ] Search by fund code works
- [ ] Search by fund name works
- [ ] Search by manager works
- [ ] Filter by fund type works
- [ ] Filter by market works
- [ ] Pagination works correctly
- [ ] Click card navigates to detail page

**Fund Detail Page:**
- [ ] Fund header displays correct information
- [ ] NAV chart loads and displays data
- [ ] Share size chart loads and displays data
- [ ] Daily chart loads and displays data
- [ ] Time range selector works
- [ ] Chart zoom and pan work
- [ ] Tab switching works

**Performance:**
- [ ] Page load time < 2 seconds
- [ ] Chart rendering < 1 second
- [ ] Search results appear instantly
- [ ] No lag when switching tabs

**Error Handling:**
- [ ] Database connection error shows friendly message
- [ ] Missing data shows appropriate empty state
- [ ] Invalid fund code handled gracefully

## Future Enhancements

### Short-term (Next 1-2 months)
1. **Comparison Mode**: Compare multiple funds side-by-side
2. **Export Functionality**: Export charts and data to Excel/CSV
3. **Favorites**: Save favorite funds for quick access
4. **Alerts**: Set price/NAV alerts

### Medium-term (3-6 months)
1. **Portfolio Tracking**: Track personal fund holdings
2. **Performance Analytics**: Calculate returns, Sharpe ratio, etc.
3. **Backtesting**: Test investment strategies
4. **Mobile App**: Native mobile version

### Long-term (6+ months)
1. **AI Recommendations**: ML-based fund recommendations
2. **Social Features**: Share insights with other users
3. **Real-time Data**: WebSocket for live updates
4. **Advanced Analytics**: Factor analysis, risk metrics

## Conclusion

This design provides a solid foundation for a professional fund data display system. The modular architecture allows for easy expansion, while the performance optimizations ensure a smooth user experience. The Streamlit multi-page approach balances simplicity with scalability, making it ideal for rapid development and iteration.

**Key Strengths:**
- Clean, maintainable code structure
- Professional financial UI
- Interactive data visualization
- Scalable for future features
- Performance-optimized

**Next Steps:**
1. Review and approve this design
2. Set up git worktree for isolated development
3. Create detailed implementation plan
4. Begin Phase 1 implementation
