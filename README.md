# HONOR Supervisor Hub

Sistema de gestión para supervisores de HONOR que permite administrar tiendas, clientes y equipos.

## Características Principales

### Dashboard del Supervisor
- **Tiendas Asignadas**: Total de tiendas que tiene el supervisor
- **Promotores**: Total de promotores asignados al supervisor
- **Tiendas por Crear**: Listado detallado de tiendas pendientes de creación
- **Mi Equipo**: Listado de clientes y promotores con distinción entre creados y pendientes

### Gestión de Tiendas Pendientes
- Crear nuevas tiendas pendientes con toda la información requerida
- Campos incluidos:
  - Nombre de la tienda
  - Nombre del cliente
  - Ubicación (Estado, Ciudad, Urbanización/Municipio, Calle)
  - Mercado/Centro Comercial (con opción de crear nuevos)
  - Nivel y Local
  - Capacidad mensual
  - Ventas del último mes
  - Características (Fachada, Mesa)

### Gestión de Clientes Pendientes
- Crear nuevos clientes pendientes con información completa
- Campos incluidos:
  - Información personal (Nombre, ID, Género)
  - Contacto (Teléfono +58, Email)
  - Ubicación (Provincia, Ciudad)
  - Información automática (Organización VE001, Tipo MSS Non-HN FF, etc.)

### Sistema de Aprobación
- Botones de aprobación para tiendas y clientes pendientes
- Una vez aprobados, se marcan como "APPROVED"
- Preparado para integración con tablas principales del sistema

## Estructura de la Base de Datos

### Tablas Principales
- `pending_stores`: Tiendas pendientes de aprobación
- `pending_clients`: Clientes pendientes de aprobación
- `geography_codes`: Códigos geográficos para estados y ciudades
- `market_centers`: Centros comerciales y mercados disponibles

### Campos de Reporte Preparados
El sistema está preparado para generar reportes con las siguientes columnas:
- **Store Name**: Concatenación de Store + Market + Level + City
- **Short Store Name**: STORE + LOCAL
- **Business Type**: Honor (fijo)
- **Store Type**: Other (fijo)
- **Organization Code**: VE001 (fijo)
- **Geography Code**: Basado en geo_code
- **Store Address**: Concatenación de dirección completa
- **Store Monthly Capacity**: Campo CAPA
- **Honor Mobile Phone Sales**: Campo VENTAS
- **Honor Enter**: YES si VENTAS > 0, NO en caso contrario
- **Channel ID**: 200017495501 (fijo)

## Instalación y Configuración

### Requisitos
- Python 3.7+
- Flask
- SQLite3

### Instalación
1. Clonar el repositorio
2. Crear entorno virtual: `python -m venv venv`
3. Activar entorno virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Instalar dependencias: `pip install -r requirements.txt`
5. Inicializar base de datos: `python init_db.py`
6. Ejecutar aplicación: `python app.py`

### Acceso
- URL: `http://localhost:5000`
- Usar credenciales de supervisor existentes

## Autenticación

El sistema utiliza un sistema de autenticación basado en sesiones:

- **Contraseña por Defecto**: Todos los usuarios comienzan con la contraseña `honor1##`
- **Formato de ID**: Los IDs de Honor pueden ser cualquier identificador único (formato flexible)
- **Validación**: Solo se valida que el ID exista en la base de datos y pertenezca a un supervisor
- **Nota**: La funcionalidad de cambio de contraseña estará disponible en futuras actualizaciones

## Uso del Sistema

### Gestión Unificada (Recomendado)
1. Ir al Dashboard
2. Hacer clic en "🚀 Gestión Unificada"
3. **Sección Tienda**: Buscar tienda existente por código APSVE O crear nueva tienda
4. **Sección Cliente**: Buscar cliente existente O crear nuevo cliente
5. **Sección Asignación**: Asignar cliente a nueva tienda y/o tiendas existentes
6. **Envío**: Todo se procesa en una sola operación

### Crear Nueva Tienda Pendiente (Formulario Individual)
1. Ir al Dashboard
2. Hacer clic en "+ Nueva Tienda"
3. Completar formulario con información de la tienda
4. Seleccionar estado y ciudad del dropdown
5. Elegir mercado/centro comercial existente o crear uno nuevo
6. Completar campos de capacidad y ventas
7. Marcar características (fachada, mesa)
8. Guardar

### Crear Nuevo Cliente Pendiente (Formulario Individual)
1. Ir al Dashboard
2. Hacer clic en "+ Nuevo Cliente"
3. Completar información personal del cliente
4. Ingresar número de contacto (automáticamente +58)
5. Seleccionar estado y ciudad
6. La información automática se establece por defecto
7. Guardar

### Aprobar Tiendas/Clientes
1. En el Dashboard, ver la sección correspondiente
2. Hacer clic en "Aprobar" junto al elemento deseado
3. Confirmar la acción
4. El elemento se marcará como aprobado

## Estructura de Archivos

```
hub/
├── app.py                 # Aplicación principal Flask
├── init_db.py            # Script de inicialización de BD
├── honor_hub.db          # Base de datos SQLite
├── templates/            # Plantillas HTML
│   ├── dashboard.html    # Dashboard principal
│   ├── login.html        # Página de login
│   ├── unified_store_client_form.html  # Formulario unificado (RECOMENDADO)
│   ├── create_pending_store.html    # Formulario individual de tienda
│   └── create_pending_client.html   # Formulario individual de cliente
└── README.md             # Este archivo
```

## Funcionalidades Futuras

- Integración completa con tablas principales del sistema
- Generación automática de reportes
- Sistema de notificaciones
- Historial de cambios
- Exportación de datos
- API REST completa

## Soporte

Para soporte técnico o preguntas sobre el sistema, contactar al equipo de desarrollo de HONOR.

## Licencia

Sistema interno de HONOR - Uso exclusivo para empleados autorizados.
