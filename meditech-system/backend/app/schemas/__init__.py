"""
Pydantic Schemas para validación de datos
"""
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class RoleType(str, Enum):
    SUPER_ROOT = "super_root"
    ADMIN = "admin"
    RECEPCION = "recepcion"
    DOCTOR = "doctor"
    LAB = "laboratorio"
    RADIOLOGO = "radiologo"
    CONTABILIDAD = "contabilidad"


class InvoiceStatus(str, Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    PAYPAL = "paypal"
    INSURANCE = "insurance"
    TRANSFER = "transfer"


# ==================== BRANCH SCHEMAS ====================

class BranchBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=2, max_length=20)
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    logo_url: Optional[str] = None


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    logo_url: Optional[str] = None
    active: Optional[bool] = None


class BranchResponse(BranchBase):
    id: int
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== ROLE SCHEMAS ====================

class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    role_type: RoleType
    permissions: Dict[str, bool] = {}


class RoleCreate(RoleBase):
    branch_id: Optional[int] = None


class RoleResponse(RoleBase):
    id: int
    branch_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== USER SCHEMAS ====================

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=200)
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role_id: int
    branch_id: int


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    role_id: int
    branch_id: int
    active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    role_type: Optional[str] = None
    branch_id: Optional[int] = None


# ==================== PATIENT SCHEMAS ====================

class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = None
    second_last_name: Optional[str] = None
    id_number: Optional[str] = Field(None, max_length=50)  # Cédula opcional
    birth_date: Optional[date] = None
    gender: Optional[str] = Field(None, pattern="^(M|F|Other)$")
    blood_type: Optional[str] = Field(None, max_length=10)
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[str] = None
    
    @validator('id_number')
    def validate_id_number(cls, v):
        if v is not None:
            v_upper = v.upper().strip()
            if v_upper == "MENOR":
                return None  # NULL para menores
            return v_upper
        return v


class PatientCreate(PatientBase):
    branch_id: int


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    second_last_name: Optional[str] = None
    id_number: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[str] = None
    active: Optional[bool] = None


class PatientResponse(PatientBase):
    id: int
    branch_id: int
    full_name: str
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PatientSearch(BaseModel):
    term: str
    branch_id: Optional[int] = None
    limit: int = Field(20, ge=1, le=100)


# ==================== STUDY CATALOG SCHEMAS ====================

class StudyCatalogBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    category: Optional[str] = Field(None, max_length=100)
    requires_sample: bool = False
    requires_prep: bool = False
    prep_instructions: Optional[str] = None
    turnaround_time_hours: int = Field(24, ge=1)


class StudyCatalogCreate(StudyCatalogBase):
    branch_id: int


class StudyCatalogUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    requires_sample: Optional[bool] = None
    requires_prep: Optional[bool] = None
    prep_instructions: Optional[str] = None
    turnaround_time_hours: Optional[int] = None
    active: Optional[bool] = None


class StudyCatalogResponse(StudyCatalogBase):
    id: int
    branch_id: int
    active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== INVOICE SCHEMAS ====================

class InvoiceItemCreate(BaseModel):
    study_catalog_id: int
    quantity: int = Field(1, ge=1)
    unit_price: float = Field(..., ge=0)
    notes: Optional[str] = None


class InvoiceCreate(BaseModel):
    patient_id: int
    items: List[InvoiceItemCreate]
    insurance_name: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_coverage_percent: float = Field(0, ge=0, le=100)
    notes: Optional[str] = None


class InvoicePayment(BaseModel):
    amount: float = Field(..., gt=0)
    payment_method: PaymentMethod
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class InvoiceItemResponse(BaseModel):
    id: int
    invoice_id: int
    study_catalog_id: Optional[int]
    study_name: str
    study_code: Optional[str]
    quantity: int
    unit_price: float
    total_price: float
    estado_resultado: str
    openelis_order_id: Optional[str]
    orthanc_study_uid: Optional[str]
    result_pdf_url: Optional[str]
    dicom_viewer_url: Optional[str]
    notas: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    id: int
    invoice_id: int
    amount: float
    payment_method: PaymentMethod
    payment_date: datetime
    reference_number: Optional[str]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    id: int
    branch_id: int
    invoice_id_local: str  # ID de 4-5 dígitos
    patient_id: int
    patient_name: str
    status: InvoiceStatus
    subtotal: float
    insurance_coverage_percent: float
    insurance_amount: float
    patient_amount: float
    total: float
    amount_paid: float
    balance: float
    insurance_name: Optional[str]
    insurance_policy_number: Optional[str]
    notes: Optional[str]
    barcode: str
    qr_code: str
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    items: List[InvoiceItemResponse] = []
    payments: List[PaymentResponse] = []
    
    class Config:
        from_attributes = True


class InvoiceSearchResult(BaseModel):
    id: int
    branch_id: int
    invoice_id_local: str
    patient_name: str
    patient_id_number: Optional[str]
    status: InvoiceStatus
    total: float
    balance: float
    created_at: datetime
    barcode: str
    has_results: bool


# ==================== RESULT SCHEMAS ====================

class ResultData(BaseModel):
    test_name: str
    value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    flag: Optional[str] = None  # H, L, A (High, Low, Abnormal)
    additional_data: Optional[Dict[str, Any]] = None


class ResultCreate(BaseModel):
    invoice_item_id: int
    tipo: str = Field(..., pattern="^(LABORATORIO|IMAGEN)$")
    datos_resultado: List[ResultData] = []
    archivo_pdf: Optional[str] = None
    imagenes_urls: List[str] = []
    notas: Optional[str] = None


class ResultUpdate(BaseModel):
    datos_resultado: Optional[List[ResultData]] = None
    archivo_pdf: Optional[str] = None
    imagenes_urls: Optional[List[str]] = None
    notas: Optional[str] = None
    visible_portal: Optional[bool] = None


class ResultResponse(BaseModel):
    id: int
    invoice_item_id: int
    patient_id: int
    branch_id: int
    tipo: str
    datos_resultado: Dict[str, Any]
    archivo_pdf: Optional[str]
    imagenes_urls: List[str]
    validado_por_id: Optional[int]
    fecha_validacion: Optional[datetime]
    visible_portal: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== AUDIT SCHEMAS ====================

class AuditLogCreate(BaseModel):
    user_id: Optional[int] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    details: Dict[str, Any]
    ip_address: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== SYSTEM CONFIG SCHEMAS ====================

class SystemConfigBase(BaseModel):
    config_key: str = Field(..., min_length=1, max_length=100)
    config_value: str
    config_type: str = Field("string", pattern="^(string|json|boolean|integer)$")
    description: Optional[str] = None


class SystemConfigCreate(SystemConfigBase):
    branch_id: Optional[int] = None


class SystemConfigResponse(SystemConfigBase):
    id: int
    branch_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ==================== ROOT SETUP SCHEMA ====================

class RootSetupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    branch_name: str = Field(..., min_length=1, max_length=200)
    branch_code: str = Field(..., min_length=2, max_length=20)
