#!/usr/bin/env python3
"""
Script de Inicialización - Crea usuario SUPER_ROOT y primera sucursal
Ejecutar después de instalar la base de datos
"""
import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.core.config import get_settings
from app.models.database import Base, Branch, Role, User, RoleType, StudyCatalog
from app.services.auth import get_password_hash

settings = get_settings()


def init_database():
    """Inicializa la base de datos con tablas y datos semilla"""
    
    print("=" * 60)
    print("MediTech System - Inicialización de Base de Datos")
    print("=" * 60)
    
    # Crear engine y tablas
    print(f"\n[1/5] Conectando a la base de datos: {settings.DB_NAME}@{settings.DB_HOST}")
    engine = create_engine(settings.DATABASE_URL)
    
    print("[2/5] Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas creadas exitosamente")
    
    # Crear sesión
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Verificar si ya existe configuración
        existing_root = db.query(User).join(Role).filter(
            Role.role_type == RoleType.SUPER_ROOT
        ).first()
        
        if existing_root:
            print("\n⚠️  ADVERTENCIA: El sistema ya está inicializado")
            print(f"   Usuario ROOT existente: {existing_root.username}")
            response = input("\n¿Desea continuar y crear otro usuario ROOT? (y/N): ")
            if response.lower() != 'y':
                print("Inicialización cancelada")
                return
        
        # Crear sucursal principal si no existe
        print("\n[3/5] Configurando sucursal principal...")
        
        branch_code = input("Código de sucursal principal (ej: 001): ").strip() or "001"
        branch_name = input("Nombre de sucursal principal: ").strip() or "Sucursal Principal"
        
        branch = Branch(
            code=branch_code,
            name=branch_name,
            address="Dirección de la sucursal",
            phone="Teléfono",
            email="contacto@meditech.com",
            active=True
        )
        
        db.add(branch)
        db.commit()
        db.refresh(branch)
        print(f"✓ Sucursal creada: {branch.name} (Código: {branch.code})")
        
        # Crear rol SUPER_ROOT
        print("\n[4/5] Creando usuario SUPER_ROOT...")
        
        root_role = Role(
            nombre="Super Administrador",
            descripcion="Rol con acceso total al sistema",
            role_type=RoleType.SUPER_ROOT,
            permissions={
                "*": True,  # Todos los permisos
                "admin.all": True,
                "users.create": True,
                "users.edit": True,
                "users.delete": True,
                "branches.create": True,
                "branches.edit": True,
                "roles.create": True,
                "invoices.view_all": True,
                "reports.all": True,
            }
        )
        
        db.add(root_role)
        db.commit()
        db.refresh(root_role)
        
        # Datos del usuario ROOT
        print("\nIngrese los datos del usuario SUPER_ROOT:")
        username = input("Username (ej: admin): ").strip() or "admin"
        email = input("Email: ").strip() or "admin@meditech.com"
        full_name = input("Nombre completo: ").strip() or "Administrador Principal"
        
        while True:
            password = input("Contraseña (mínimo 8 caracteres): ").strip()
            if len(password) >= 8:
                break
            print("Error: La contraseña debe tener al menos 8 caracteres")
        
        root_user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            role_id=root_role.id,
            branch_id=branch.id,
            active=True
        )
        
        db.add(root_user)
        db.commit()
        db.refresh(root_user)
        
        print(f"✓ Usuario ROOT creado: {root_user.username}")
        
        # Crear roles por defecto
        print("\n[5/5] Creando roles por defecto...")
        
        default_roles = [
            {
                "nombre": "Administrador",
                "role_type": RoleType.ADMIN,
                "permissions": {
                    "users.create": True,
                    "users.edit": True,
                    "patients.all": True,
                    "invoices.all": True,
                    "reports.view": True,
                    "config.edit": True,
                }
            },
            {
                "nombre": "Recepción",
                "role_type": RoleType.RECEPCION,
                "permissions": {
                    "patients.create": True,
                    "patients.edit": True,
                    "patients.view": True,
                    "invoices.create": True,
                    "invoices.view": True,
                    "payments.create": True,
                }
            },
            {
                "nombre": "Doctor",
                "role_type": RoleType.DOCTOR,
                "permissions": {
                    "patients.view": True,
                    "results.view": True,
                    "results.validate": True,
                    "reports.view": True,
                }
            },
            {
                "nombre": "Laboratorio",
                "role_type": RoleType.LAB,
                "permissions": {
                    "samples.view": True,
                    "results.create": True,
                    "results.edit": True,
                }
            },
            {
                "nombre": "Radiólogo",
                "role_type": RoleType.RADIOLOGO,
                "permissions": {
                    "images.view": True,
                    "results.create": True,
                    "results.validate": True,
                }
            },
        ]
        
        for role_data in default_roles:
            role = Role(
                nombre=role_data["nombre"],
                role_type=role_data["role_type"],
                permissions=role_data["permissions"],
                branch_id=branch.id
            )
            db.add(role)
        
        db.commit()
        print("✓ Roles por defecto creados")
        
        # Crear estudios de ejemplo
        print("\n[EXTRA] Creando catálogo de estudios de ejemplo...")
        
        sample_studies = [
            {"name": "Hemograma Completo", "code": "LAB001", "price": 15.00, "category": "LABORATORIO"},
            {"name": "Examen General de Orina", "code": "LAB002", "price": 10.00, "category": "LABORATORIO"},
            {"name": "Coprológico", "code": "LAB003", "price": 12.00, "category": "LABORATORIO"},
            {"name": "Glucosa en Sangre", "code": "LAB004", "price": 8.00, "category": "LABORATORIO"},
            {"name": "Colesterol Total", "code": "LAB005", "price": 10.00, "category": "LABORATORIO"},
            {"name": "Rayos X Tórax", "code": "IMG001", "price": 25.00, "category": "IMAGENES"},
            {"name": "Ultrasonido Abdominal", "code": "IMG002", "price": 45.00, "category": "IMAGENES"},
            {"name": "Electrocardiograma", "code": "ESP001", "price": 20.00, "category": "ESPECIALIDADES"},
        ]
        
        for study_data in sample_studies:
            study = StudyCatalog(
                branch_id=branch.id,
                name=study_data["name"],
                code=study_data["code"],
                price=study_data["price"],
                category=study_data["category"],
                requires_sample=study_data["category"] == "LABORATORIO",
                active=True
            )
            db.add(study)
        
        db.commit()
        print("✓ Estudios de ejemplo creados")
        
        print("\n" + "=" * 60)
        print("¡INICIALIZACIÓN COMPLETADA EXITOSAMENTE!")
        print("=" * 60)
        print(f"\nDatos de acceso:")
        print(f"  Username: {username}")
        print(f"  URL de acceso: http://localhost")
        print(f"  API Docs: http://localhost:8000/docs")
        print(f"\nPróximos pasos:")
        print(f"  1. Inicia sesión con el usuario ROOT")
        print(f"  2. Configura los logos y personalización")
        print(f"  3. Crea usuarios para cada sucursal")
        print(f"  4. Configura los analizadores de laboratorio")
        print(f"  5. Comienza a operar")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR durante la inicialización: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
