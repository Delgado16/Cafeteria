import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración base de la aplicación"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    
    # MySQL Configuration
    MYSQL_HOST = os.getenv('MYSQLHOST', os.getenv('MYSQL_HOST', 'localhost'))
    MYSQL_USER = os.getenv('MYSQLUSER', os.getenv('MYSQL_USER', 'root'))
    MYSQL_PASSWORD = os.getenv('MYSQLPASSWORD', os.getenv('MYSQL_PASSWORD', 'admin'))
    MYSQL_DB = os.getenv('MYSQLDATABASE', os.getenv('MYSQL_DB', 'cafeteria_facturacion'))
    MYSQL_CURSORCLASS = 'DictCursor'
    
    # Sesión
    PERMANENT_SESSION_LIFETIME = 86400  # 24 horas
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
