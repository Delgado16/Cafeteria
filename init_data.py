#!/usr/bin/env python3
"""
Script para inicializar la base de datos con datos de prueba
Ejecutar con: python init_data.py
"""
import MySQLdb
from config import Config
from utils import hash_password
from datetime import datetime, timedelta

def init_test_data():
    """Inserta datos de prueba en la base de datos"""
    try:
        conn = MySQLdb.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            passwd=Config.MYSQL_PASSWORD,
            db=Config.MYSQL_DB
        )
        cursor = conn.cursor()

        # Verificar si los datos ya existen
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        row = cursor.fetchone()
        if row and row[0] > 0:
            print("La base de datos ya contiene datos. Saltando inicialización...")
            cursor.close()
            conn.close()
            return

        print("Inicializando datos de prueba...")

        # 1. Insertar usuarios
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, contrasena, rol)
            VALUES (%s, %s, %s, %s)
        """, ('Admin Sistema', 'admin@cafeteria.com', hash_password('admin123'), 'admin'))
        admin_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO usuarios (nombre, email, contrasena, rol)
            VALUES (%s, %s, %s, %s)
        """, ('Vendedor Ejemplo', 'vendedor@cafeteria.com', hash_password('vendedor123'), 'vendedor'))
        vendedor_id = cursor.lastrowid

        # 2. Insertar productos
        productos = [
            ('Café Espresso', 'Café fuerte y concentrado', 3.50, 100),
            ('Café Americano', 'Café diluido', 3.00, 100),
            ('Cappuccino', 'Café con leche espumada', 4.50, 50),
            ('Latte', 'Café con mucha leche', 4.00, 50),
            ('Mocha', 'Café con chocolate', 5.00, 30),
            ('Croissant', 'Pan de mantequilla', 2.50, 50),
            ('Pastel de Chocolate', 'Delicioso pastel', 3.50, 30),
            ('Galletas', 'Galletas variadas', 1.50, 100),
            ('Jugo Natural', 'Jugo fresco', 2.50, 40),
            ('Agua Embotellada', 'Agua mineral', 1.00, 200),
        ]

        for nombre, desc, precio, stock in productos:
            cursor.execute("""
                INSERT INTO productos (nombre, descripcion, precio_venta, stock)
                VALUES (%s, %s, %s, %s)
            """, (nombre, desc, precio, stock))

        # 3. Insertar clientes
        clientes = [
            ('Juan Pérez', '1234567890', '555-1234', 'juan@email.com', 'Calle 1 #123', 'Ciudad A'),
            ('María García', '0987654321', '555-5678', 'maria@email.com', 'Calle 2 #456', 'Ciudad A'),
            ('Carlos López', '1122334455', '555-9012', 'carlos@email.com', 'Calle 3 #789', 'Ciudad B'),
            ('Ana Martínez', '5566778899', '555-3456', 'ana@email.com', 'Calle 4 #101', 'Ciudad B'),
            ('Pedro Rodríguez', '9988776655', '555-7890', 'pedro@email.com', 'Calle 5 #202', 'Ciudad A'),
        ]

        cliente_ids = []
        for nombre, cedula, celular, email, direccion, ciudad in clientes:
            cursor.execute("""
                INSERT INTO clientes (nombre, cedula, celular, email, direccion, ciudad)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (nombre, cedula, celular, email, direccion, ciudad))
            cliente_ids.append(cursor.lastrowid)

        # 4. Insertar facturas de prueba
        fecha_hace_15_dias = datetime.now().date() - timedelta(days=15)
        
        for i, cliente_id in enumerate(cliente_ids[:3]):
            numero_factura = f"FAC-{i+1:06d}"
            cursor.execute("""
                INSERT INTO facturas (numero_factura, cliente_id, vendedor_id, fecha_emision, total, estado)
                VALUES (%s, %s, %s, %s, %s, 'pendiente')
            """, (numero_factura, cliente_id, vendedor_id, fecha_hace_15_dias, 25.00))
            
            factura_id = cursor.lastrowid

            # 5. Insertar detalles de factura
            cursor.execute("""
                INSERT INTO detalle_factura (factura_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """, (factura_id, 1, 2, 3.50, 7.00))

            cursor.execute("""
                INSERT INTO detalle_factura (factura_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """, (factura_id, 6, 1, 2.50, 2.50))

            cursor.execute("""
                INSERT INTO detalle_factura (factura_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            """, (factura_id, 9, 3, 2.50, 7.50))

            # Recalcular total
            nuevo_total = 7.00 + 2.50 + 7.50
            cursor.execute("UPDATE facturas SET total = %s WHERE id = %s", (nuevo_total, factura_id))

            # 6. Insertar cuenta por cobrar
            cursor.execute("""
                INSERT INTO cuentas_cobrar (factura_id, cliente_id, monto_original, saldo_pendiente, estado)
                VALUES (%s, %s, %s, %s, 'pendiente')
            """, (factura_id, cliente_id, nuevo_total, nuevo_total))

        conn.commit()
        cursor.close()
        conn.close()

        print("Datos de prueba inicializados correctamente")
        print("\nCuentas de prueba:")
        print("  Admin: admin@cafeteria.com / admin123")
        print("  Vendedor: vendedor@cafeteria.com / vendedor123")

    except Exception as e:
        print(f"Error inicializando datos: {e}")
        raise

if __name__ == '__main__':
    init_test_data()
