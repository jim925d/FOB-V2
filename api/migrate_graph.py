import asyncio
import os
import sys

# Add the app directory to sys.path so we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from sqlalchemy import text
from app.models.database import get_async_engine
from app.config import get_settings

async def run():
    print("Starting migration...")
    settings = get_settings()
    
    sql_path = os.path.join(os.path.dirname(__file__), 'migrations', '002_career_graph_schema.sql')
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql = f.read()
        
    engine = get_async_engine(settings.database_url)
    
    print(f"Connecting to database...")
    async with engine.begin() as conn:
        print("Executing SQL statements...")
        await conn.execute(text(sql))
        
    await engine.dispose()
    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(run())
