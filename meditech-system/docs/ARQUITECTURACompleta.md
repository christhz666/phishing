# MediTech System - Sistema Integral de Gestión Médica

## Arquitectura Open Source Definitiva

### Stack Tecnológico

#### Backend (Núcleo HIS & Facturación)
- **Lenguaje:** Python 3.11+
- **Framework:** FastAPI (alto rendimiento, async nativo)
- **Base de Datos:** PostgreSQL 15+
- **ORM:** SQLAlchemy 2.0 + Alembic (migraciones)
- **Autenticación:** JWT + OAuth2
- **Validación:** Pydantic v2

#### Frontend
- **Framework:** React 18+ con TypeScript
- **Build Tool:** Vite (ultra rápido)
- **UI Library:** Tailwind CSS + Headless UI
- **Estado:** Zustand (ligero) + React Query
- **Gráficos:** Recharts / Chart.js
- **Códigos QR/Barra:** react-qr-code + react-barcode

#### PACS (Imágenes Médicas)
- **Servidor DICOM:** Orthanc (liviano, REST API completa)
- **Visor Web:** OHIF Viewer v3 (moderno, configurable)
- **Protocolos:** DICOM, DICOMweb, WADO-RS

#### LIS (Laboratorio Clínico)
- **Sistema:** OpenELIS Global 2
- **Protocolos:** HL7 v2.x, ASTM
- **Middleware:** Mirth Connect (opcional para equipos legacy)

#### Infraestructura
- **Web Server:** Nginx (reverse proxy, SSL)
- **Cola Tareas:** Celery + Redis (impresión asíncrona)
- **Cache:** Redis
- **Logs:** Structured logging + ELK (opcional)

---

## Estándares de Interoperabilidad

### HL7 v2.x
- **ADT^A01:** Admisión de pacientes
- **ORM^O01:** Órdenes de laboratorio/imágenes
- **ORU^R01:** Resultados de laboratorio/imágenes
- **DFT^P03:** Facturación

### FHIR R4
- **Patient:** Datos demográficos
- **Encounter:** Visitas/consultas
- **ServiceRequest:** Órdenes médicas
- **DiagnosticReport:** Resultados
- **Observation:** Hallazgos clínicos
- **Invoice:** Facturación

### DICOM/DICOMweb
- **WADO-RS:** Recuperación de imágenes
- **QIDO-RS:** Búsqueda de estudios
- **STOW-RS:** Almacenamiento de imágenes

---

## Modelo de Datos Clave

### Sucursales (Branches)
```sql
- id: UUID
- codigo: VARCHAR(10) -- Ej: "SUC01"
- nombre: VARCHAR(100)
- direccion: TEXT
- telefono: VARCHAR(20)
- email: VARCHAR(100)
- logo: VARCHAR(255)
- configuracion: JSONB -- Personalización UI
- activo: BOOLEAN
- created_at: TIMESTAMP
```

### Pacientes (Patients)
```sql
- id: UUID
- sucursal_id: FK -> branches.id
- primer_nombre: VARCHAR(50)
- segundo_nombre: VARCHAR(50)
- primer_apellido: VARCHAR(50)
- segundo_apellido: VARCHAR(50)
- fecha_nacimiento: DATE
- sexo: CHAR(1) -- M/F/O
- tipo_sangre: VARCHAR(5)
- cedula: VARCHAR(20) -- NULL para menores
- es_menor: BOOLEAN
- telefono: VARCHAR(20)
- email: VARCHAR(100)
- direccion: TEXT
- contacto_emergencia: JSONB
- historial_medico: TEXT
- created_at: TIMESTAMP
```

### Facturas (Invoices) - ID ÚNICO POR SUCURSAL
```sql
- id: UUID
- sucursal_id: FK -> branches.id
- consecutivo_sucursal: INTEGER -- Genera ID 4-5 dígitos
- codigo_unico: VARCHAR(10) -- Ej: "05021" (calculado)
- paciente_id: FK -> patients.id
- usuario_crea_id: FK -> users.id
- fecha_emision: TIMESTAMP
- estado: VARCHAR(20) -- PENDIENTE, PARCIAL, PAGADA, CANCELADA
- subtotal: DECIMAL(10,2)
- descuento: DECIMAL(10,2)
- impuesto: DECIMAL(10,2)
- total: DECIMAL(10,2)
- saldo_pendiente: DECIMAL(10,2)
- codigo_barras: VARCHAR(100) -- Hash único
- codigo_qr: VARCHAR(255) -- URL/token acceso resultados
- observaciones: TEXT
- metadata: JSONB
- created_at: TIMESTAMP
```

### Estudios/Servicios (Services)
```sql
- id: UUID
- sucursal_id: FK -> branches.id
- codigo: VARCHAR(20)
- nombre: VARCHAR(100)
- descripcion: TEXT
- categoria: VARCHAR(50) -- LABORATORIO, IMAGENES, CONSULTA
- precio_base: DECIMAL(10,2)
- requiere_muestra: BOOLEAN
- tiempo_entrega_horas: INTEGER
- codigo_cpt: VARCHAR(10)
- activo: BOOLEAN
```

### Factura Detalle (Invoice Items) - LIGA ESTUDIOS A FACTURA
```sql
- id: UUID
- factura_id: FK -> invoices.id
- servicio_id: FK -> services.id
- cantidad: INTEGER
- precio_unitario: DECIMAL(10,2)
- subtotal: DECIMAL(10,2)
- estado_resultado: VARCHAR(20) -- PENDIENTE, EN_PROCESO, COMPLETADO
- orden_laboratorio_id: FK -- Referencia a OpenELIS
- estudio_pacs_uid: VARCHAR(64) -- Referencia a Orthanc
- creado_en: TIMESTAMP
```

### Resultados (Results)
```sql
- id: UUID
- factura_detalle_id: FK -> invoice_items.id
- paciente_id: FK -> patients.id
- sucursal_id: FK -> branches.id
- tipo: VARCHAR(20) -- LABORATORIO, IMAGEN
- datos_resultado: JSONB -- Estructura flexible
- archivo_pdf: VARCHAR(255)
- imagenes_urls: JSONB
- validado_por_id: FK -> users.id
- fecha_validacion: TIMESTAMP
- visible_portal: BOOLEAN
- created_at: TIMESTAMP
```

### Usuarios (Users)
```sql
- id: UUID
- sucursal_id: FK -> branches.id
- username: VARCHAR(50)
- email: VARCHAR(100)
- password_hash: VARCHAR(255)
- primer_nombre: VARCHAR(50)
- apellidos: VARCHAR(100)
- rol_id: FK -> roles.id
- activo: BOOLEAN
- ultimo_acceso: TIMESTAMP
- created_at: TIMESTAMP
```

### Roles (Roles) - SISTEMA GRANULAR DE PERMISOS
```sql
- id: UUID
- nombre: VARCHAR(50) -- SUPER_ADMIN, ADMIN, RECEPCION, DOCTOR, LAB, IMAGENES, CAJA
- descripcion: TEXT
- permisos: JSONB -- {modulo: [leer, crear, editar, eliminar]}
- creado_por_id: FK -> users.id
- created_at: TIMESTAMP
```

---

## Flujo de Trabajo Principal

### 1. Registro de Paciente
```
Recepción → Buscar existente (nombre/cédula) 
         → Si no existe: Nuevo registro (cedula opcional si menor)
         → Asignar a sucursal actual
         → Redirigir a selección de estudios
```

### 2. Selección de Estudios
```
Catálogo de servicios por categoría
→ Marcar estudios requeridos
→ Ver precios y tiempos de entrega
→ Confirmar selección
→ Redirigir a facturación
```

### 3. Facturación
```
Generar factura con consecutivo por sucursal
→ Calcular ID único 4-5 dígitos (ej: 05021)
→ Generar código de barras (hash único)
→ Generar código QR (token acceso resultados)
→ Aplicar seguros/coberturas si corresponde
→ Registrar forma de pago (efectivo, tarjeta, pendiente)
→ Imprimir factura con códigos
→ Crear órdenes en sistemas externos (LIS/PACS)
```

### 4. Toma de Muestras/Estudios
```
Laboratorio/Imágenes recibe orden automáticamente
→ Ejecuta estudio en equipo analítico
→ Resultado se captura automáticamente (HL7/DICOM)
→ Validación por profesional
→ Resultado se liga a factura original
```

### 5. Entrega de Resultados
```
Paciente busca por:
- Código QR (desde casa)
- Código de barras (en sucursal)
- Nombre (historial completo)
- ID factura (resultados específicos de esa visita)

Si hay saldo pendiente:
→ Mostrar pantalla amigable de pago requerido
→ Bloquear descarga/impresión
→ Ofrecer opciones de pago
```

---

## Integración con Equipos de Laboratorio

### Conexión Directa (Recomendada)
```
Analizador → TCP/IP (puerto configurable) → OpenELIS
Protocolo: ASTM 1381 o HL7 v2.x
- El equipo envía resultados automáticamente
- OpenELIS procesa y valida
- API REST notifica al núcleo HIS
```

### Middleware (Equipos Legacy)
```
Analizador → Serial/USB → Mirth Connect → Transformación HL7 → OpenELIS
- Mirth actúa como puente
- Convierte protocolos propietarios a HL7
- Filtra y enruta mensajes
```

### Configuración por Equipo
```yaml
equipos:
  - nombre: "Analizador Hematología"
    marca: "Sysmex"
    modelo: "XS-500i"
    protocolo: "ASTM"
    puerto_tcp: 5000
    baud_rate: 9600
    paridad: "NONE"
    bits_datos: 8
    bits_stop: 1
    campo_paciente: "ID_FACTURA"
    mapeo_campos:
      WBC: "leucocitos"
      RBC: "eritrocitos"
      HGB: "hemoglobina"
```

---

## Seguridad y Permisos

### Roles Predefinidos
1. **SUPER_ROOT:** Acceso total, configuración inicial, multi-sucursal
2. **ADMIN_SUCURSAL:** Gestión completa de su sucursal
3. **RECEPCION:** Registro pacientes, facturación, búsqueda
4. **DOCTOR:** Validación resultados, historial clínico
5. **LABORATORIO:** Procesamiento muestras, validación lab
6. **IMAGENES:** Procesamiento estudios, validación radiología
7. **CAJA:** Cobros, reportes financieros
8. **PACIENTE:** Portal web, ver sus resultados

### Permisos Granulares
```json
{
  "pacientes": ["leer", "crear", "editar"],
  "facturacion": ["leer", "crear", "cobrar"],
  "resultados": ["leer", "validar"],
  "reportes": ["leer", "exportar"],
  "configuracion": ["leer", "editar"],
  "usuarios": ["leer", "crear"]
}
```

---

## Plan de Implementación

### Fase 1: Infraestructura Base (Semana 1-2)
- [ ] Instalar Ubuntu Server 22.04 LTS
- [ ] Configurar PostgreSQL 15
- [ ] Instalar Nginx con SSL
- [ ] Configurar Redis
- [ ] Desplegar Orthanc (PACS)
- [ ] Desplegar OpenELIS Global 2 (LIS)

### Fase 2: Núcleo HIS (Semana 3-6)
- [ ] Desarrollar backend FastAPI
- [ ] Modelos de datos y migraciones
- [ ] Autenticación JWT + Roles
- [ ] CRUD Pacientes, Facturas, Servicios
- [ ] Generación IDs únicos por sucursal
- [ ] Códigos QR y barras

### Fase 3: Frontend (Semana 7-10)
- [ ] Setup React + Vite + TypeScript
- [ ] Diseño UI/UX con Tailwind
- [ ] Dashboard personalizable
- [ ] Flujos completos (registro → factura → resultados)
- [ ] Buscador multi-criterio
- [ ] Vista previa impresión modal

### Fase 4: Integraciones (Semana 11-14)
- [ ] Conectar Orthanc vía DICOMweb
- [ ] Conectar OpenELIS vía HL7/REST
- [ ] Sincronización automática de órdenes
- [ ] Recepción automática de resultados
- [ ] Pruebas con equipos reales

### Fase 5: Funcionalidades Avanzadas (Semana 15-18)
- [ ] Portal pacientes web
- [ ] Pagos en línea (Stripe/PayPal)
- [ ] Seguros y coberturas
- [ ] Reportes avanzados
- [ ] Auditoría forense
- [ ] Backup automático

### Fase 6: Pruebas y Despliegue (Semana 19-20)
- [ ] Pruebas de carga
- [ ] Pruebas de seguridad
- [ ] Capacitación usuarios
- [ ] Go-live piloto
- [ ] Ajustes finales

---

## Scripts de Instalación Automática

El sistema incluirá scripts bash para:
1. `install_dependencies.sh` - Instala todo el software base
2. `setup_database.sh` - Configura PostgreSQL y crea DB
3. `deploy_orthanc.sh` - Descarga y configura Orthanc
4. `deploy_openelis.sh` - Descarga y configura OpenELIS
5. `init_super_root.sh` - Crea usuario root inicial
6. `configure_ssl.sh` - Genera certificados SSL

---

## Consideraciones de Diseño UI/UX

### Principios Modernos
- **Glassmorphism:** Efectos de vidrio esmerilado
- **Gradientes sutiles:** Profundidad visual
- **Micro-interacciones:** Feedback inmediato
- **Dark mode:** Opción configurable
- **Responsive:** Mobile-first
- **Accesibilidad:** WCAG 2.1 AA

### Componentes Clave
- Dashboard con widgets arrastrables
- Tablas virtuales (renderizado eficiente)
- Modales no bloqueantes
- Notificaciones toast
- Skeletons de carga
- Búsqueda global instantánea

### Personalización por Sucursal
- Logo en login y header
- Paleta de colores corporativa
- Formato de facturas
- Plantillas de resultados
- Mensajes personalizados

---

## Recomendaciones Adicionales Christhz 3.0

1. **Cola de Impresión Asíncrona:** Usar Celery para imprimir sin bloquear UI
2. **Auditoría Forense:** Log inmutable de todas las acciones críticas
3. **Backup Automático:** Script diario a S3/NAS externo
4. **Monitorización:** Prometheus + Grafana para métricas en tiempo real
5. **CDN Local:** Para servir assets estáticos rápidamente
6. **Compresión DICOM:** JPEG2000 para reducir almacenamiento 80%
7. **Indexación Full-Text:** PostgreSQL GIN para búsquedas rápidas
8. **Rate Limiting:** Proteger APIs contra abuso
9. **Health Checks:** Endpoints para monitoreo de servicios
10. **Documentación Swagger:** Auto-generada para todas las APIs

---

**Estado:** Arquitectura completada. Listo para comenzar implementación fase 1.
