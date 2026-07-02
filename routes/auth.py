from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from flask_mysqldb import MySQL
from utils import hash_password, check_password, admin_required
import MySQLdb
import datetime

auth_bp = Blueprint('auth', __name__)

# Esta variable será inyectada desde app.py
mysql = None

def set_mysql(mysql_instance):
    global mysql
    mysql = mysql_instance

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        contrasena = request.form.get('contrasena', '')
        
        if not email or not contrasena:
            error = 'Email y contraseña son requeridos'
        else:
            try:
                cursor = mysql.connection.cursor()
                cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
                usuario = cursor.fetchone()
                cursor.close()
                
                if usuario and check_password(contrasena, usuario['contrasena']):
                    if not usuario['activo']:
                        error = 'Usuario inactivo'
                    else:
                        session['usuario_id'] = usuario['id']
                        session['nombre'] = usuario['nombre']
                        session['email'] = usuario['email']
                        session['rol'] = usuario['rol']
                        return redirect(url_for('auth.dashboard'))
                else:
                    error = 'Email o contraseña inválidos'
            except Exception as e:
                error = f'Error en login: {str(e)}'
        
        return render_template('login.html', error=error)
    
    return render_template('login.html')

@auth_bp.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        cursor = mysql.connection.cursor()
        
        if session.get('rol') == 'admin':
            # Dashboard Admin - mostrar estadísticas generales
            cursor.execute("SELECT COUNT(*) as total FROM clientes")
            total_clientes = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as total FROM facturas")
            total_facturas = cursor.fetchone()['total']
            
            # Cartera pendiente real obtenida de cuentas por cobrar
            cursor.execute("SELECT SUM(saldo_pendiente) as total FROM cuentas_cobrar WHERE estado != 'pagada'")
            result = cursor.fetchone()
            monto_pendiente = result['total'] if result['total'] else 0
            
            cursor.execute("SELECT COUNT(*) as total FROM productos")
            total_productos = cursor.fetchone()['total']
            
            # Ventas de hoy
            cursor.execute("""
                SELECT SUM(total) as total 
                FROM facturas 
                WHERE fecha_emision = CURRENT_DATE() AND estado != 'cancelada' AND total > 0
            """)
            result_hoy = cursor.fetchone()
            ventas_hoy = result_hoy['total'] if result_hoy['total'] else 0
            
            # Ventas del mes
            cursor.execute("""
                SELECT SUM(total) as total 
                FROM facturas 
                WHERE MONTH(fecha_emision) = MONTH(CURRENT_DATE()) 
                  AND YEAR(fecha_emision) = YEAR(CURRENT_DATE()) 
                  AND estado != 'cancelada' AND total > 0
            """)
            result_mes = cursor.fetchone()
            ventas_mes = result_mes['total'] if result_mes['total'] else 0
            
            # Productos con bajo stock
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM productos 
                WHERE stock <= 10 AND activo = 1
            """)
            bajo_stock_count = cursor.fetchone()['total']
            
            cursor.execute("""
                SELECT id, nombre, stock 
                FROM productos 
                WHERE stock <= 10 AND activo = 1 
                ORDER BY stock ASC 
                LIMIT 5
            """)
            productos_bajo_stock = cursor.fetchall()
            
            # Últimas 5 facturas
            cursor.execute("""
                SELECT f.id, f.numero_factura, c.nombre as cliente, f.total, f.fecha_emision, f.estado 
                FROM facturas f
                JOIN clientes c ON f.cliente_id = c.id
                ORDER BY f.fecha_registro DESC 
                LIMIT 5
            """)
            ultimas_facturas = cursor.fetchall()
            
            # Últimos 5 abonos
            cursor.execute("""
                SELECT a.id, c.nombre as cliente, a.monto, a.fecha_abono, a.referencia 
                FROM abonos a
                JOIN clientes c ON a.cliente_id = c.id
                ORDER BY a.fecha_registro DESC 
                LIMIT 5
            """)
            ultimos_abonos = cursor.fetchall()
            
            # Ventas de la semana (últimos 7 días)
            cursor.execute("""
                SELECT fecha_emision, SUM(total) as total_dia 
                FROM facturas 
                WHERE fecha_emision >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) 
                  AND estado != 'cancelada' AND total > 0
                GROUP BY fecha_emision
                ORDER BY fecha_emision ASC
            """)
            ventas_semana_raw = cursor.fetchall()
            
            # Generar datos limpios para los últimos 7 días
            hoy = datetime.date.today()
            dias = [hoy - datetime.timedelta(days=i) for i in range(6, -1, -1)]
            
            # Mapear fechas a totales
            ventas_map = {}
            for row in ventas_semana_raw:
                f_emision = row['fecha_emision']
                date_str = f_emision.strftime('%Y-%m-%d') if isinstance(f_emision, datetime.date) else str(f_emision)
                ventas_map[date_str] = float(row['total_dia'])
            
            ventas_semana_labels = []
            ventas_semana_valores = []
            nombres_dias = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
            
            for d in dias:
                date_str = d.strftime('%Y-%m-%d')
                dia_semana_nombre = nombres_dias[d.weekday()]
                ventas_semana_labels.append(f"{dia_semana_nombre} {d.strftime('%d/%m')}")
                ventas_semana_valores.append(ventas_map.get(date_str, 0.0))
            
            # Productos más vendidos
            cursor.execute("""
                SELECT p.nombre, SUM(df.cantidad) as total_cantidad
                FROM detalle_factura df
                JOIN productos p ON df.producto_id = p.id
                JOIN facturas f ON df.factura_id = f.id
                WHERE f.estado != 'cancelada'
                GROUP BY p.id, p.nombre
                ORDER BY total_cantidad DESC
                LIMIT 5
            """)
            productos_mas_vendidos_raw = cursor.fetchall()
            
            productos_mas_vendidos_labels = [row['nombre'] for row in productos_mas_vendidos_raw]
            productos_mas_vendidos_valores = [int(row['total_cantidad']) for row in productos_mas_vendidos_raw]
            
            # Clientes con deuda para modal rápido
            cursor.execute("""
                SELECT c.id, c.nombre, SUM(cc.saldo_pendiente) as deuda_total
                FROM clientes c
                JOIN cuentas_cobrar cc ON c.id = cc.cliente_id
                WHERE cc.estado != 'pagada'
                GROUP BY c.id, c.nombre
                HAVING deuda_total > 0
                ORDER BY c.nombre ASC
            """)
            clientes_con_deuda = cursor.fetchall()
            
            cursor.close()
            
            return render_template('dashboard_admin.html', 
                                 total_clientes=total_clientes,
                                 total_facturas=total_facturas,
                                 monto_pendiente=monto_pendiente,
                                 total_productos=total_productos,
                                 ventas_hoy=ventas_hoy,
                                 ventas_mes=ventas_mes,
                                 bajo_stock_count=bajo_stock_count,
                                 productos_bajo_stock=productos_bajo_stock,
                                 ultimas_facturas=ultimas_facturas,
                                 ultimos_abonos=ultimos_abonos,
                                 ventas_semana_labels=ventas_semana_labels,
                                 ventas_semana_valores=ventas_semana_valores,
                                 productos_mas_vendidos_labels=productos_mas_vendidos_labels,
                                 productos_mas_vendidos_valores=productos_mas_vendidos_valores,
                                 clientes_con_deuda=clientes_con_deuda)
        else:
            # Dashboard Vendedor - solo sus facturas
            cursor.execute("""
                SELECT COUNT(*) as total FROM facturas 
                WHERE vendedor_id = %s
            """, (session['usuario_id'],))
            total_facturas = cursor.fetchone()['total']
            
            cursor.execute("""
                SELECT SUM(total) as total FROM facturas 
                WHERE vendedor_id = %s AND estado = 'pendiente'
            """, (session['usuario_id'],))
            result = cursor.fetchone()
            monto_pendiente = result['total'] if result['total'] else 0
            
            cursor.close()
            
            return render_template('dashboard_vendedor.html',
                                 total_facturas=total_facturas,
                                 monto_pendiente=monto_pendiente)
    
    except Exception as e:
        error = f'Error: {str(e)}'
        if session.get('rol') == 'admin':
            return render_template('dashboard_admin.html', 
                                 error=error, 
                                 total_clientes=0, 
                                 total_facturas=0, 
                                 monto_pendiente=0.0, 
                                 total_productos=0,
                                 ventas_hoy=0.0,
                                 ventas_mes=0.0,
                                 bajo_stock_count=0,
                                 productos_bajo_stock=[],
                                 ultimas_facturas=[],
                                 ultimos_abonos=[],
                                 ventas_semana_labels=[],
                                 ventas_semana_valores=[],
                                 productos_mas_vendidos_labels=[],
                                 productos_mas_vendidos_valores=[],
                                 clientes_con_deuda=[])
        else:
            return render_template('dashboard_vendedor.html', error=error, total_facturas=0, monto_pendiente=0.0)

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/admin/usuarios')
def listar_usuarios():
    if 'usuario_id' not in session or session.get('rol') != 'admin':
        return redirect(url_for('auth.login'))
    
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, nombre, email, rol, activo FROM usuarios ORDER BY nombre")
        usuarios = cursor.fetchall()
        cursor.close()
        return render_template('usuarios/listar.html', usuarios=usuarios)
    except Exception as e:
        error = f'Error: {str(e)}'
        return render_template('usuarios/listar.html', error=error, usuarios=[])

@auth_bp.route('/admin/usuarios/crear', methods=['GET', 'POST'])
def crear_usuario():
    if 'usuario_id' not in session or session.get('rol') != 'admin':
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        contrasena = request.form.get('contrasena', '')
        rol = request.form.get('rol', 'vendedor')
        
        if not nombre or not email or not contrasena:
            error = 'Todos los campos son requeridos'
            return render_template('usuarios/crear.html', error=error)
        
        try:
            cursor = mysql.connection.cursor()
            
            # Verificar que el email no exista
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            if cursor.fetchone():
                cursor.close()
                error = 'El email ya está registrado'
                return render_template('usuarios/crear.html', error=error)
            
            contrasena_hash = hash_password(contrasena)
            cursor.execute("""
                INSERT INTO usuarios (nombre, email, contrasena, rol) 
                VALUES (%s, %s, %s, %s)
            """, (nombre, email, contrasena_hash, rol))
            
            mysql.connection.commit()
            cursor.close()
            
            return redirect(url_for('auth.listar_usuarios'))
        
        except Exception as e:
            error = f'Error: {str(e)}'
            return render_template('usuarios/crear.html', error=error)
    
    return render_template('usuarios/crear.html')

@auth_bp.route('/admin/usuarios/toggle/<int:usuario_id>', methods=['POST'])
@admin_required
def toggle_usuario(usuario_id):
    try:
        # Impedir que el usuario actual se desactive a sí mismo
        if usuario_id == session.get('usuario_id'):
            flash('No puede desactivar su propia cuenta', 'danger')
            return redirect(url_for('auth.listar_usuarios'))
            
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT activo FROM usuarios WHERE id = %s", (usuario_id,))
        usuario = cursor.fetchone()
        if usuario:
            nuevo_estado = 0 if usuario['activo'] else 1
            cursor.execute("UPDATE usuarios SET activo = %s WHERE id = %s", (nuevo_estado, usuario_id))
            mysql.connection.commit()
        cursor.close()
        return redirect(url_for('auth.listar_usuarios'))
    except Exception as e:
        error = f'Error: {str(e)}'
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT id, nombre, email, rol, activo FROM usuarios ORDER BY nombre")
            usuarios = cursor.fetchall()
            cursor.close()
        except Exception:
            usuarios = []
        return render_template('usuarios/listar.html', error=error, usuarios=usuarios)
