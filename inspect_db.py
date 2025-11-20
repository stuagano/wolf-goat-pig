
from sqlalchemy import create_engine, inspect
from backend.app.database import DATABASE_URL, SQLITE_DATABASE_URL

# Use the same logic as database.py to get the URL
url = SQLITE_DATABASE_URL
print(f"Inspecting database at: {url}")

engine = create_engine(url)
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Tables found: {tables}")
