from database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

with engine.connect() as conn:
    res = conn.execute(text("PRAGMA table_info('productos')")).fetchall()
    existing_cols = [row[1] for row in res]
    logger.info('Existing producto columns: %s', existing_cols)
    if 'stock' not in existing_cols:
        logger.info("Adding 'stock' column to productos table")
        conn.execute(text("ALTER TABLE productos ADD COLUMN stock INTEGER DEFAULT 0"))
        logger.info("Added 'stock' column")
    else:
        logger.info("'stock' column already present")

print('Migration complete')
