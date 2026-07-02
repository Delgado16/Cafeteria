import MySQLdb
from config import Config

def update_db():
    try:
        conn = MySQLdb.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            passwd=Config.MYSQL_PASSWORD,
            db=Config.MYSQL_DB
        )
        cursor = conn.cursor()
        
        # Add tipo_venta to facturas table
        try:
            cursor.execute("ALTER TABLE facturas ADD COLUMN tipo_venta ENUM('contado', 'credito') DEFAULT 'contado'")
            print("Columna tipo_venta añadida a la tabla facturas.")
        except MySQLdb.OperationalError as e:
            if 'Duplicate column name' in str(e):
                print("La columna tipo_venta ya existe en la tabla facturas.")
            else:
                raise
                
        conn.commit()
        cursor.close()
        conn.close()
        print("Actualización de base de datos completada.")
        
    except Exception as e:
        print(f"Error actualizando base de datos: {e}")

if __name__ == '__main__':
    update_db()
