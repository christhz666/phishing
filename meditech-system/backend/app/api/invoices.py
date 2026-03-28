from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.services.database import get_db
from app.services.invoice_service import InvoiceService
from app.schemas import (
    InvoiceCreate, InvoiceResponse, InvoiceSearchResult,
    InvoicePayment, PaymentResponse
)
from app.models.database import Invoice, InvoiceStatus
from app.services.auth import get_current_user, User

router = APIRouter()


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crea una nueva factura con estudios médicos
    
    - **patient_id**: ID del paciente
    - **items**: Lista de estudios con cantidades y precios
    - **insurance_name**: Nombre del seguro (opcional)
    - **insurance_policy_number**: Número de póliza (opcional)
    - **insurance_coverage_percent**: Porcentaje de cobertura (0-100)
    """
    service = InvoiceService(db)
    
    try:
        invoice = service.create_invoice(
            invoice_data=invoice_data,
            branch_id=current_user.branch_id,
            user_id=current_user.id
        )
        
        # Construir respuesta completa
        return {
            "id": invoice.id,
            "branch_id": invoice.branch_id,
            "invoice_id_local": invoice.codigo_unico,
            "patient_id": invoice.paciente_id,
            "patient_name": invoice.patient.full_name if invoice.patient else "Desconocido",
            "status": invoice.estado,
            "subtotal": float(invoice.subtotal),
            "insurance_coverage_percent": float(invoice.seguro_cobertura_percent),
            "insurance_amount": float(invoice.seguro_monto),
            "patient_amount": float(invoice.paciente_monto),
            "total": float(invoice.total),
            "amount_paid": float(invoice.monto_pagado),
            "balance": float(invoice.saldo_pendiente),
            "insurance_name": invoice.seguro_nombre,
            "insurance_policy_number": invoice.seguro_poliza,
            "notes": invoice.observaciones,
            "barcode": invoice.codigo_barras,
            "qr_code": invoice.codigo_qr,
            "created_by": invoice.usuario_crea_id,
            "created_at": invoice.created_at,
            "items": [
                {
                    "id": item.id,
                    "invoice_id": item.invoice_id,
                    "study_catalog_id": item.service_id,
                    "study_name": item.study_name,
                    "study_code": item.study_code,
                    "quantity": item.cantidad,
                    "unit_price": float(item.precio_unitario),
                    "total_price": float(item.subtotal),
                    "estado_resultado": item.estado_resultado,
                    "openelis_order_id": item.openelis_order_id,
                    "orthanc_study_uid": item.orthanc_study_uid,
                    "created_at": item.created_at
                }
                for item in invoice.items.all()
            ],
            "payments": []
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/search/{term}", response_model=List[InvoiceSearchResult])
async def search_invoices(
    term: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Busca facturas por múltiples criterios:
    - ID local (4-5 dígitos)
    - Código de barras
    - Código QR
    - Nombre de paciente
    - Cédula
    
    Retorna historial completo ordenado por fecha (más reciente primero)
    """
    service = InvoiceService(db)
    
    invoices = service.search_invoices(
        term=term,
        branch_id=current_user.branch_id,
        limit=50
    )
    
    results = []
    for inv in invoices:
        # Verificar si tiene resultados disponibles
        has_results = any(
            item.estado_resultado == 'VALIDADO' 
            for item in inv.items.all()
        )
        
        results.append({
            "id": inv.id,
            "branch_id": inv.branch_id,
            "invoice_id_local": inv.codigo_unico,
            "patient_name": inv.patient.full_name if inv.patient else "Desconocido",
            "patient_id_number": inv.patient.id_number if inv.patient else None,
            "status": inv.estado,
            "total": float(inv.total),
            "balance": float(inv.saldo_pendiente),
            "created_at": inv.created_at,
            "barcode": inv.codigo_barras,
            "has_results": has_results
        })
    
    return results


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene detalles completos de una factura"""
    invoice = db.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.branch_id == current_user.branch_id
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Factura no encontrada"
        )
    
    return {
        "id": invoice.id,
        "branch_id": invoice.branch_id,
        "invoice_id_local": invoice.codigo_unico,
        "patient_id": invoice.paciente_id,
        "patient_name": invoice.patient.full_name if invoice.patient else "Desconocido",
        "status": invoice.estado,
        "subtotal": float(invoice.subtotal),
        "insurance_coverage_percent": float(invoice.seguro_cobertura_percent),
        "insurance_amount": float(invoice.seguro_monto),
        "patient_amount": float(invoice.paciente_monto),
        "total": float(invoice.total),
        "amount_paid": float(invoice.monto_pagado),
        "balance": float(invoice.saldo_pendiente),
        "insurance_name": invoice.seguro_nombre,
        "insurance_policy_number": invoice.seguro_poliza,
        "notes": invoice.observaciones,
        "barcode": invoice.codigo_barras,
        "qr_code": invoice.codigo_qr,
        "created_by": invoice.usuario_crea_id,
        "created_at": invoice.created_at,
        "paid_at": invoice.paid_at,
        "items": [
            {
                "id": item.id,
                "invoice_id": item.invoice_id,
                "study_catalog_id": item.service_id,
                "study_name": item.study_name,
                "study_code": item.study_code,
                "quantity": item.cantidad,
                "unit_price": float(item.precio_unitario),
                "total_price": float(item.subtotal),
                "estado_resultado": item.estado_resultado,
                "openelis_order_id": item.openelis_order_id,
                "orthanc_study_uid": item.orthanc_study_uid,
                "result_pdf_url": item.result_pdf_url,
                "dicom_viewer_url": item.dicom_viewer_url,
                "notas": item.notas,
                "created_at": item.created_at
            }
            for item in invoice.items.all()
        ],
        "payments": [
            {
                "id": p.id,
                "invoice_id": p.invoice_id,
                "amount": float(p.monto),
                "payment_method": p.metodo_pago,
                "payment_date": p.fecha_pago,
                "reference_number": p.numero_referencia,
                "notes": p.notas
            }
            for p in invoice.payments.all()
        ]
    }


@router.post("/{invoice_id}/pay", response_model=PaymentResponse)
async def register_payment(
    invoice_id: int,
    payment_data: InvoicePayment,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Registra un pago a una factura
    
    - **amount**: Monto a pagar
    - **payment_method**: Método de pago (cash, card, paypal, insurance, transfer)
    - **reference_number**: Número de referencia (opcional)
    - **notes**: Notas adicionales (opcional)
    """
    service = InvoiceService(db)
    
    try:
        payment = service.register_payment(
            invoice_id=invoice_id,
            payment_data=payment_data,
            user_id=current_user.id
        )
        
        return {
            "id": payment.id,
            "invoice_id": payment.invoice_id,
            "amount": float(payment.monto),
            "payment_method": payment.metodo_pago,
            "payment_date": payment.fecha_pago,
            "reference_number": payment.numero_referencia,
            "notes": payment.notas
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{invoice_id}/results")
async def get_invoice_results(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene resultados de una factura
    
    ⚠️ **IMPORTANTE**: Solo retorna resultados si la factura está completamente pagada
    """
    service = InvoiceService(db)
    
    try:
        results = service.get_invoice_results(invoice_id=invoice_id)
        
        return {
            "invoice_id": invoice_id,
            "results_available": True,
            "items": [
                {
                    "id": item.id,
                    "study_name": item.study_name,
                    "study_code": item.study_code,
                    "estado_resultado": item.estado_resultado,
                    "result_pdf_url": item.result_pdf_url,
                    "dicom_viewer_url": item.dicom_viewer_url,
                    "orthanc_study_uid": item.orthanc_study_uid,
                    "openelis_order_id": item.openelis_order_id
                }
                for item in results
            ]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": str(e),
                "message": "Para retirar los resultados debe cancelar la totalidad de la factura",
                "friendly_message": "Estimado paciente, sus resultados estarán disponibles una vez complete el pago de su factura. Puede acercarse a recepción o pagar en línea."
            }
        )


@router.get("/patient/{patient_id}/history")
async def get_patient_invoice_history(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene historial completo de facturas de un paciente"""
    from app.models.database import Patient
    
    # Verificar que el paciente pertenezca a la sucursal
    patient = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.branch_id == current_user.branch_id
    ).first()
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado"
        )
    
    invoices = db.query(Invoice).filter(
        Invoice.paciente_id == patient_id
    ).order_by(Invoice.created_at.desc()).all()
    
    return [
        {
            "id": inv.id,
            "invoice_id_local": inv.codigo_unico,
            "status": inv.estado,
            "total": float(inv.total),
            "balance": float(inv.saldo_pendiente),
            "created_at": inv.created_at,
            "items_count": inv.items.count()
        }
        for inv in invoices
    ]
