from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, DECIMAL, Text, ForeignKey, JSON, Date, CHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import uuid
from typing import Optional

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class Branch(Base):
    """Sucursales del sistema"""
    __tablename__ = "branches"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    codigo = Column(String(10), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    direccion = Column(Text)
    telefono = Column(String(20))
    email = Column(String(100))
    logo = Column(String(255))
    configuracion = Column(JSON, default={})
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    patients = relationship("Patient", back_populates="branch")
    users = relationship("User", back_populates="branch")
    services = relationship("Service", back_populates="branch")
    invoices = relationship("Invoice", back_populates="branch")
    results = relationship("Result", back_populates="branch")


class Patient(Base):
    """Pacientes del sistema"""
    __tablename__ = "patients"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=False)
    primer_nombre = Column(String(50), nullable=False)
    segundo_nombre = Column(String(50))
    primer_apellido = Column(String(50), nullable=False)
    segundo_apellido = Column(String(50))
    fecha_nacimiento = Column(Date, nullable=False)
    sexo = Column(CHAR(1))  # M, F, O
    tipo_sangre = Column(String(5))
    cedula = Column(String(20))  # NULL para menores
    es_menor = Column(Boolean, default=False)
    telefono = Column(String(20))
    email = Column(String(100))
    direccion = Column(Text)
    contacto_emergencia = Column(JSON, default={})
    historial_medico = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    branch = relationship("Branch", back_populates="patients")
    invoices = relationship("Invoice", back_populates="patient")
    results = relationship("Result", back_populates="patient")


class Role(Base):
    """Roles del sistema con permisos granulares"""
    __tablename__ = "roles"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    permisos = Column(JSON, default={})
    creado_por_id = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    users = relationship("User", back_populates="role")


class User(Base):
    """Usuarios del sistema"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    primer_nombre = Column(String(50), nullable=False)
    apellidos = Column(String(100), nullable=False)
    rol_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    activo = Column(Boolean, default=True)
    ultimo_acceso = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    branch = relationship("Branch", back_populates="users")
    role = relationship("Role", back_populates="users")
    invoices_created = relationship("Invoice", back_populates="creator")
    validated_results = relationship("Result", back_populates="validator")


class Service(Base):
    """Servicios/Estudios disponibles"""
    __tablename__ = "services"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=False)
    codigo = Column(String(20), nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    categoria = Column(String(50))  # LABORATORIO, IMAGENES, CONSULTA
    precio_base = Column(DECIMAL(10, 2), nullable=False)
    requiere_muestra = Column(Boolean, default=False)
    tiempo_entrega_horas = Column(Integer, default=24)
    codigo_cpt = Column(String(10))
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    branch = relationship("Branch", back_populates="services")
    invoice_items = relationship("InvoiceItem", back_populates="service")


class Invoice(Base):
    """Facturas con ID único por sucursal"""
    __tablename__ = "invoices"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=False)
    consecutivo_sucursal = Column(Integer, nullable=False)
    codigo_unico = Column(String(10), nullable=False)  # Ej: "05021"
    paciente_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    usuario_crea_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    fecha_emision = Column(DateTime, default=datetime.utcnow)
    estado = Column(String(20), default="PENDIENTE")  # PENDIENTE, PARCIAL, PAGADA, CANCELADA
    subtotal = Column(DECIMAL(10, 2), default=0)
    descuento = Column(DECIMAL(10, 2), default=0)
    impuesto = Column(DECIMAL(10, 2), default=0)
    total = Column(DECIMAL(10, 2), default=0)
    saldo_pendiente = Column(DECIMAL(10, 2), default=0)
    codigo_barras = Column(String(100), unique=True)
    codigo_qr = Column(String(255))
    observaciones = Column(Text)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    branch = relationship("Branch", back_populates="invoices")
    patient = relationship("Patient", back_populates="invoices")
    creator = relationship("User", back_populates="invoices_created")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    """Detalle de factura - Liga estudios a factura"""
    __tablename__ = "invoice_items"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    factura_id = Column(String(36), ForeignKey("invoices.id"), nullable=False)
    servicio_id = Column(String(36), ForeignKey("services.id"), nullable=False)
    cantidad = Column(Integer, default=1)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    estado_resultado = Column(String(20), default="PENDIENTE")
    orden_laboratorio_id = Column(String(36))  # Referencia a OpenELIS
    estudio_pacs_uid = Column(String(64))  # Referencia a Orthanc
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    invoice = relationship("Invoice", back_populates="items")
    service = relationship("Service", back_populates="invoice_items")
    results = relationship("Result", back_populates="invoice_item")


class Result(Base):
    """Resultados de laboratorio/imágenes"""
    __tablename__ = "results"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    factura_detalle_id = Column(String(36), ForeignKey("invoice_items.id"), nullable=False)
    paciente_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=False)
    tipo = Column(String(20), nullable=False)  # LABORATORIO, IMAGEN
    datos_resultado = Column(JSON, default={})
    archivo_pdf = Column(String(255))
    imagenes_urls = Column(JSON, default=[])
    validado_por_id = Column(String(36), ForeignKey("users.id"))
    fecha_validacion = Column(DateTime)
    visible_portal = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    invoice_item = relationship("InvoiceItem", back_populates="results")
    patient = relationship("Patient", back_populates="results")
    branch = relationship("Branch", back_populates="results")
    validator = relationship("User", back_populates="validated_results")


class AuditLog(Base):
    """Registro de auditoría forense"""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    usuario_id = Column(String(36), ForeignKey("users.id"))
    accion = Column(String(50), nullable=False)
    modulo = Column(String(50))
    registro_id = Column(String(36))
    detalles = Column(JSON, default={})
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
