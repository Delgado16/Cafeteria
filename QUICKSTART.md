# Inicio Rápido - Sistema de Facturación Cafetería

## 🚀 Pasos para ejecutar la aplicación

### Paso 1: Instalar Python y MySQL

**En Windows:**
1. Descargar Python desde https://www.python.org/
2. Descargar MySQL desde https://dev.mysql.com/downloads/mysql/

**En macOS (con Homebrew):**
```bash
brew install python3
brew install mysql
```

**En Linux (Ubuntu/Debian):**
```bash
sudo apt-get install python3 python3-pip mysql-server
```

### Paso 2: Clonar/Descargar el proyecto

```bash
cd /ruta/del/proyecto
```

### Paso 3: Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

En algunos sistemas puede ser necesario:
```bash
pip3 install -r requirements.txt
```

### Paso 4: Configurar el archivo .env

Editar el archivo `.env` con tus credenciales de MySQL:

```
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=tu_contraseña_mysql
MYSQL_DB=cafeteria_facturacion
SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria
FLASK_ENV=development
FLASK_APP=app.py
```

### Paso 5: Iniciar MySQL

**Windows:**
- Abrir MySQL Workbench o comando: `mysql -u root -p`

**macOS/Linux:**
```bash
mysql -u root -p
# Ingresar contraseña
```

### Paso 6: Ejecutar la aplicación

```bash
python app.py
```

Verás algo como:
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### Paso 7: Abrir en navegador

1. Ir a: http://localhost:5000
2. Usar cualquiera de estas cuentas:

**Admin:**
- Email: `admin@cafeteria.com`
- Contraseña: `admin123`

**Vendedor:**
- Email: `vendedor@cafeteria.com`
- Contraseña: `vendedor123`

## ¿Qué puedo hacer?

### Como Admin

1. **Dashboard**: Ver estadísticas en tiempo real
   - Total de clientes
   - Total de facturas
   - Monto pendiente
   - Total de productos

2. **Gestión de Productos**: 
   - Crear nuevos productos
   - Editar precios y descripciones
   - Eliminar productos

3. **Gestión de Clientes**: 
   - Registrar nuevos clientes
   - Editar información de clientes
   - Ver detalles y facturas de cada cliente

4. **Ver todas las Facturas**: 
   - Facturas de todos los vendedores
   - Ver estado y detalles
   - Imprimir facturas

5. **Cuentas por Cobrar**: 
   - Ver todas las cuentas pendientes
   - Registrar PAGOS (a factura específica)
   - Registrar ABONOS (al saldo total del cliente)
   - Ver historial de pagos

6. **Reportes**: 
   - Generar reporte de cuentas por cobrar
   - Descargar en PDF
   - Descargar en Excel

7. **Gestión de Usuarios**: 
   - Crear nuevos vendedores o admins
   - Ver lista de usuarios

### Como Vendedor

1. **Dashboard**: Ver mis estadísticas
   - Mis facturas totales
   - Mi monto pendiente

2. **Crear Facturas**:
   - Seleccionar cliente
   - Agregar productos
   - La cantidad se multiplica automáticamente
   - Finalizar para crear cuenta por cobrar

3. **Ver Mis Facturas**:
   - Solo mis facturas creadas
   - Imprimir
   - Ver detalles

4. **Ver Clientes**: (Solo lectura)
   - Información de contacto
   - Facturas pendientes

## 📊 Ejemplo de Flujo Completo

### Como Vendedor:

1. Ir a "Facturas" → "Nueva Factura"
2. Seleccionar cliente (ej: Juan Pérez)
3. Seleccionar productos (ej: 2 Cappuccinos a $4.50 c/u)
4. Agregar a la factura
5. Seleccionar más productos si quiere
6. Hacer clic en "Finalizar Factura"
7. La factura se crea y se genera automáticamente la cuenta por cobrar

### Como Admin:

1. Ir a "Cuentas por Cobrar"
2. Ver la factura del vendedor
3. Hacer clic en "Pagar"
4. Ingresar monto (ej: $5.00)
5. Ingresar referencia (ej: Cheque #123)
6. Registrar pago
7. El saldo se actualiza automáticamente

## 🔍 Diferencia: PAGO vs ABONO

### PAGO
- Se registra contra **una factura específica**
- Reduce el saldo de esa factura
- Ejemplo: Cliente debe $25 en 3 facturas, paga $10 en la factura 1

### ABONO
- Se registra contra el **saldo total consolidado**
- Se aplica al total del cliente
- Ejemplo: Cliente debe $100 total, abona $50 (se resta de todo)

## 📄 Generar Reporte Quincenal

1. Ir a "Reportes"
2. Hacer clic en "Cuentas por Cobrar"
3. Ver tabla con todos los clientes y sus saldos
4. Descargar como PDF o Excel

El reporte incluye:
- Cédula del cliente
- Nombre del cliente
- Celular
- Saldo pendiente consolidado
- **Total general adeudado**

## ⚙️ Troubleshooting

### "Error: Connection refused"
**Solución**: MySQL no está ejecutándose
```bash
# En Windows, abrir PowerShell como Admin:
net start MySQL80

# En macOS/Linux:
mysql.server start
```

### "Error: Access denied"
**Solución**: Contraseña MySQL incorrecta en `.env`
- Verificar que `MYSQL_PASSWORD` sea correcta

### "ModuleNotFoundError: No module named 'flask'"
**Solución**: Instalar dependencias
```bash
pip install -r requirements.txt
```

### "Table already exists"
**Solución**: Las tablas ya existen, es normal
- Ejecutar `python init_data.py` solo si quieres borrar y reiniciar datos

## 💡 Consejos

1. **Backup de datos**: Hacer backup regular de MySQL
   ```bash
   mysqldump -u root -p cafeteria_facturacion > backup.sql
   ```

2. **Cambiar contraseña**: 
   - Ir a "Usuarios" como admin
   - Editar usuario

3. **Crear más vendedores**:
   - Como admin, ir a "Usuarios" → "Nuevo Usuario"
   - Seleccionar rol "Vendedor"

4. **Datos de prueba**:
   - El script `init_data.py` crea 5 clientes y 3 facturas de ejemplo

## 📞 Soporte

Si hay errores, revisar:
1. La consola de Python (línea roja = error)
2. Archivo `.env` (credenciales correctas)
3. MySQL ejecutándose (ver en tareas del sistema)

¡Listo! Ahora puedes usar el sistema de facturación. 🎉
