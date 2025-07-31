web: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT --workers 1
release: cd backend && python -c "from app.database import init_db; init_db()" 