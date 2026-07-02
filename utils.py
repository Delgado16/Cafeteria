from functools import wraps
from flask import session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb

def login_required(f):
    """Decorador para requerir login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorador para requerir rol admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('rol') != 'admin':
            return "Acceso denegado. Solo administradores", 403
        return f(*args, **kwargs)
    return decorated_function

def hash_password(password):
    """Genera hash de contraseña"""
    return generate_password_hash(password, method='pbkdf2:sha256')

def check_password(password, hash):
    """Verifica hash de contraseña"""
    return check_password_hash(hash, password)

def get_usuario_actual(mysql):
    """Obtiene datos del usuario actual desde sesión"""
    if 'usuario_id' not in session:
        return None
    
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (session['usuario_id'],))
        usuario = cursor.fetchone()
        cursor.close()
        return usuario
    except Exception as e:
        print(f"Error obteniendo usuario: {e}")
        return None

def generar_numero_factura(mysql):
    """Genera número único de factura"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT MAX(id) as max_id FROM facturas")
        result = cursor.fetchone()
        cursor.close()
        
        max_id = result['max_id'] if result['max_id'] else 0
        numero = f"FAC-{max_id + 1:06d}"
        return numero
    except Exception as e:
        print(f"Error generando número de factura: {e}")
        return None

def calcular_saldo_cliente(mysql, cliente_id):
    """Calcula el saldo consolidado de un cliente (suma de cuentas por cobrar - abonos)"""
    try:
        cursor = mysql.connection.cursor()
        
        # Suma de cuentas por cobrar
        cursor.execute("""
            SELECT SUM(saldo_pendiente) as total_cuentas 
            FROM cuentas_cobrar 
            WHERE cliente_id = %s AND estado != 'pagada'
        """, (cliente_id,))
        result_cuentas = cursor.fetchone()
        total_cuentas = float(result_cuentas['total_cuentas']) if result_cuentas['total_cuentas'] else 0
        
        # Suma de abonos
        cursor.execute("""
            SELECT SUM(monto) as total_abonos 
            FROM abonos 
            WHERE cliente_id = %s
        """, (cliente_id,))
        result_abonos = cursor.fetchone()
        total_abonos = float(result_abonos['total_abonos']) if result_abonos['total_abonos'] else 0
        
        cursor.close()
        
        saldo_pendiente = total_cuentas - total_abonos
        return max(saldo_pendiente, 0)  # No puede ser negativo
        
    except Exception as e:
        print(f"Error calculando saldo: {e}")
        return 0
