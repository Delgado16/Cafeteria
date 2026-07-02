from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from flask_mysqldb import MySQL
from utils import admin_required, login_required, calcular_saldo_cliente
from datetime import datetime
import MySQLdb

cuentas_bp = Blueprint('cuentas', __name__, url_prefix='/cuentas')

mysql = None

def set_mysql(mysql_instance):
    global mysql
    mysql = mysql_instance

@cuentas_bp.route('/')
@login_required
def listar():
    """Lista todas las cuentas por cobrar"""
    try:
        cursor = mysql.connection.cursor()
        
        cursor.execute("""
            SELECT cc.id, f.numero_factura, c.nombre as cliente, 
                   cc.monto_original, cc.saldo_pendiente, cc.estado, f.fecha_emision
            FROM cuentas_cobrar cc
            JOIN facturas f ON cc.factura_id = f.id
            JOIN clientes c ON cc.cliente_id = c.id
            ORDER BY f.fecha_emision DESC
        """)
        cuentas = cursor.fetchall()
        cursor.close()
        
        return render_template('cuentas/listar.html', cuentas=cuentas)
    except Exception as e:
        error = f'Error: {str(e)}'
        return render_template('cuentas/listar.html', error=error, cuentas=[])

@cuentas_bp.route('/cliente/<int:cliente_id>')
@login_required
def cuentas_cliente(cliente_id):
    """Muestra todas las cuentas por cobrar de un cliente"""
    try:
        cursor = mysql.connection.cursor()
        
        # Obtener cliente
        cursor.execute("SELECT * FROM clientes WHERE id = %s", (cliente_id,))
        cliente = cursor.fetchone()
        
        if not cliente:
            cursor.close()
            return redirect(url_for('clientes.listar'))
        
        # Obtener cuentas por cobrar del cliente
        cursor.execute("""
            SELECT cc.id, f.numero_factura, f.fecha_emision, 
                   cc.monto_original, cc.saldo_pendiente, cc.estado
            FROM cuentas_cobrar cc
            JOIN facturas f ON cc.factura_id = f.id
            WHERE cc.cliente_id = %s
            ORDER BY f.fecha_emision DESC
        """, (cliente_id,))
        cuentas = cursor.fetchall()
        
        # Calcular saldo consolidado
        saldo_consolidado = calcular_saldo_cliente(mysql, cliente_id)
        
        cursor.close()
        
        return render_template('cuentas/cuentas_cliente.html', 
                             cliente=cliente, 
                             cuentas=cuentas,
                             saldo_consolidado=saldo_consolidado)
    except Exception as e:
        error = f'Error: {str(e)}'
        return render_template('cuentas/cuentas_cliente.html', error=error, cliente={}, cuentas=[], saldo_consolidado=0.0)

@cuentas_bp.route('/pagar/<int:cuenta_id>', methods=['GET', 'POST'])
@admin_required
def pagar(cuenta_id):
    """Registrar pago a una cuenta específica"""
    try:
        cursor = mysql.connection.cursor()
        
        # Obtener cuenta por cobrar
        cursor.execute("""
            SELECT cc.*, f.numero_factura, c.nombre as cliente_nombre 
            FROM cuentas_cobrar cc
            JOIN facturas f ON cc.factura_id = f.id
            JOIN clientes c ON cc.cliente_id = c.id
            WHERE cc.id = %s
        """, (cuenta_id,))
        cuenta = cursor.fetchone()
        
        if not cuenta:
            cursor.close()
            return redirect(url_for('cuentas.listar'))
        
        if request.method == 'POST':
            monto = request.form.get('monto', '')
            referencia = request.form.get('referencia', '').strip()
            observaciones = request.form.get('observaciones', '').strip()
            
            if not monto:
                error = 'El monto es requerido'
                cursor.close()
                return render_template('cuentas/pagar.html', error=error, cuenta=cuenta)
            
            try:
                monto = float(monto)
                
                if monto <= 0:
                    error = 'El monto debe ser mayor a 0'
                    cursor.close()
                    return render_template('cuentas/pagar.html', error=error, cuenta=cuenta)
                
                if monto > cuenta['saldo_pendiente']:
                    error = f'El monto no puede exceder el saldo pendiente ({cuenta["saldo_pendiente"]})'
                    cursor.close()
                    return render_template('cuentas/pagar.html', error=error, cuenta=cuenta)
                
                # Registrar pago
                fecha_pago = datetime.now().date()
                cursor.execute("""
                    INSERT INTO pagos (cuenta_cobrar_id, factura_id, monto, referencia, fecha_pago, observaciones) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (cuenta_id, cuenta['factura_id'], monto, referencia, fecha_pago, observaciones))
                
                # Actualizar saldo pendiente
                nuevo_saldo = cuenta['saldo_pendiente'] - monto
                
                # Determinar estado
                if nuevo_saldo <= 0:
                    nuevo_estado = 'pagada'
                else:
                    nuevo_estado = 'abonada'
                
                cursor.execute("""
                    UPDATE cuentas_cobrar 
                    SET saldo_pendiente = %s, estado = %s 
                    WHERE id = %s
                """, (max(nuevo_saldo, 0), nuevo_estado, cuenta_id))
                
                # Actualizar estado de factura
                if nuevo_saldo <= 0:
                    cursor.execute("UPDATE facturas SET estado = %s WHERE id = %s", 
                                 ('pagada', cuenta['factura_id']))
                else:
                    cursor.execute("UPDATE facturas SET estado = %s WHERE id = %s", 
                                 ('abonada', cuenta['factura_id']))
                
                mysql.connection.commit()
                cursor.close()
                
                return redirect(url_for('cuentas.listar'))
            
            except ValueError:
                error = 'El monto debe ser un número válido'
                cursor.close()
                return render_template('cuentas/pagar.html', error=error, cuenta=cuenta)
        
        cursor.close()
        return render_template('cuentas/pagar.html', cuenta=cuenta)
    
    except Exception as e:
        error = f'Error: {str(e)}'
        return render_template('cuentas/pagar.html', error=error, cuenta={'monto_original': 0.0, 'saldo_pendiente': 0.0})

@cuentas_bp.route('/abonar/<int:cliente_id>', methods=['GET', 'POST'])
@admin_required
def abonar(cliente_id):
    """Registrar abono al saldo consolidado del cliente"""
    try:
        cursor = mysql.connection.cursor()
        
        # Obtener cliente
        cursor.execute("SELECT * FROM clientes WHERE id = %s", (cliente_id,))
        cliente = cursor.fetchone()
        
        if not cliente:
            cursor.close()
            return redirect(url_for('clientes.listar'))
        
        # Calcular saldo consolidado
        saldo_consolidado = calcular_saldo_cliente(mysql, cliente_id)
        
        if request.method == 'POST':
            monto = request.form.get('monto', '')
            referencia = request.form.get('referencia', '').strip()
            observaciones = request.form.get('observaciones', '').strip()
            
            if not monto:
                error = 'El monto es requerido'
                cursor.close()
                return render_template('cuentas/abonar.html', 
                                     error=error, 
                                     cliente=cliente, 
                                     saldo_consolidado=saldo_consolidado)
            
            try:
                monto = float(monto)
                
                if monto <= 0:
                    error = 'El monto debe ser mayor a 0'
                    cursor.close()
                    return render_template('cuentas/abonar.html', 
                                         error=error, 
                                         cliente=cliente, 
                                         saldo_consolidado=saldo_consolidado)
                
                # Registrar abono
                fecha_abono = datetime.now().date()
                cursor.execute("""
                    INSERT INTO abonos (cliente_id, monto, referencia, fecha_abono, observaciones) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (cliente_id, monto, referencia, fecha_abono, observaciones))
                
                mysql.connection.commit()
                cursor.close()
                
                return redirect(url_for('cuentas.cuentas_cliente', cliente_id=cliente_id))
            
            except ValueError:
                error = 'El monto debe ser un número válido'
                cursor.close()
                return render_template('cuentas/abonar.html', 
                                     error=error, 
                                     cliente=cliente, 
                                     saldo_consolidado=saldo_consolidado)
        
        cursor.close()
        return render_template('cuentas/abonar.html', 
                             cliente=cliente, 
                             saldo_consolidado=saldo_consolidado)
    
    except Exception as e:
        error = f'Error: {str(e)}'
        return render_template('cuentas/abonar.html', error=error, cliente={'id': cliente_id, 'nombre': '', 'cedula': ''}, saldo_consolidado=0.0)

@cuentas_bp.route('/historial-pagos/<int:cuenta_id>')
@login_required
def historial_pagos(cuenta_id):
    """Ver historial de pagos de una cuenta"""
    try:
        cursor = mysql.connection.cursor()
        
        # Obtener cuenta
        cursor.execute("""
            SELECT cc.*, f.numero_factura, c.nombre as cliente_nombre 
            FROM cuentas_cobrar cc
            JOIN facturas f ON cc.factura_id = f.id
            JOIN clientes c ON cc.cliente_id = c.id
            WHERE cc.id = %s
        """, (cuenta_id,))
        cuenta = cursor.fetchone()
        
        if not cuenta:
            cursor.close()
            return redirect(url_for('cuentas.listar'))
        
        # Obtener pagos
        cursor.execute("""
            SELECT * FROM pagos WHERE cuenta_cobrar_id = %s ORDER BY fecha_pago DESC
        """, (cuenta_id,))
        pagos = cursor.fetchall()
        
        cursor.close()
        
        return render_template('cuentas/historial_pagos.html', cuenta=cuenta, pagos=pagos)
    
    except Exception as e:
        error = f'Error: {str(e)}'
        return render_template('cuentas/historial_pagos.html', error=error, cuenta={'numero_factura': '', 'cliente_nombre': '', 'saldo_pendiente': 0.0, 'monto_original': 0.0}, pagos=[])

@cuentas_bp.route('/cancelar-todo/<int:cliente_id>', methods=['GET', 'POST'])
@admin_required
def cancelar_todo(cliente_id):
    """Cancela (paga) todas las cuentas pendientes de un cliente"""
    try:
        cursor = mysql.connection.cursor()
        
        # Obtener cuentas pendientes del cliente
        cursor.execute("""
            SELECT cc.id, cc.factura_id, cc.saldo_pendiente 
            FROM cuentas_cobrar cc
            WHERE cc.cliente_id = %s AND cc.estado != 'pagada'
        """, (cliente_id,))
        cuentas_pendientes = cursor.fetchall()
        
        if not cuentas_pendientes:
            cursor.close()
            return redirect(url_for('cuentas.cuentas_cliente', cliente_id=cliente_id))
            
        fecha_pago = datetime.now().date()
        referencia = "Pago total manual"
        observaciones = "Cancelación total de deuda"
        
        for cuenta in cuentas_pendientes:
            monto = cuenta['saldo_pendiente']
            cuenta_id = cuenta['id']
            factura_id = cuenta['factura_id']
            
            if monto > 0:
                # 1. Registrar pago
                cursor.execute("""
                    INSERT INTO pagos (cuenta_cobrar_id, factura_id, monto, referencia, fecha_pago, observaciones) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (cuenta_id, factura_id, monto, referencia, fecha_pago, observaciones))
                
                # 2. Actualizar cuenta_cobrar
                cursor.execute("""
                    UPDATE cuentas_cobrar 
                    SET saldo_pendiente = 0, estado = 'pagada' 
                    WHERE id = %s
                """, (cuenta_id,))
                
                # 3. Actualizar factura
                cursor.execute("""
                    UPDATE facturas SET estado = 'pagada' WHERE id = %s
                """, (factura_id,))
            
        mysql.connection.commit()
        cursor.close()
        
        return redirect(url_for('cuentas.cuentas_cliente', cliente_id=cliente_id))
        
    except Exception as e:
        print(f"Error cancelando toda la deuda: {e}")
        try:
            mysql.connection.rollback()
        except:
            pass
        return redirect(url_for('cuentas.cuentas_cliente', cliente_id=cliente_id))

