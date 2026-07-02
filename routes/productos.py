from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from flask_mysqldb import MySQL
from utils import admin_required
import os

productos_bp = Blueprint('productos', __name__, url_prefix='/productos')

mysql = None

def set_mysql(mysql_instance):
    global mysql
    mysql = mysql_instance

@productos_bp.route('/')
@admin_required
def listar():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT id, nombre, descripcion, precio_venta, stock, activo 
            FROM productos 
            ORDER BY nombre
        """)
        productos = cursor.fetchall()
        cursor.close()
        return render_template('productos/listar.html', productos=productos)
    except Exception as e:
        error = f'Error: {str(e)}'
        return render_template('productos/listar.html', error=error, productos=[])

@productos_bp.route('/crear', methods=['GET', 'POST'])
@admin_required
def crear():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        precio_venta = request.form.get('precio_venta', '')
        stock = request.form.get('stock', '0')
        
        if not nombre or not precio_venta:
            error = 'Nombre y precio de venta son requeridos'
            return render_template('productos/crear.html', error=error)
        
        try:
            precio_venta = float(precio_venta)
            stock = int(stock)
            
            if precio_venta < 0 or stock < 0:
                error = 'Precio y stock deben ser positivos'
                return render_template('productos/crear.html', error=error)
            
            # Procesar imagen si se sube
            imagen_filename = None
            if 'imagen' in request.files:
                file = request.files['imagen']
                if file and file.filename:
                    # Guardar con timestamp para evitar conflictos
                    from datetime import datetime
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    imagen_filename = f"producto_{timestamp}_{file.filename}"
                    file.save(os.path.join('static/uploads/productos', imagen_filename))
            
            cursor = mysql.connection.cursor()
            cursor.execute("""
                INSERT INTO productos (nombre, descripcion, precio_venta, stock, imagen) 
                VALUES (%s, %s, %s, %s, %s)
            """, (nombre, descripcion, precio_venta, stock, imagen_filename))
            
            mysql.connection.commit()
            cursor.close()
            
            return redirect(url_for('productos.listar'))
        
        except ValueError:
            error = 'Precio debe ser un número válido'
            return render_template('productos/crear.html', error=error)
        except Exception as e:
            error = f'Error: {str(e)}'
            return render_template('productos/crear.html', error=error)
    
    return render_template('productos/crear.html')

@productos_bp.route('/editar/<int:producto_id>', methods=['GET', 'POST'])
@admin_required
def editar(producto_id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM productos WHERE id = %s", (producto_id,))
        producto = cursor.fetchone()
        
        if not producto:
            cursor.close()
            error = 'Producto no encontrado'
            return render_template('productos/editar.html', error=error, producto={})
        
        if request.method == 'POST':
            nombre = request.form.get('nombre', '').strip()
            descripcion = request.form.get('descripcion', '').strip()
            precio_venta = request.form.get('precio_venta', '')
            stock = request.form.get('stock', '0')
            
            if not nombre or not precio_venta:
                error = 'Nombre y precio son requeridos'
                cursor.close()
                return render_template('productos/editar.html', error=error, producto=producto)
            
            try:
                precio_venta = float(precio_venta)
                stock = int(stock)
                
                cursor.execute("""
                    UPDATE productos 
                    SET nombre = %s, descripcion = %s, precio_venta = %s, stock = %s 
                    WHERE id = %s
                """, (nombre, descripcion, precio_venta, stock, producto_id))
                
                mysql.connection.commit()
                cursor.close()
                
                return redirect(url_for('productos.listar'))
            
            except ValueError:
                error = 'Precio debe ser un número válido'
                cursor.close()
                return render_template('productos/editar.html', error=error, producto=producto)
        
        cursor.close()
        return render_template('productos/editar.html', producto=producto)
    
    except Exception as e:
        error = f'Error: {str(e)}'
        return render_template('productos/editar.html', error=error, producto={})

@productos_bp.route('/eliminar/<int:producto_id>', methods=['POST'])
@admin_required
def eliminar(producto_id):
    try:
        cursor = mysql.connection.cursor()
        # Toggle del estado activo en lugar de eliminar físicamente
        cursor.execute("SELECT activo FROM productos WHERE id = %s", (producto_id,))
        producto = cursor.fetchone()
        if producto:
            nuevo_estado = 0 if producto['activo'] else 1
            cursor.execute("UPDATE productos SET activo = %s WHERE id = %s", (nuevo_estado, producto_id))
            mysql.connection.commit()
        cursor.close()
        return redirect(url_for('productos.listar'))
    except Exception as e:
        error = f'Error: {str(e)}'
        try:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT id, nombre, descripcion, precio_venta, stock, activo FROM productos ORDER BY nombre")
            productos = cursor.fetchall()
            cursor.close()
        except Exception:
            productos = []
        return render_template('productos/listar.html', error=error, productos=productos)
