web: python -c "from database import init_db; init_db()" && gunicorn --workers 4 --threads 4 --bind 0.0.0.0:$PORT app:app
