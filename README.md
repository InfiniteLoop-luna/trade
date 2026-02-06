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
