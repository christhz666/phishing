# MediTech System

## Sistema Integral de Gestión Médica - Open Source

![Versión](https://img.shields.io/badge/versión-1.0.0-blue)
![Licencia](https://img.shields.io/badge/licencia-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![React](https://img.shields.io/badge/react-18+-cyan)

---

## 🏥 Descripción

MediTech System es una plataforma integral de gestión para clínicas y hospitales que combina:

- **HIS** (Hospital Information System) - Gestión administrativa y clínica
- **PACS** (Picture Archiving and Communication System) - Imágenes médicas
- **LIS** (Laboratory Information System) - Laboratorio clínico
- **Facturación** - Ciclo completo de ingresos

Todo integrado en una sola interfaz moderna y fácil de usar.

---

## ✨ Características Principales

### 🏢 Multi-Sucursal
- Cada sucursal opera con IDs independientes (4-5 dígitos)
- Configuración personalizada por sucursal (logos, colores, plantillas)
- Usuarios y roles específicos por ubicación

### 👥 Gestión de Pacientes
- Búsqueda por nombre, cédula o ID
- Soporte para menores sin cédula
- Historial clínico completo
- Contacto de emergencia

### 💰 Facturación Inteligente
- IDs únicos por factura vinculados a estudios específicos
- Códigos QR y de barras para búsqueda rápida
- Integración con seguros médicos
- Control de pagos pendientes
- Múltiples formas de pago (efectivo, tarjeta, PayPal)

### 🔬 Laboratorio Clínico (OpenELIS)
- Conexión directa con analizadores automáticos
- Captura automática de resultados vía HL7/ASTM
- Validación por profesionales
- Plantillas personalizables

### 📷 Imágenes Médicas (Orthanc + OHIF)
- Almacenamiento DICOM centralizado
- Visor web integrado
- Reportes radiológicos
- Compresión inteligente

### 🔐 Seguridad y Roles
- **SUPER_ROOT**: Acceso total inicial
- **ADMIN**: Gestión de sucursal
- **RECEPCION**: Registro y facturación
- **DOCTOR**: Validación y historial
- **LABORATORIO**: Procesamiento muestras
- **IMAGENES**: Estudios radiológicos
- **CAJA**: Cobros y reportes

### 🎨 UI/UX Moderno
- Diseño glassmorphism
- Dark mode opcional
- Totalmente responsive
- Animaciones fluidas
- Accesible (WCAG 2.1 AA)

---

## 🛠️ Stack Tecnológico

### Backend
- **Python 3.11+** con **FastAPI**
- **PostgreSQL 15** como base de datos
- **SQLAlchemy 2.0** ORM
- **Redis** para cache y colas
- **Celery** para tareas asíncronas
- **JWT** para autenticación

### Frontend
- **React 18** con **TypeScript**
- **Vite** como build tool
- **Tailwind CSS** para estilos
- **Zustand** para estado
- **React Query** para data fetching
- **Framer Motion** para animaciones

### Infraestructura
- **Orthanc** - Servidor PACS/DICOM
- **OpenELIS Global 2** - Sistema LIS
- **OHIF Viewer v3** - Visor de imágenes
- **Nginx** - Reverse proxy
- **Supervisor** - Gestión de procesos

---

## 🚀 Instalación Rápida

### Requisitos Previos
- Ubuntu 22.04 LTS o Debian 12
- 4GB RAM mínimo (8GB recomendado)
- 50GB espacio en disco
- Conexión a internet

### Pasos de Instalación

```bash
# Clonar repositorio
cd /workspace
git clone <repo-url> meditech-system
cd meditech-system

# Ejecutar instalador automático (como root)
sudo bash scripts/install.sh
```

El script realizará:
1. ✅ Instalación de dependencias del sistema
2. ✅ Configuración de PostgreSQL y Redis
3. ✅ Despliegue de Orthanc (PACS)
4. ✅ Configuración del backend Python
5. ✅ Setup de Nginx como proxy
6. ✅ Creación de servicios systemd

### Primer Inicio

```bash
# Crear usuario super_root
python /opt/meditech/backend/scripts/create_super_root.py

# Acceder al sistema
# Frontend: http://localhost
# API Docs: http://localhost/api/docs
# Orthanc: http://localhost:8042
```

---

## 📁 Estructura del Proyecto

```
meditech-system/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── api/            # Endpoints REST
│   │   ├── core/           # Configuración
│   │   ├── models/         # Modelos SQLAlchemy
│   │   ├── services/       # Lógica de negocio
│   │   └── integrations/   # Orthanc, OpenELIS
│   ├── tests/
│   └── requirements.txt
├── frontend/               # React + TypeScript
│   ├── src/
│   │   ├── components/    # Componentes reutilizables
│   │   ├── pages/         # Vistas principales
│   │   ├── context/       # Contextos React
│   │   └── styles/        # Estilos globales
│   └── package.json
├── scripts/               # Scripts de instalación
├── docs/                  # Documentación
└── config/                # Configuraciones ejemplo
```

---

## 🔌 Integraciones

### Con Equipos de Laboratorio

Los analizadores se conectan directamente:

```
Analizador → TCP/IP → OpenELIS → MediTech HIS
     (HL7 v2.x o ASTM)
```

**Equipos soportados:**
- Sysmex (hematología)
- Roche (química clínica)
- Abbott (inmunología)
- Beckman Coulter
- Y más mediante middleware Mirth Connect

### Con Modalidades de Imágenes

```
Modalidad → DICOM → Orthanc → MediTech HIS → OHIF Viewer
```

**Soporta:**
- Rayos X digitales
- Tomografía (CT)
- Resonancia (MRI)
- Ultrasonido
- Mamografía

---

## 📊 Flujo de Trabajo Típico

### 1. Registro de Paciente
```
Recepción → Buscar paciente → Nuevo registro → Sucursal actual
```

### 2. Orden de Estudios
```
Seleccionar estudios → Ver precios → Confirmar → Facturación
```

### 3. Facturación
```
Generar factura → ID único (ej: 05021) → QR + Código barras → Pago
```

### 4. Ejecución
```
Orden automática a LIS/PACS → Toma de muestra/estudio → Resultado automático
```

### 5. Entrega
```
Validación profesional → Disponible → Búsqueda por QR/código/nombre
```

---

## 🔒 Consideraciones de Seguridad

- **Encriptación**: BCrypt para contraseñas, TLS para comunicaciones
- **Auditoría**: Log forense de todas las acciones
- **Backups**: Automáticos diarios configurables
- **Rate Limiting**: Protección contra abuso de APIs
- **RBAC**: Control de acceso basado en roles granular

---

## 📖 Documentación Completa

- [Arquitectura del Sistema](docs/ARQUITECTURACompleta.md)
- [Guía de Instalación](docs/INSTALACION.md)
- [Manual de Usuario](docs/MANUAL_USUARIO.md)
- [API Reference](http://localhost/api/docs)

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📄 Licencia

Distribuido bajo la licencia MIT. Ver `LICENSE` para más información.

---

## 👨‍💻 Desarrollado por

**Christhz 3.0** - *Arquitecto Senior HealthTech*

Con la visión de **Christhz 1.0**

---

## 🆘 Soporte

Para issues y preguntas:
- GitHub Issues: [Link]
- Email: soporte@meditech.system
- Documentación: https://docs.meditech.system

---

## 🎯 Roadmap

- [ ] Telemedicina integrada
- [ ] App móvil pacientes
- [ ] Facturación electrónica fiscal
- [ ] IA para diagnóstico asistido
- [ ] Interoperabilidad FHIR completa
- [ ] Marketplace de plugins

---

**Hecho con ❤️ para mejorar la salud global**
