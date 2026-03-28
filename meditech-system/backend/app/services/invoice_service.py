"""
Servicios de Negocio para Facturación
Genera IDs únicos por sucursal, códigos QR/barras, gestiona pagos
"""
from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
import qrcode
import barcode
from barcode.writer import ImageWriter
import io
import base64

from app.models.database import (
    Invoice, InvoiceItem, InvoiceStatus, Payment, PaymentMethod,
    Patient, StudyCatalog, Branch
)
from app.schemas import InvoiceCreate, InvoicePayment


def get_next_invoice_id(db: Session, branch_id: int) -> Tuple[int, str]:
    """
    Obtiene el siguiente ID consecutivo para una sucursal
    Retorna (consecutivo, codigo_unico formateado)
    """
    # Obtener el máximo consecutivo actual para esta sucursal
    max_consecutive = db.query(func.max(Invoice.consecutivo_sucursal)).filter(
        Invoice.branch_id == branch_id
    ).scalar()
    
    next_consecutive = (max_consecutive or 0) + 1
    
    # Formatear como 4-5 dígitos
    if next_consecutive < 10000:
        codigo_unico = f"{next_consecutive:04d}"
    else:
        codigo_unico = f"{next_consecutive:05d}"
    
    return next_consecutive, codigo_unico


def generate_barcode_data(invoice_id: str, branch_code: str) -> str:
    """Genera datos para código de barras (Code128)"""
    # Formato: BRANCH-ID-TIMESTAMP
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{branch_code}-{invoice_id}-{timestamp}"


def generate_qr_data(invoice_id: str, branch_code: str, patient_id: int) -> str:
    """
    Genera datos para código QR
    Incluye URL de verificación y datos encriptados
    """
    # En producción esto sería una URL real con token seguro
    base_url = "https://results.meditech.com/verify"
    data = f"{base_url}?id={invoice_id}&b={branch_code}&p={patient_id}"
    return data


def create_barcode_image(data: str) -> str:
    """Crea imagen de código de barras y retorna en base64"""
    try:
        # Usar Code128 que es estándar para facturación
        code = barcode.get('code128', data, writer=ImageWriter())
        
        buffer = io.BytesIO()
        code.write(buffer, options={'module_width': 0.4, 'module_height': 15.0})
        buffer.seek(0)
        
        # Convertir a base64
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        # Fallback: retornar solo los datos
        return data


def create_qr_image(data: str) -> str:
    """Crea imagen de código QR y retorna en base64"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Convertir a base64
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        return data


def calculate_invoice_totals(
    items: List[dict],
    insurance_coverage_percent: float = 0
) -> dict:
    """
    Calcula totales de factura con seguro
    Retorna: subtotal, insurance_amount, patient_amount, total
    """
    subtotal = sum(item['quantity'] * item['unit_price'] for item in items)
    
    insurance_amount = subtotal * (insurance_coverage_percent / 100)
    patient_amount = subtotal - insurance_amount
    
    # Aquí se podría agregar impuestos si es necesario
    tax = 0  # impuesto
    total = subtotal  # o subtotal + tax según normativa
    
    return {
        'subtotal': round(subtotal, 2),
        'insurance_coverage_percent': insurance_coverage_percent,
        'insurance_amount': round(insurance_amount, 2),
        'patient_amount': round(patient_amount, 2),
        'tax': round(tax, 2),
        'total': round(total, 2)
    }


def check_invoice_payment_status(invoice: Invoice) -> InvoiceStatus:
    """Determina el estado de pago de la factura"""
    if invoice.monto_pagado <= 0:
        return InvoiceStatus.PENDING
    elif invoice.monto_pagado < invoice.total:
        return InvoiceStatus.PARTIAL
    else:
        return InvoiceStatus.PAID


def can_access_results(invoice: Invoice) -> bool:
    """Verifica si se pueden entregar resultados (factura pagada)"""
    return invoice.estado == InvoiceStatus.PAID


class InvoiceService:
    """Servicio principal para gestión de facturas"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_invoice(
        self,
        invoice_data: InvoiceCreate,
        branch_id: int,
        user_id: int
    ) -> Invoice:
        """Crea una nueva factura con todos sus items"""
        
        # Obtener sucursal para código
        branch = self.db.query(Branch).filter(Branch.id == branch_id).first()
        if not branch:
            raise ValueError("Sucursal no encontrada")
        
        # Verificar paciente
        patient = self.db.query(Patient).filter(
            Patient.id == invoice_data.patient_id,
            Patient.branch_id == branch_id
        ).first()
        if not patient:
            raise ValueError("Paciente no encontrado en esta sucursal")
        
        # Obtener siguiente ID único
        consecutive, codigo_unico = get_next_invoice_id(self.db, branch_id)
        
        # Calcular totales
        items_data = []
        for item in invoice_data.items:
            study = self.db.query(StudyCatalog).filter(
                StudyCatalog.id == item.study_catalog_id,
                StudyCatalog.branch_id == branch_id
            ).first()
            if not study:
                raise ValueError(f"Estudio {item.study_catalog_id} no encontrado")
            
            items_data.append({
                'study_catalog_id': study.id,
                'study_name': study.name,
                'study_code': study.code,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
            })
        
        totals = calculate_invoice_totals(
            items_data,
            invoice_data.insurance_coverage_percent
        )
        
        # Generar códigos
        barcode_data = generate_barcode_data(codigo_unico, branch.code)
        qr_data = generate_qr_data(codigo_unico, branch.code, patient.id)
        
        # Crear factura
        invoice = Invoice(
            branch_id=branch_id,
            consecutivo_sucursal=consecutive,
            codigo_unico=codigo_unico,
            paciente_id=invoice_data.patient_id,
            usuario_crea_id=user_id,
            estado=InvoiceStatus.PENDING,
            subtotal=totals['subtotal'],
            seguro_cobertura_percent=invoice_data.insurance_coverage_percent,
            seguro_nombre=invoice_data.insurance_name,
            seguro_poliza=invoice_data.insurance_policy_number,
            seguro_monto=totals['insurance_amount'],
            paciente_monto=totals['patient_amount'],
            total=totals['total'],
            monto_pagado=0,
            saldo_pendiente=totals['total'],
            codigo_barras=barcode_data,
            codigo_qr=qr_data,
            observaciones=invoice_data.notes,
            metadata={'items_count': len(items_data)}
        )
        
        self.db.add(invoice)
        self.db.flush()  # Para obtener el ID
        
        # Crear items
        for item_data in items_data:
            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                service_id=item_data['study_catalog_id'],
                study_name=item_data['study_name'],
                study_code=item_data['study_code'],
                cantidad=item_data['quantity'],
                precio_unitario=item_data['unit_price'],
                subtotal=item_data['quantity'] * item_data['unit_price'],
                estado_resultado='PENDIENTE'
            )
            self.db.add(invoice_item)
        
        self.db.commit()
        self.db.refresh(invoice)
        
        return invoice
    
    def register_payment(
        self,
        invoice_id: int,
        payment_data: InvoicePayment,
        user_id: int
    ) -> Payment:
        """Registra un pago a una factura"""
        
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError("Factura no encontrada")
        
        if invoice.estado == InvoiceStatus.CANCELLED:
            raise ValueError("No se puede pagar una factura cancelada")
        
        if payment_data.amount > invoice.saldo_pendiente:
            raise ValueError(
                f"El monto excede el saldo pendiente ({invoice.saldo_pendiente})"
            )
        
        # Crear pago
        payment = Payment(
            invoice_id=invoice_id,
            monto=payment_data.amount,
            metodo_pago=payment_data.payment_method,
            numero_referencia=payment_data.reference_number,
            notas=payment_data.notes,
            procesado_por_id=user_id
        )
        
        self.db.add(payment)
        
        # Actualizar factura
        invoice.monto_pagado += payment_data.amount
        invoice.saldo_pendiente -= payment_data.amount
        
        # Actualizar estado
        invoice.estado = check_invoice_payment_status(invoice)
        
        if invoice.estado == InvoiceStatus.PAID:
            invoice.paid_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(invoice)
        
        return payment
    
    def search_invoices(
        self,
        term: str,
        branch_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Invoice]:
        """
        Busca facturas por:
        - ID local (4-5 dígitos)
        - Código de barras
        - Código QR
        - Nombre de paciente
        - Cédula
        """
        query = self.db.query(Invoice).join(Patient)
        
        # Filtrar por sucursal si se especifica
        if branch_id:
            query = query.filter(Invoice.branch_id == branch_id)
        
        # Búsqueda flexible
        term_upper = term.upper().strip()
        
        results = query.filter(
            (Invoice.codigo_unico == term) |
            (Invoice.codigo_barras.like(f"%{term}%")) |
            (Invoice.codigo_qr.like(f"%{term}%")) |
            (func.upper(Patient.first_name).like(f"%{term_upper}%")) |
            (func.upper(Patient.last_name).like(f"%{term_upper}%")) |
            (Patient.id_number == term_upper)
        ).order_by(Invoice.created_at.desc()).limit(limit).all()
        
        return results
    
    def get_patient_history(
        self,
        patient_id: int,
        branch_id: Optional[int] = None
    ) -> List[Invoice]:
        """Obtiene historial completo de facturas de un paciente"""
        query = self.db.query(Invoice).filter(Invoice.paciente_id == patient_id)
        
        if branch_id:
            query = query.filter(Invoice.branch_id == branch_id)
        
        return query.order_by(Invoice.created_at.desc()).all()
    
    def get_invoice_results(
        self,
        invoice_id: int
    ) -> List[InvoiceItem]:
        """
        Obtiene resultados de una factura
        Solo si está completamente pagada
        """
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()
        
        if not invoice:
            raise ValueError("Factura no encontrada")
        
        if not can_access_results(invoice):
            raise ValueError(
                "Resultados no disponibles - Factura pendiente de pago"
            )
        
        results = self.db.query(InvoiceItem).filter(
            InvoiceItem.invoice_id == invoice_id,
            InvoiceItem.estado_resultado == 'VALIDADO'
        ).all()
        
        return results
