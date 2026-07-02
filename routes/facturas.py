from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from flask_mysqldb import MySQL
from utils import login_required, generar_numero_factura, admin_required
from datetime import datetime
import MySQLdb

facturas_bp = Blueprint('facturas', __name__, url_prefix='/facturas')

mysql = None

def set_mysql(mysql_instance):
    global mysql
    mysql = mysql_instance

@facturas_bp.route('/')
@login_required
def listar():
    try:
        cursor = mysql.connection.cursor()
        
        if session.get('rol') == 'admin':
            # Admin ve todas las facturas
            cursor.execute("""
                SELECT f.id, f.numero_factura, f.fecha_emision, c.nombre as cliente,
                       f.total, f.estado, u.nombre as vendedor
                FROM facturas f
                JOIN clientes c ON f.cliente_id = c.id
                JOIN usuarios u ON f.vendedor_id = u.id
                ORDER BY f.id DESC
            """)
        else:
            # Vendedor solo ve sus facturas
            cursor.execute("""
                SELECT f.id, f.numero_factura, f.fecha_emision, c.nombre as cliente,
                       f.total, f.estado, u.nombre as vendedor
                FROM facturas f
                JOIN clientes c ON f.cliente_id = c.id
                JOIN usuarios u ON f.vendedor_id = u.id
                WHERE f.vendedor_id = %s
                ORDER BY f.id DESC
            """, (session['usuario_id'],))
        
        facturas = cursor.fetchall()
        cursor.close()
        return render_template('facturas/listar.html', facturas=facturas)
    except Exception as e:
        error = f'Error: {str(e)}'
        return render_template('facturas/listar.html', error=error, facturas=[])

@facturas_bp.route('/crear', methods=['POST'])
@login_required
def crear():
    try:
        cursor = mysql.connection.cursor()
        
        # Buscar "Clientes Varios" (cedula = '0000000000')
        cursor.execute("SELECT id FROM clientes WHERE cedula = '0000000000'")
        cliente = cursor.fetchone()
        
        if not cliente:
            # Fallback en caso de que no exista
            cursor.execute("SELECT id FROM clientes LIMIT 1")
            cliente = cursor.fetchone()
            
        cliente_id = cliente['id'] if cliente else 1
        
        # Generar número de factura
        numero_factura = generar_numero_factura(mysql)
        
        # Crear factura temporal/pendiente
        fecha_emision = datetime.now().date()
        cursor.execute("""
            INSERT INTO facturas (numero_factura, cliente_id, vendedor_id, fecha_emision, total, estado, tipo_venta) 
            VALUES (%s, %s, %s, %s, 0, 'pendiente', 'contado')
        """, (numero_factura, cliente_id, session['usuario_id'], fecha_emision))
        
        mysql.connection.commit()
        factura_id = cursor.lastrowid
        cursor.close()
        
        # Redirigir al POS
        return redirect(url_for('facturas.editar', factura_id=factura_id))
    
    except Exception as e:
        return f"Error al inicializar POS: {str(e)}", 500

@facturas_bp.route('/editar/<int:factura_id>', methods=['GET', 'POST'])
@login_required
def editar(factura_id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT f.*, c.nombre as cliente_nombre 
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            WHERE f.id = %s
        """, (factura_id,))
        factura = cursor.fetchone()
        
        if not factura:
            cursor.close()
            return redirect(url_for('facturas.listar'))
        
        # Verificar permisos: admin o el vendedor que creó la factura
        if session.get('rol') != 'admin' and factura['vendedor_id'] != session['usuario_id']:
            cursor.close()
            return "Acceso denegado", 403
            
        # Verificar si la factura ya está finalizada (tiene cuenta por cobrar)
        cursor.execute("SELECT id FROM cuentas_cobrar WHERE factura_id = %s", (factura_id,))
        finalizada = cursor.fetchone()
        if finalizada:
            cursor.close()
            is_ajax = request.headers.get('Content-Type') == 'application/json' or request.is_json
            if is_ajax:
                return jsonify({'error': 'La factura ya está finalizada y no se puede modificar'}), 400
            return redirect(url_for('facturas.ver', factura_id=factura_id))
            
        if request.method == 'POST':
            # Detectar si la petición es AJAX (JSON)
            is_ajax = request.headers.get('Content-Type') == 'application/json' or request.is_json
            
            if is_ajax:
                data = request.get_json() if request.is_json else request.json
                producto_id = data.get('producto_id', '')
                cantidad = data.get('cantidad', 1)
            else:
                producto_id = request.form.get('producto_id', '')
                cantidad = request.form.get('cantidad', '1')
            
            if not producto_id or cantidad is None:
                error = 'Producto y cantidad son requeridos'
                if is_ajax:
                    return jsonify({'error': error}), 400
                
                cursor.execute("SELECT id, nombre, precio_venta, stock, imagen FROM productos WHERE activo = TRUE")
                productos = cursor.fetchall()
                cursor.execute("""
                    SELECT df.id, df.producto_id, df.cantidad, df.precio_unitario, df.subtotal, 
                           p.nombre as producto_nombre
                    FROM detalle_factura df
                    JOIN productos p ON df.producto_id = p.id
                    WHERE df.factura_id = %s
                """, (factura_id,))
                detalles = cursor.fetchall()
                cursor.close()
                return render_template('facturas/editar.html', 
                                     factura=factura, 
                                     productos=productos, 
                                     detalles=detalles,
                                     error=error)
            
            try:
                producto_id = int(producto_id)
                cantidad = int(cantidad)
                
                # Obtener precio del producto
                cursor.execute("SELECT precio_venta FROM productos WHERE id = %s", (producto_id,))
                resultado = cursor.fetchone()
                
                if not resultado:
                    raise ValueError("Producto no encontrado")
                
                precio_unitario = resultado['precio_venta']
                subtotal = precio_unitario * cantidad
                
                # Verificar si el producto ya existe en la factura
                cursor.execute("""
                    SELECT id, cantidad FROM detalle_factura 
                    WHERE factura_id = %s AND producto_id = %s
                """, (factura_id, producto_id))
                
                existe = cursor.fetchone()
                if existe:
                    nueva_cantidad = existe['cantidad'] + cantidad
                    if nueva_cantidad <= 0:
                        cursor.execute("DELETE FROM detalle_factura WHERE id = %s", (existe['id'],))
                    else:
                        nuevo_subtotal = precio_unitario * nueva_cantidad
                        cursor.execute("""
                            UPDATE detalle_factura 
                            SET cantidad = %s, subtotal = %s 
                            WHERE id = %s
                        """, (nueva_cantidad, nuevo_subtotal, existe['id']))
                else:
                    if cantidad <= 0:
                        raise ValueError("La cantidad debe ser mayor a 0")
                    # Agregar detalle
                    cursor.execute("""
                        INSERT INTO detalle_factura (factura_id, producto_id, cantidad, precio_unitario, subtotal) 
                        VALUES (%s, %s, %s, %s, %s)
                    """, (factura_id, producto_id, cantidad, precio_unitario, subtotal))
                
                # Recalcular total de factura
                cursor.execute("""
                    SELECT SUM(subtotal) as total FROM detalle_factura WHERE factura_id = %s
                """, (factura_id,))
                
                result = cursor.fetchone()
                nuevo_total = result['total'] if result['total'] else 0
                
                cursor.execute("UPDATE facturas SET total = %s WHERE id = %s", 
                             (nuevo_total, factura_id))
                
                mysql.connection.commit()
                cursor.close()
                
                if is_ajax:
                    return jsonify({'success': True, 'nuevo_total': float(nuevo_total)})
                
                return redirect(url_for('facturas.editar', factura_id=factura_id))
            
            except ValueError as e:
                error = str(e)
                cursor.close()
                if is_ajax:
                    return jsonify({'error': error}), 400
            except Exception as e:
                error = f'Error: {str(e)}'
                cursor.close()
                if is_ajax:
                    return jsonify({'error': error}), 500
        
        # Cargar productos y detalles
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, nombre, precio_venta, stock, imagen FROM productos WHERE activo = TRUE")
        productos = cursor.fetchall()
        
        cursor.execute("""
            SELECT df.id, df.producto_id, df.cantidad, df.precio_unitario, df.subtotal, 
                   p.nombre as producto_nombre
            FROM detalle_factura df
            JOIN productos p ON df.producto_id = p.id
            WHERE df.factura_id = %s
        """, (factura_id,))
        detalles = cursor.fetchall()
        
        cursor.execute("SELECT id, nombre, cedula FROM clientes WHERE activo = TRUE ORDER BY nombre")
        clientes = cursor.fetchall()
        cursor.close()
        
        return render_template('facturas/editar.html', 
                             factura=factura, 
                             productos=productos, 
                             detalles=detalles,
                             clientes=clientes)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        error = f'Error: {str(e)}'
        return render_template('facturas/editar.html', error=error, factura={}, productos=[], detalles=[])

@facturas_bp.route('/eliminar-detalle/<int:detalle_id>', methods=['POST'])
@login_required
def eliminar_detalle(detalle_id):
    try:
        cursor = mysql.connection.cursor()
        
        # Obtener el detalle para saber a qué factura pertenece
        cursor.execute("SELECT factura_id FROM detalle_factura WHERE id = %s", (detalle_id,))
        resultado = cursor.fetchone()
        
        if not resultado:
            cursor.close()
            return jsonify({'error': 'Detalle no encontrado'}), 404
        
        factura_id = resultado['factura_id']
        
        # Verificar si la factura ya está finalizada
        cursor.execute("SELECT id FROM cuentas_cobrar WHERE factura_id = %s", (factura_id,))
        finalizada = cursor.fetchone()
        if finalizada:
            cursor.close()
            return jsonify({'error': 'La factura ya está finalizada y no se puede modificar'}), 400
            
        # Verificar permisos
        cursor.execute("SELECT vendedor_id FROM facturas WHERE id = %s", (factura_id,))
        factura = cursor.fetchone()
        
        if session.get('rol') != 'admin' and factura['vendedor_id'] != session['usuario_id']:
            cursor.close()
            return jsonify({'error': 'Acceso denegado'}), 403
        
        # Eliminar detalle
        cursor.execute("DELETE FROM detalle_factura WHERE id = %s", (detalle_id,))
        
        # Recalcular total
        cursor.execute("""
            SELECT SUM(subtotal) as total FROM detalle_factura WHERE factura_id = %s
        """, (factura_id,))
        
        result = cursor.fetchone()
        nuevo_total = result['total'] if result['total'] else 0
        
        cursor.execute("UPDATE facturas SET total = %s WHERE id = %s", (nuevo_total, factura_id))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@facturas_bp.route('/finalizar/<int:factura_id>', methods=['POST'])
@login_required
def finalizar(factura_id):
    try:
        data = request.get_json() if request.is_json else request.json
        if not data:
            data = {}
            
        nuevo_cliente_id = data.get('cliente_id')
        nuevo_tipo_venta = data.get('tipo_venta')
        
        cursor = mysql.connection.cursor()
        
        # Obtener factura
        cursor.execute("SELECT * FROM facturas WHERE id = %s", (factura_id,))
        factura = cursor.fetchone()
        
        if not factura:
            cursor.close()
            return jsonify({'error': 'Factura no encontrada'}), 404
        
        # Verificar permisos
        if session.get('rol') != 'admin' and factura['vendedor_id'] != session['usuario_id']:
            cursor.close()
            return jsonify({'error': 'Acceso denegado'}), 403
            
        # Actualizar datos de cliente y tipo_venta antes de procesar el pago
        if nuevo_cliente_id:
            factura['cliente_id'] = nuevo_cliente_id
        if nuevo_tipo_venta:
            factura['tipo_venta'] = nuevo_tipo_venta
            
        cursor.execute("UPDATE facturas SET cliente_id = %s, tipo_venta = %s WHERE id = %s", 
                       (factura['cliente_id'], factura['tipo_venta'], factura_id))
            
        # Obtener y verificar stock de los productos en la factura
        cursor.execute("""
            SELECT df.producto_id, df.cantidad, p.nombre, p.stock 
            FROM detalle_factura df 
            JOIN productos p ON df.producto_id = p.id 
            WHERE df.factura_id = %s
        """, (factura_id,))
        detalles = cursor.fetchall()
        
        for detalle in detalles:
            if detalle['stock'] < detalle['cantidad']:
                cursor.close()
                return jsonify({
                    'error': f"Stock insuficiente para: {detalle['nombre']} (Stock disponible: {detalle['stock']}, Requerido: {detalle['cantidad']})"
                }), 400
                
        # Deducir stock del inventario
        for detalle in detalles:
            cursor.execute("""
                UPDATE productos 
                SET stock = stock - %s 
                WHERE id = %s
            """, (detalle['cantidad'], detalle['producto_id']))
        
        # Lógica para crédito o contado
        if factura.get('tipo_venta') == 'credito':
            # Crear cuenta por cobrar
            cursor.execute("""
                INSERT INTO cuentas_cobrar (factura_id, cliente_id, monto_original, saldo_pendiente, estado) 
                VALUES (%s, %s, %s, %s, 'pendiente')
            """, (factura_id, factura['cliente_id'], factura['total'], factura['total']))
            
            # Actualizar estado de factura
            cursor.execute("UPDATE facturas SET estado = 'pendiente' WHERE id = %s", (factura_id,))
        else:
            # Ventas de contado
            cursor.execute("UPDATE facturas SET estado = 'pagada' WHERE id = %s", (factura_id,))
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@facturas_bp.route('/ver/<int:factura_id>')
@login_required
def ver(factura_id):
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT f.*, c.nombre as cliente_nombre, c.cedula, c.celular,
                   u.nombre as vendedor_nombre
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            JOIN usuarios u ON f.vendedor_id = u.id
            WHERE f.id = %s
        """, (factura_id,))
        factura = cursor.fetchone()
        
        if not factura:
            cursor.close()
            return redirect(url_for('facturas.listar'))
        
        # Verificar permisos
        if session.get('rol') != 'admin' and factura['vendedor_id'] != session['usuario_id']:
            cursor.close()
            return "Acceso denegado", 403
        
        cursor.execute("""
            SELECT df.id, df.cantidad, df.precio_unitario, df.subtotal, 
                   p.nombre as producto_nombre
            FROM detalle_factura df
            JOIN productos p ON df.producto_id = p.id
            WHERE df.factura_id = %s
        """, (factura_id,))
        detalles = cursor.fetchall()
        
        cursor.close()
        
        return render_template('facturas/ver.html', factura=factura, detalles=detalles)
    
    except Exception as e:
        error = f'Error: {str(e)}'
        return render_template('facturas/ver.html', error=error, factura={'total': 0.0, 'estado': 'pendiente'}, detalles=[])

@facturas_bp.route('/cancelar/<int:factura_id>', methods=['POST'])
@admin_required
def cancelar(factura_id):
    try:
        cursor = mysql.connection.cursor()
        
        # Obtener factura
        cursor.execute("SELECT * FROM facturas WHERE id = %s", (factura_id,))
        factura = cursor.fetchone()
        
        if not factura:
            cursor.close()
            return "Factura no encontrada", 404
        
        if factura['estado'] == 'cancelada':
            cursor.close()
            return "La factura ya está cancelada", 400
            
        # Revertir stock de los productos
        cursor.execute("""
            SELECT df.producto_id, df.cantidad 
            FROM detalle_factura df 
            WHERE df.factura_id = %s
        """, (factura_id,))
        detalles = cursor.fetchall()
        
        for detalle in detalles:
            cursor.execute("""
                UPDATE productos 
                SET stock = stock + %s 
                WHERE id = %s
            """, (detalle['cantidad'], detalle['producto_id']))
            
        # Eliminar pagos asociados a la cuenta por cobrar
        cursor.execute("SELECT id FROM cuentas_cobrar WHERE factura_id = %s", (factura_id,))
        cuenta = cursor.fetchone()
        if cuenta:
            cursor.execute("DELETE FROM pagos WHERE cuenta_cobrar_id = %s", (cuenta['id'],))
            cursor.execute("DELETE FROM cuentas_cobrar WHERE id = %s", (cuenta['id'],))
            
        # Cambiar estado de factura a 'cancelada'
        cursor.execute("UPDATE facturas SET estado = 'cancelada' WHERE id = %s", (factura_id,))
        
        mysql.connection.commit()
        cursor.close()
        
        return redirect(url_for('facturas.ver', factura_id=factura_id))
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                SELECT df.id, df.cantidad, df.precio_unitario, df.subtotal, 
                       p.nombre as producto_nombre
                FROM detalle_factura df
                JOIN productos p ON df.producto_id = p.id
                WHERE df.factura_id = %s
            """, (factura_id,))
            detalles = cursor.fetchall()
            cursor.close()
        except Exception:
            detalles = []
        return render_template('facturas/ver.html', error=f"Error al cancelar: {str(e)}", factura=factura, detalles=detalles)

@facturas_bp.route('/buscar_cliente', methods=['POST'])
@login_required
def buscar_cliente():
    try:
        data = request.get_json() if request.is_json else request.json
        cedula = data.get('cedula', '').strip()
        
        if not cedula:
            return jsonify({'error': 'Cédula no proporcionada'}), 400
            
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, nombre, cedula FROM clientes WHERE cedula = %s AND activo = TRUE", (cedula,))
        cliente = cursor.fetchone()
        cursor.close()
        
        if cliente:
            return jsonify({'success': True, 'cliente': cliente})
        else:
            return jsonify({'error': 'Cliente no encontrado'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@facturas_bp.route('/ticket/<int:factura_id>')
@login_required
def ticket(factura_id):
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT f.*, c.nombre as cliente_nombre, c.cedula, c.celular, c.direccion,
                   u.nombre as vendedor_nombre
            FROM facturas f
            JOIN clientes c ON f.cliente_id = c.id
            JOIN usuarios u ON f.vendedor_id = u.id
            WHERE f.id = %s
        """, (factura_id,))
        factura = cursor.fetchone()
        
        if not factura:
            cursor.close()
            return "Factura no encontrada", 404
            
        # Verificar permisos
        if session.get('rol') != 'admin' and factura['vendedor_id'] != session['usuario_id']:
            cursor.close()
            return "Acceso denegado", 403
            
        cursor.execute("""
            SELECT df.cantidad, df.precio_unitario, df.subtotal, 
                   p.nombre as producto_nombre
            FROM detalle_factura df
            JOIN productos p ON df.producto_id = p.id
            WHERE df.factura_id = %s
        """, (factura_id,))
        detalles = cursor.fetchall()
        
        cursor.close()
        
        return render_template('facturas/ticket.html', factura=factura, detalles=detalles)
    except Exception as e:
        return f"Error al generar ticket: {str(e)}", 500
