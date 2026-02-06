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
