web: python -c "from database import init_db; init_db()" && gunicorn --workers 2 --threads 2 --bind 0.0.0.0:$PORT app:app
