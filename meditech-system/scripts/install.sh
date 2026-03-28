#!/bin/bash

# ============================================
# MediTech System - Script de Instalación
# ============================================
# Este script instala todas las dependencias necesarias
# para ejecutar el sistema MediTech sin Docker

set -e

echo "============================================"
echo "  MediTech System - Instalador"
echo "============================================"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Verificar si es root
if [ "$EUID" -ne 0 ]; then 
    print_error "Por favor ejecuta como root (sudo ./install.sh)"
    exit 1
fi

# Actualizar paquetes
print_info "Actualizando paquetes del sistema..."
apt-get update -qq

# Instalar dependencias del sistema
print_info "Instalando dependencias del sistema..."
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    nginx \
    redis-server \
    curl \
    wget \
    git \
    unzip \
    dcmtk \
    vim \
    supervisor \
    || true

print_success "Dependencias del sistema instaladas"

# Configurar PostgreSQL
print_info "Configurando PostgreSQL..."
systemctl enable postgresql
systemctl start postgresql

# Crear usuario y base de datos
sudo -u postgres psql -c "CREATE USER meditech_user WITH PASSWORD 'meditech_password';" || true
sudo -u postgres psql -c "CREATE DATABASE meditech_db OWNER meditech_user;" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE meditech_db TO meditech_user;" || true

print_success "PostgreSQL configurado"

# Configurar Redis
print_info "Configurando Redis..."
systemctl enable redis-server
systemctl start redis-server

print_success "Redis configurado"

# Crear directorios necesarios
print_info "Creando directorios..."
mkdir -p /var/meditech/{uploads,results,logs}
mkdir -p /opt/meditech/{backend,frontend,pacs,lis}
chown -R $SUDO_USER:$SUDO_USER /var/meditech
chown -R $SUDO_USER:$SUDO_USER /opt/meditech

print_success "Directorios creados"

# Instalar Orthanc (PACS)
print_info "Descargando e instalando Orthanc (PACS)..."
cd /tmp
wget -q https://orthanc.uclouvain.be/downloads/orthanc-debian-11.0.tar.gz
tar -xzf orthanc-debian-11.0.tar.gz
cd orthanc-debian-11.0
dpkg -i orthanc_*.deb || apt-get install -f -y
cd /tmp
rm -rf orthanc-debian-11.0*

# Configurar Orthanc
cat > /etc/orthanc/configuration.json << 'ORTHANC_CONFIG'
{
  "Name": "MediTech-PACS",
  "StorageDirectory": "/var/meditech/pacs-storage",
  "DatabaseDirectory": "/var/meditech/pacs-db",
  "HttpPort": 8042,
  "DicomAet": "MEDITECH",
  "DicomPort": 4242,
  "DefaultEncoding": "Latin1",
  "UserCredentials": {
    "username": "orthanc",
    "password": "orthanc123"
  },
  "RemoteModalityHosts": {},
  "OverwriteInstances": true,
  "StoreMD5ForAttachments": false,
  "LimitFindResults": 100,
  "LimitFindOrphans": 0,
  "HttpDescribeErrors": true,
  "HttpCompressionEnabled": true,
  "DicomModalities": {}
}
ORTHANC_CONFIG

mkdir -p /var/meditech/pacs-storage /var/meditech/pacs-db
chown -R orthanc:orthanc /var/meditech/pacs-storage /var/meditech/pacs-db

systemctl enable orthanc
systemctl start orthanc

print_success "Orthanc instalado y configurado"

# Instalar dependencias Python del backend
print_info "Configurando backend Python..."
cd /opt/meditech/backend

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

print_success "Backend Python configurado"

# Inicializar base de datos del backend
print_info "Inicializando base de datos..."
python -c "from app.services.database import init_db; init_db()"

print_success "Base de datos inicializada"

# Crear archivo .env
print_info "Creando configuración de entorno..."
cat > .env << 'ENV_FILE'
APP_NAME=MediTech System
DEBUG=True
DB_HOST=localhost
DB_PORT=5432
DB_NAME=meditech_db
DB_USER=meditech_user
DB_PASSWORD=meditech_password
SECRET_KEY=cambia-esta-clave-secreta-en-produccion-min-32-caracteres
REDIS_HOST=localhost
REDIS_PORT=6379
ORTHANC_URL=http://localhost:8042
ORTHANC_USERNAME=orthanc
ORTHANC_PASSWORD=orthanc123
ENV_FILE

print_success "Configuración creada"

# Configurar Nginx
print_info "Configurando Nginx..."
cat > /etc/nginx/sites-available/meditech << 'NGINX_CONFIG'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /orthanc/ {
        proxy_pass http://localhost:8042/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
NGINX_CONFIG

ln -sf /etc/nginx/sites-available/meditech /etc/nginx/sites-enabled/meditech
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl restart nginx

print_success "Nginx configurado"

# Crear servicios systemd
print_info "Creando servicios del sistema..."

# Servicio backend
cat > /etc/systemd/system/meditech-backend.service << 'BACKEND_SERVICE'
[Unit]
Description=MediTech Backend API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/meditech/backend
Environment="PATH=/opt/meditech/backend/venv/bin"
ExecStart=/opt/meditech/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
BACKEND_SERVICE

# Servicio Celery worker
cat > /etc/systemd/system/meditech-worker.service << 'WORKER_SERVICE'
[Unit]
Description=MediTech Celery Worker
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/meditech/backend
Environment="PATH=/opt/meditech/backend/venv/bin"
ExecStart=/opt/meditech/backend/venv/bin/celery -A app.celery worker --loglevel=info
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
WORKER_SERVICE

# Recargar systemd
systemctl daemon-reload
systemctl enable meditech-backend
systemctl enable meditech-worker
systemctl start meditech-backend
systemctl start meditech-worker

print_success "Servicios creados e iniciados"

# Instrucciones finales
echo ""
echo "============================================"
echo -e "${GREEN}  ¡Instalación completada exitosamente!${NC}"
echo "============================================"
echo ""
echo "Accesos:"
echo "  - Frontend: http://localhost"
echo "  - API Docs: http://localhost/api/docs"
echo "  - Orthanc:  http://localhost:8042"
echo ""
echo "Próximos pasos:"
echo "  1. Cambia la SECRET_KEY en /opt/meditech/backend/.env"
echo "  2. Ejecuta: python /opt/meditech/backend/scripts/create_super_root.py"
echo "  3. Configura OpenELIS para integración con laboratorio"
echo ""
echo "Comandos útiles:"
echo "  - Ver logs backend: journalctl -u meditech-backend -f"
echo "  - Reiniciar backend: systemctl restart meditech-backend"
echo "  - Estado servicios: systemctl status meditech-*"
echo ""
