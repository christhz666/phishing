# MediTech System - Backend

Backend del sistema integral de gestión médica basado en FastAPI.

## Estructura del Proyecto

```
backend/
├── app/
│   ├── api/              # Endpoints de la API
│   │   ├── auth.py       # Autenticación y autorización
│   │   ├── branches.py   # Sucursales
│   │   ├── patients.py   # Pacientes
│   │   ├── invoices.py   # Facturación
│   │   ├── services.py   # Servicios/Estudios
│   │   ├── results.py    # Resultados
│   │   ├── users.py      # Usuarios
│   │   ├── roles.py      # Roles y permisos
│   │   └── public.py     # Endpoints públicos (QR, códigos barra)
│   ├── core/             # Configuración central
│   │   └── config.py
│   ├── models/           # Modelos SQLAlchemy
│   │   └── database.py
│   ├── services/         # Lógica de negocio
│   │   └── database.py
│   ├── integrations/     # Integraciones externas
│   │   ├── orthanc.py    # PACS
│   │   └── openelis.py   # LIS
│   └── main.py           # Punto de entrada
├── tests/                # Pruebas unitarias
├── requirements.txt      # Dependencias Python
└── .env.example          # Variables de entorno ejemplo
```

## Instalación

### 1. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 4. Inicializar base de datos

```bash
# Asegúrate de tener PostgreSQL corriendo
python -c "from app.services.database import init_db; init_db()"
```

### 5. Crear usuario super_root

```bash
python scripts/create_super_root.py
```

### 6. Ejecutar servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Documentación API

Una vez ejecutando el servidor, visita:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Endpoints Principales

### Autenticación
- `POST /api/v1/auth/login` - Iniciar sesión
- `POST /api/v1/auth/refresh` - Refrescar token
- `GET /api/v1/auth/me` - Obtener usuario actual

### Pacientes
- `GET /api/v1/patients` - Listar pacientes
- `POST /api/v1/patients` - Crear paciente
- `GET /api/v1/patients/{id}` - Obtener paciente
- `PUT /api/v1/patients/{id}` - Actualizar paciente
- `GET /api/v1/patients/search?q={nombre}` - Buscar paciente

### Facturación
- `POST /api/v1/invoices` - Crear factura (genera ID único por sucursal)
- `GET /api/v1/invoices/{codigo_unico}` - Obtener factura por ID único
- `GET /api/v1/invoices?patient_id={id}` - Historial de facturas por paciente

### Resultados
- `GET /api/v1/results/invoice/{invoice_id}` - Resultados de una factura específica
- `GET /api/v1/results/patient/{patient_id}` - Todos los resultados del paciente
- `GET /api/v1/public/result/{qr_code}` - Resultado por código QR (público)
- `GET /api/v1/public/result/barcode/{barcode}` - Resultado por código de barras (público)

## Integraciones

### Orthanc (PACS)
El sistema se conecta a Orthanc para:
- Enviar órdenes de estudios de imágenes
- Recuperar estudios DICOM completados
- Generar URLs para visor OHIF

### OpenELIS (LIS)
El sistema se conecta a OpenELIS para:
- Enviar órdenes de laboratorio
- Recibir resultados automáticamente vía HL7
- Sincronizar catálogos de pruebas

## Seguridad

- JWT para autenticación
- BCrypt para hashing de contraseñas
- Rate limiting para prevenir abuso
- CORS configurado
- Auditoría forense de todas las acciones

## Roles del Sistema

1. **SUPER_ROOT** - Acceso total, configuración inicial
2. **ADMIN_SUCURSAL** - Gestión completa de su sucursal
3. **RECEPCION** - Registro, facturación, búsqueda
4. **DOCTOR** - Validación resultados, historial clínico
5. **LABORATORIO** - Procesamiento muestras
6. **IMAGENES** - Procesamiento estudios radiológicos
7. **CAJA** - Cobros y reportes financieros
