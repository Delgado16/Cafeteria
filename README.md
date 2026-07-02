# Sistema de Facturación para Cafetería

Sistema completo de facturación web con gestión de créditos, cuentas por cobrar y reportes automatizados.

## Características Principales

- **Dos Roles de Usuario**: Admin (gestión completa) y Vendedor (solo facturas)
- **Gestión de Productos**: Crear, editar y eliminar productos con precios e imágenes
- **Gestión de Clientes**: Registro de clientes con datos de contacto
- **Sistema de Facturación**: Crear facturas con detalles de productos y cálculos automáticos
- **Cuentas por Cobrar**: Seguimiento de créditos a clientes
- **Pagos y Abonos**: 
  - Pago: registra pago específico a una factura
  - Abono: abona al saldo consolidado total del cliente
- **Reportes Quincenales**: Exporta reportes de cuentas por cobrar a PDF y Excel

## Requisitos

- Python 3.8+
- MySQL 5.7+
- pip (gestor de paquetes de Python)

## Instalación

### 1. Clonar o descargar el proyecto

```bash
cd cafeteria-facturacion
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar base de datos

Editar el archivo `.env`:

```bash
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=tu_contraseña
MYSQL_DB=cafeteria_facturacion
SECRET_KEY=tu-clave-secreta-aqui
```

### 4. Inicializar base de datos

```bash
python init_data.py
```

Esto creará:
- Todas las tablas necesarias
- Usuarios de prueba (admin y vendedor)
- Productos y clientes de ejemplo
- Facturas de prueba con cuentas por cobrar

## Ejecutar la aplicación

```bash
python app.py
```

La aplicación estará disponible en: `http://localhost:5000`

### Cuentas de Prueba

**Admin:**
- Email: `admin@cafeteria.com`
- Contraseña: `admin123`

**Vendedor:**
- Email: `vendedor@cafeteria.com`
- Contraseña: `vendedor123`

## Estructura del Proyecto

```
cafeteria-facturacion/
├── app.py                      # Archivo principal
├── config.py                   # Configuración
├── database.py                 # Inicialización de BD
├── utils.py                    # Funciones auxiliares
├── init_data.py               # Datos de prueba
├── requirements.txt           # Dependencias
├── .env                       # Variables de entorno
├── routes/
│   ├── auth.py               # Autenticación y usuarios
│   ├── productos.py          # Gestión de productos
│   ├── clientes.py           # Gestión de clientes
│   ├── facturas.py           # Sistema de facturación
│   ├── cuentas_cobrar.py     # Cuentas y pagos
│   └── reportes.py           # Reportes
├── templates/
│   ├── base.html             # Template base
│   ├── login.html            # Login
│   ├── dashboard_*.html      # Dashboards
│   ├── usuarios/             # Templates usuarios
│   ├── productos/            # Templates productos
│   ├── clientes/             # Templates clientes
│   ├── facturas/             # Templates facturas
│   ├── cuentas/              # Templates cuentas
│   └── reportes/             # Templates reportes
└── static/
    ├── css/                  # Archivos CSS
    ├── js/                   # Archivos JavaScript
    └── uploads/              # Cargas de usuarios
```

## Flujo de Uso

### Para Admin

1. **Dashboard Admin**: Ver estadísticas generales
2. **Productos**: Crear y gestionar productos
3. **Clientes**: Crear y editar clientes
4. **Facturas**: Ver todas las facturas del sistema
5. **Cuentas por Cobrar**: Registrar pagos a facturas específicas
6. **Abonos**: Registrar abonos al saldo consolidado del cliente
7. **Reportes**: Generar y exportar reportes de cuentas por cobrar

### Para Vendedor

1. **Dashboard Vendedor**: Ver solo sus facturas
2. **Crear Factura**: 
   - Seleccionar cliente
   - Agregar productos con cantidades
   - Finalizar factura (crea cuenta por cobrar automáticamente)
3. **Ver Facturas**: Ver solo sus facturas creadas
4. **Ver Clientes**: Información de clientes (solo lectura)

## Conceptos Clave

### Pago vs Abono

- **Pago**: Se registra contra una factura específica. Reduce el saldo pendiente de esa factura.
- **Abono**: Se registra contra el saldo total consolidado del cliente (suma de todas sus cuentas por cobrar).

### Estados de Factura

- **Pendiente**: Factura sin pagar
- **Abonada**: Parcialmente pagada
- **Pagada**: Totalmente pagada

## API Endpoints

### Autenticación
- `POST /login` - Iniciar sesión
- `GET /logout` - Cerrar sesión
- `GET /dashboard` - Dashboard principal

### Productos (Admin)
- `GET /productos` - Listar productos
- `POST /productos/crear` - Crear producto
- `GET/POST /productos/editar/<id>` - Editar producto
- `POST /productos/eliminar/<id>` - Eliminar producto

### Clientes
- `GET /clientes` - Listar clientes
- `POST /clientes/crear` - Crear cliente (Admin)
- `GET/POST /clientes/editar/<id>` - Editar cliente (Admin)
- `GET /clientes/ver/<id>` - Ver detalle cliente

### Facturas
- `GET /facturas` - Listar facturas
- `POST /facturas/crear` - Crear factura
- `GET/POST /facturas/editar/<id>` - Editar/agregar detalles
- `GET /facturas/ver/<id>` - Ver factura
- `POST /facturas/finalizar/<id>` - Finalizar factura

### Cuentas por Cobrar (Admin)
- `GET /cuentas` - Listar cuentas
- `GET/POST /cuentas/pagar/<id>` - Registrar pago
- `GET/POST /cuentas/abonar/<id>` - Registrar abono
- `GET /cuentas/historial-pagos/<id>` - Ver historial

### Reportes (Admin)
- `GET /reportes` - Centro de reportes
- `GET /reportes/cuentas-por-cobrar` - Ver reporte
- `GET /reportes/cuentas-por-cobrar/pdf` - Descargar PDF
- `GET /reportes/cuentas-por-cobrar/excel` - Descargar Excel

## Personalizaciones Comunes

### Cambiar nombre de empresa
Editar en `templates/base.html`:
```html
<a href="/" class="navbar-brand">☕ Tu Nombre</a>
```

### Agregar más productos
Editar `init_data.py` y volver a ejecutar, o usar la interfaz.

### Cambiar colores
Editar variables CSS en `templates/base.html`:
```css
:root {
    --primary: #2563eb;
    --success: #10b981;
    --danger: #ef4444;
    /* ... más colores */
}
```

## Troubleshooting

### Error de conexión a MySQL
- Verificar que MySQL está corriendo
- Verificar credenciales en `.env`
- Verificar que la base de datos existe

### Error "ModuleNotFoundError"
- Ejecutar `pip install -r requirements.txt` nuevamente
- Verificar que se está usando el ambiente virtual correcto

### Tablas no se crean
- Ejecutar `python init_data.py`
- O ejecutar `app.py` que también las crea automáticamente

## Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.
