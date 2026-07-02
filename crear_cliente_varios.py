import MySQLdb
from config import Config

def create_clientes_varios():
    try:
        conn = MySQLdb.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            passwd=Config.MYSQL_PASSWORD,
            db=Config.MYSQL_DB
        )
        cursor = conn.cursor()
        
        # Check if it exists
        cursor.execute("SELECT id FROM clientes WHERE cedula = '0000000000'")
        cliente = cursor.fetchone()
        
        if not cliente:
            cursor.execute("""
                INSERT INTO clientes (nombre, cedula, celular, email, direccion, ciudad)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ('Clientes Varios', '0000000000', '', '', '', ''))
            print(f"Cliente 'Clientes Varios' creado con ID {cursor.lastrowid}")
        else:
            print(f"El cliente 'Clientes Varios' ya existe con ID {cliente[0]}")
            
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    create_clientes_varios()
