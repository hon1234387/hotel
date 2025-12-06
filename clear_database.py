#!/usr/bin/env python3
"""Script para limpiar la base de datos, manteniendo solo el usuario admin"""

from app import create_app, db
from models import Guest, Room, Reservation, Service, Payment, MaintenanceLog, HousekeepingTask, AuditLog, User

def clear_database():
    """Elimina todos los datos excepto el usuario admin"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🗑️  Iniciando limpieza de base de datos...")
            
            # Obtener el ID del admin antes de eliminar
            admin_user = User.query.filter_by(role='admin').first()
            admin_id = admin_user.id if admin_user else None
            
            # Eliminar en orden (respetar relaciones)
            print("Eliminando auditoría...")
            AuditLog.query.delete()
            
            print("Eliminando tareas de limpieza...")
            HousekeepingTask.query.delete()
            
            print("Eliminando registros de mantenimiento...")
            MaintenanceLog.query.delete()
            
            print("Eliminando pagos...")
            Payment.query.delete()
            
            print("Eliminando reservaciones...")
            Reservation.query.delete()
            
            print("Eliminando huéspedes...")
            Guest.query.delete()
            
            print("Eliminando servicios...")
            Service.query.delete()
            
            print("Eliminando habitaciones...")
            Room.query.delete()
            
            print("Eliminando usuarios (excepto admin)...")
            User.query.filter(User.id != admin_id).delete()
            
            db.session.commit()
            
            print("\n✅ Base de datos limpiada exitosamente!")
            print(f"✓ Usuario admin preservado (ID: {admin_id})")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error durante la limpieza: {str(e)}")
            raise

if __name__ == '__main__':
    clear_database()
