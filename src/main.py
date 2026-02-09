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

        # Create tables if they don't exist
        db.create_tables()
        logger.info("Database tables initialized")

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
