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
