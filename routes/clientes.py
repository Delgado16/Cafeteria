from flask import Blueprint, render_template, request, session, redirect, url_for
from flask_mysqldb import MySQL
from utils import admin_required, login_required
import MySQLdb

clientes_bp = Blueprint('clientes', __name__, url_prefix='/clientes')

mysql = None

def set_mysql(mysql_instance):
    global mysql
    mysql = mysql_instance

@clientes_bp.route('/')
@login_required
def listar():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT id, nombre, cedula, celular, email, activo 
            FROM clientes 
            ORDER BY nombre
        """)
        clientes = cursor.fetchall()
        cursor.close()
        return render_template('clientes/listar.html', clientes=clientes)
    except Exception as e:
        error = f'Error: {str(e)}'
        return render_template('clientes/listar.html', error=error, clientes=[])

@clientes_bp.route('/crear', methods=['GET', 'POST'])
@admin_required
def crear():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        cedula = request.form.get('cedula', '').strip()
        celular = request.form.get('celular', '').strip()
        email = request.form.get('email', '').strip()
        direccion = request.form.get('direccion', '').strip()
        ciudad = request.form.get('ciudad', '').strip()
        
        if not nombre or not cedula:
            error = 'Nombre y cédula son requeridos'
            return render_template('clientes/crear.html', error=error)
        
        try:
            cursor = mysql.connection.cursor()
            
            # Verificar cédula única
            cursor.execute("SELECT id FROM clientes WHERE cedula = %s", (cedula,))
            if cursor.fetchone():
                cursor.close()
                error = 'La cédula ya está registrada'
                return render_template('clientes/crear.html', error=error)
            
            cursor.execute("""
                INSERT INTO clientes (nombre, cedula, celular, email, direccion, ciudad) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (nombre, cedula, celular, email, direccion, ciudad))
            
            mysql.connection.commit()
            cursor.close()
            
            return redirect(url_for('clientes.listar'))
        
        except Exception as e:
            error = f'Error: {str(e)}'
            return render_template('clientes/crear.html', error=error)
    
    return render_template('clientes/crear.html')

@clientes_bp.route('/editar/<int:cliente_id>', methods=['GET', 'POST'])
@admin_required
def editar(cliente_id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM clientes WHERE id = %s", (cliente_id,))
        cliente = cursor.fetchone()
        
        if not cliente:
            cursor.close()
            error = 'Cliente no encontrado'
            return render_template('clientes/editar.html', error=error, cliente={})
        
        if request.method == 'POST':
            nombre = request.form.get('nombre', '').strip()
            cedula = request.form.get('cedula', '').strip()
            celular = request.form.get('celular', '').strip()
            email = request.form.get('email', '').strip()
            direccion = request.form.get('direccion', '').strip()
            ciudad = request.form.get('ciudad', '').strip()
            
            if not nombre or not cedula:
                error = 'Nombre y cédula son requeridos'
                cursor.close()
                return render_template('clientes/editar.html', error=error, cliente=cliente)
            
            try:
                cursor.execute("""
                    UPDATE clientes 
                    SET nombre = %s, cedula = %s, celular = %s, email = %s, 
                        direccion = %s, ciudad = %s 
                    WHERE id = %s
                """, (nombre, cedula, celular, email, direccion, ciudad, cliente_id))
                
                mysql.connection.commit()
                cursor.close()
                
                return redirect(url_for('clientes.listar'))
            
            except MySQLdb.IntegrityError:
                error = 'La cédula ya está registrada'
                cursor.close()
                return render_template('clientes/editar.html', error=error, cliente=cliente)
        
        cursor.close()
        return render_template('clientes/editar.html', cliente=cliente)
    
    except Exception as e:
        error = f'Error: {str(e)}'
        return render_template('clientes/editar.html', error=error, cliente={})

@clientes_bp.route('/ver/<int:cliente_id>')
@login_required
def ver_detalle(cliente_id):
    try:
        cursor = mysql.connection.cursor()
        
        # Obtener cliente
        cursor.execute("SELECT * FROM clientes WHERE id = %s", (cliente_id,))
        cliente = cursor.fetchone()
        
        if not cliente:
            cursor.close()
            error = 'Cliente no encontrado'
            return render_template('clientes/detalle.html', error=error, cliente={}, facturas=[], total_deuda=0.0)
        
        # Obtener facturas del cliente
        cursor.execute("""
            SELECT f.id, f.numero_factura, f.fecha_emision, f.total, f.estado,
                   cc.saldo_pendiente
            FROM facturas f
            LEFT JOIN cuentas_cobrar cc ON f.id = cc.factura_id
            WHERE f.cliente_id = %s
            ORDER BY f.fecha_emision DESC
        """, (cliente_id,))
        facturas = cursor.fetchall()
        
        # Calcular saldo consolidado
        cursor.execute("""
            SELECT COALESCE(SUM(saldo_pendiente), 0) as total_deuda
            FROM cuentas_cobrar
            WHERE cliente_id = %s AND estado != 'pagada'
        """, (cliente_id,))
        deuda_result = cursor.fetchone()
        total_deuda = deuda_result['total_deuda'] if deuda_result else 0
        
        cursor.close()
        
        return render_template('clientes/detalle.html', 
                             cliente=cliente, 
                             facturas=facturas,
                             total_deuda=total_deuda)
    
    except Exception as e:
        error = f'Error: {str(e)}'
        return render_template('clientes/detalle.html', error=error, cliente={}, facturas=[], total_deuda=0.0)

@clientes_bp.route('/toggle/<int:cliente_id>', methods=['POST'])
@admin_required
def toggle_activo(cliente_id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT activo FROM clientes WHERE id = %s", (cliente_id,))
        cliente = cursor.fetchone()
        if cliente:
            nuevo_estado = 0 if cliente['activo'] else 1
            cursor.execute("UPDATE clientes SET activo = %s WHERE id = %s", (nuevo_estado, cliente_id))
            mysql.connection.commit()
        cursor.close()
        return redirect(url_for('clientes.listar'))
    except Exception as e:
        error = f'Error: {str(e)}'
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT id, nombre, cedula, celular, email, activo FROM clientes ORDER BY nombre")
            clientes = cursor.fetchall()
            cursor.close()
        except Exception:
            clientes = []
        return render_template('clientes/listar.html', error=error, clientes=clientes)
