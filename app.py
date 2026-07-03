from flask import Flask, session, redirect, url_for
from flask_mysqldb import MySQL
from config import Config
from database import init_db
import os
from datetime import timedelta

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar MySQL
mysql = MySQL(app)

# Configuración de sesión
app.permanent_session_lifetime = timedelta(hours=24)

@app.before_request
def make_session_permanent():
    session.permanent = True

# Importar blueprints después de inicializar app y mysql
from routes.auth import auth_bp, set_mysql as set_mysql_auth
from routes.productos import productos_bp, set_mysql as set_mysql_productos
from routes.clientes import clientes_bp, set_mysql as set_mysql_clientes
from routes.facturas import facturas_bp, set_mysql as set_mysql_facturas
from routes.cuentas_cobrar import cuentas_bp, set_mysql as set_mysql_cuentas
from routes.reportes import reportes_bp, set_mysql as set_mysql_reportes

# Inyectar instancia de mysql en todas las rutas
set_mysql_auth(mysql)
set_mysql_productos(mysql)
set_mysql_clientes(mysql)
set_mysql_facturas(mysql)
set_mysql_cuentas(mysql)
set_mysql_reportes(mysql)

# Registrar blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(productos_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(facturas_bp)
app.register_blueprint(cuentas_bp)
app.register_blueprint(reportes_bp)

@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    return redirect(url_for('auth.dashboard'))

@app.errorhandler(404)
def not_found(error):
    return "Página no encontrada", 404

@app.errorhandler(500)
def server_error(error):
    return "Error del servidor", 500

if __name__ == '__main__':
    # Inicializar base de datos
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)


#Espero que funcione correctamente #