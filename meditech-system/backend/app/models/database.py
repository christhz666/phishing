from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, DECIMAL, Text, ForeignKey, JSON, Date, CHAR, Enum as SQLEnum, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import uuid
import enum
from typing import Optional

Base = declarative_base()


class RoleType(str, enum.Enum):
    """Tipos de roles del sistema"""
    SUPER_ROOT = "super_root"
    ADMIN = "admin"
    RECEPCION = "recepcion"
    DOCTOR = "doctor"
    LAB = "laboratorio"
    RADIOLOGO = "radiologo"
    CONTABILIDAD = "contabilidad"


class InvoiceStatus(str, enum.Enum):
    """Estados de la factura"""
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    """Métodos de pago"""
    CASH = "cash"
    CARD = "card"
    PAYPAL = "paypal"
    INSURANCE = "insurance"
    TRANSFER = "transfer"


def generate_uuid():
    return str(uuid.uuid4())


def generate_short_id(branch_code: str, consecutive: int) -> str:
    """Genera ID único de 4-5 dígitos por sucursal"""
    return f"{consecutive:04d}" if consecutive < 10000 else f"{consecutive:05d}"


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
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=True)  # NULL = rol global
    nombre = Column(String(50), nullable=False)
    descripcion = Column(Text)
    role_type = Column(SQLEnum(RoleType), nullable=False)
    permisos = Column(JSON, default={})
    creado_por_id = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    users = relationship("User", back_populates="role")
    
    __table_args__ = (
        UniqueConstraint('nombre', 'branch_id', name='unique_role_per_branch'),
        Index('idx_role_branch', 'branch_id'),
    )


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
    """Facturas con ID único por sucursal (4-5 dígitos)"""
    __tablename__ = "invoices"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=False)
    consecutivo_sucursal = Column(Integer, nullable=False)
    codigo_unico = Column(String(10), nullable=False)  # Ej: "05021" - ID de 4-5 dígitos
    paciente_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    usuario_crea_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    fecha_emision = Column(DateTime, default=datetime.utcnow)
    estado = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.PENDING)
    subtotal = Column(DECIMAL(10, 2), default=0)
    seguro_cobertura_percent = Column(DECIMAL(5, 2), default=0)  # % cobertura seguro
    seguro_nombre = Column(String(200))
    seguro_poliza = Column(String(100))
    seguro_monto = Column(DECIMAL(10, 2), default=0)
    paciente_monto = Column(DECIMAL(10, 2), default=0)
    descuento = Column(DECIMAL(10, 2), default=0)
    impuesto = Column(DECIMAL(10, 2), default=0)
    total = Column(DECIMAL(10, 2), default=0)
    monto_pagado = Column(DECIMAL(10, 2), default=0)
    saldo_pendiente = Column(DECIMAL(10, 2), default=0)
    codigo_barras = Column(String(100), unique=True, nullable=False)
    codigo_qr = Column(String(500), unique=True, nullable=False)
    observaciones = Column(Text)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = Column(DateTime)  # Fecha de pago completo
    
    # Relaciones
    branch = relationship("Branch", back_populates="invoices")
    patient = relationship("Patient", back_populates="invoices")
    creator = relationship("User", foreign_keys=[usuario_crea_id])
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan", lazy="dynamic")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan", lazy="dynamic")
    
    __table_args__ = (
        UniqueConstraint('branch_id', 'codigo_unico', name='unique_invoice_per_branch'),
        Index('idx_invoice_branch', 'branch_id'),
        Index('idx_invoice_patient', 'paciente_id'),
        Index('idx_invoice_estado', 'estado'),
        Index('idx_invoice_barcode', 'codigo_barras'),
        Index('idx_invoice_created', 'created_at'),
    )


class InvoiceItem(Base):
    """Detalle de factura - Liga estudios a factura"""
    __tablename__ = "invoice_items"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False)
    service_id = Column(String(36), ForeignKey("services.id"), nullable=False)
    study_name = Column(String(200), nullable=False)  # Copia del nombre al facturar
    study_code = Column(String(50))
    cantidad = Column(Integer, default=1)
    precio_unitario = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    estado_resultado = Column(String(20), default="PENDIENTE")  # PENDIENTE, DISPONIBLE, VALIDADO
    openelis_order_id = Column(String(100))  # Referencia a OpenELIS LIS
    orthanc_study_uid = Column(String(64))  # Referencia a Orthanc PACS
    result_pdf_url = Column(String(500))
    dicom_viewer_url = Column(String(500))
    notas = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    invoice = relationship("Invoice", back_populates="items")
    service = relationship("Service", back_populates="invoice_items")
    results = relationship("Result", back_populates="invoice_item", lazy="dynamic")
    
    __table_args__ = (
        Index('idx_item_invoice', 'invoice_id'),
        Index('idx_item_result_estado', 'estado_resultado'),
    )


class Payment(Base):
    """Pagos realizados a facturas"""
    __tablename__ = "payments"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=False)
    monto = Column(DECIMAL(10, 2), nullable=False)
    metodo_pago = Column(SQLEnum(PaymentMethod), nullable=False)
    fecha_pago = Column(DateTime, default=datetime.utcnow)
    numero_referencia = Column(String(200))
    notas = Column(Text)
    procesado_por_id = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    invoice = relationship("Invoice", back_populates="payments")
    processor = relationship("User", foreign_keys=[procesado_por_id])
    
    __table_args__ = (
        Index('idx_payment_invoice', 'invoice_id'),
        Index('idx_payment_fecha', 'fecha_pago'),
    )


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
