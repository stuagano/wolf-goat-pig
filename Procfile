web: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
release: cd backend && python -c "from app.database import init_db; init_db()" 