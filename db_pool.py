from flask import g
from dbutils.pooled_db import PooledDB
import MySQLdb
import MySQLdb.cursors

class MySQLPool:
    def __init__(self, app=None):
        self.pool = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        cursor_class = getattr(MySQLdb.cursors, app.config.get('MYSQL_CURSORCLASS', 'DictCursor'))
        
        self.pool = PooledDB(
            creator=MySQLdb,
            mincached=6,      # Mínimo 6 conexiones simultáneas abiertas
            maxcached=10,     # Máximo 10 conexiones en caché
            maxconnections=20, # Límite máximo de conexiones
            blocking=True,    # Esperar si no hay conexiones disponibles
            host=app.config.get('MYSQL_HOST'),
            user=app.config.get('MYSQL_USER'),
            password=app.config.get('MYSQL_PASSWORD'),
            database=app.config.get('MYSQL_DB'),
            port=int(app.config.get('MYSQL_PORT', 3306)),
            cursorclass=cursor_class,
            autocommit=False
        )
        app.teardown_appcontext(self.teardown)

    @property
    def connection(self):
        # Usamos flask.g para mantener una conexión única por cada petición HTTP
        if 'mysql_db' not in g:
            g.mysql_db = self.pool.connection()
        return g.mysql_db

    def teardown(self, exception):
        # Al finalizar la petición, devolver la conexión al pool
        db = g.pop('mysql_db', None)
        if db is not None:
            db.close()  # dbutils intercepta el close() para devolverlo al pool
