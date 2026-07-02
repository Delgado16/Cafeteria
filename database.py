import MySQLdb
from config import Config

def init_db():
    """Inicializa la base de datos con las tablas necesarias"""
    try:
        conn = MySQLdb.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            passwd=Config.MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        
        # Crear base de datos si no existe
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
        cursor.execute(f"USE {Config.MYSQL_DB}")
        
        # Tabla: Usuarios (Admin y Vendedor)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT PRIMARY KEY AUTO_INCREMENT,
                nombre VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                contrasena VARCHAR(255) NOT NULL,
                rol ENUM('admin', 'vendedor') NOT NULL DEFAULT 'vendedor',
                activo BOOLEAN DEFAULT TRUE,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_email (email)
            )
        """)
        
        # Tabla: Productos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INT PRIMARY KEY AUTO_INCREMENT,
                nombre VARCHAR(150) NOT NULL,
                descripcion TEXT,
                precio_venta DECIMAL(10, 2) NOT NULL,
                stock INT DEFAULT 0,
                imagen VARCHAR(255),
                activo BOOLEAN DEFAULT TRUE,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_nombre (nombre)
            )
        """)
        
        # Tabla: Clientes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INT PRIMARY KEY AUTO_INCREMENT,
                nombre VARCHAR(150) NOT NULL,
                cedula VARCHAR(20) UNIQUE NOT NULL,
                celular VARCHAR(20),
                email VARCHAR(100),
                direccion TEXT,
                ciudad VARCHAR(100),
                activo BOOLEAN DEFAULT TRUE,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_cedula (cedula),
                INDEX idx_nombre (nombre)
            )
        """)
        
        # Tabla: Facturas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facturas (
                id INT PRIMARY KEY AUTO_INCREMENT,
                numero_factura VARCHAR(50) UNIQUE NOT NULL,
                cliente_id INT NOT NULL,
                vendedor_id INT NOT NULL,
                fecha_emision DATE NOT NULL,
                fecha_vencimiento DATE,
                subtotal DECIMAL(10, 2) DEFAULT 0,
                total DECIMAL(10, 2) NOT NULL,
                tipo_venta ENUM('contado', 'credito') DEFAULT 'contado',
                estado ENUM('pendiente', 'pagada', 'abonada', 'cancelada') DEFAULT 'pendiente',
                observaciones TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                FOREIGN KEY (vendedor_id) REFERENCES usuarios(id),
                INDEX idx_numero (numero_factura),
                INDEX idx_cliente (cliente_id),
                INDEX idx_estado (estado)
            )
        """)
        
        # Tabla: Detalle de Factura
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_factura (
                id INT PRIMARY KEY AUTO_INCREMENT,
                factura_id INT NOT NULL,
                producto_id INT NOT NULL,
                cantidad INT NOT NULL,
                precio_unitario DECIMAL(10, 2) NOT NULL,
                subtotal DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (factura_id) REFERENCES facturas(id) ON DELETE CASCADE,
                FOREIGN KEY (producto_id) REFERENCES productos(id),
                INDEX idx_factura (factura_id)
            )
        """)
        
        # Tabla: Cuentas por Cobrar
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cuentas_cobrar (
                id INT PRIMARY KEY AUTO_INCREMENT,
                factura_id INT NOT NULL UNIQUE,
                cliente_id INT NOT NULL,
                monto_original DECIMAL(10, 2) NOT NULL,
                saldo_pendiente DECIMAL(10, 2) NOT NULL,
                estado ENUM('pendiente', 'pagada', 'abonada') DEFAULT 'pendiente',
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (factura_id) REFERENCES facturas(id),
                FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                INDEX idx_cliente (cliente_id),
                INDEX idx_estado (estado)
            )
        """)
        
        # Tabla: Pagos (pago a factura específica)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagos (
                id INT PRIMARY KEY AUTO_INCREMENT,
                cuenta_cobrar_id INT NOT NULL,
                factura_id INT NOT NULL,
                monto DECIMAL(10, 2) NOT NULL,
                referencia VARCHAR(100),
                fecha_pago DATE NOT NULL,
                observaciones TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cuenta_cobrar_id) REFERENCES cuentas_cobrar(id),
                FOREIGN KEY (factura_id) REFERENCES facturas(id),
                INDEX idx_factura (factura_id),
                INDEX idx_fecha (fecha_pago)
            )
        """)
        
        # Tabla: Abonos (abono a saldo consolidado del cliente)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS abonos (
                id INT PRIMARY KEY AUTO_INCREMENT,
                cliente_id INT NOT NULL,
                monto DECIMAL(10, 2) NOT NULL,
                referencia VARCHAR(100),
                fecha_abono DATE NOT NULL,
                observaciones TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id),
                INDEX idx_cliente (cliente_id),
                INDEX idx_fecha (fecha_abono)
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Base de datos inicializada correctamente")
        
    except Exception as e:
        print(f"Error inicializando base de datos: {e}")
        raise
