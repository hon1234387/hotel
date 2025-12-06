#!/usr/bin/env python
"""Script para inicializar la base de datos con datos de demostración"""

from app import create_app, db
from models import User, Guest, Room, Service
from datetime import datetime, timedelta

def init_database():
    """Inicializa la base de datos con datos de demostración"""
    app = create_app()
    
    with app.app_context():
        # Limpiar datos existentes
        db.drop_all()
        db.create_all()
        
        # Crear usuario administrador
        admin = User(
            username='admin',
            email='admin@hotel.com',
            full_name='Administrador del Hotel',
            role='admin',
            phone='+1-555-0001',
            is_active=True
        )
        admin.set_password('admin123')
        
        # Crear otros usuarios de demostración
        receptionist = User(
            username='receptionist',
            email='receptionist@hotel.com',
            full_name='María García',
            role='receptionist',
            phone='+1-555-0002',
            is_active=True
        )
        receptionist.set_password('password123')
        
        housekeeper = User(
            username='housekeeper',
            email='housekeeper@hotel.com',
            full_name='Juan López',
            role='housekeeper',
            phone='+1-555-0003',
            is_active=True
        )
        housekeeper.set_password('password123')
        
        db.session.add_all([admin, receptionist, housekeeper])
        db.session.commit()
        print("✓ Usuarios creados")
        
        # Crear huéspedes de demostración
        guests = [
            Guest(
                first_name='Carlos',
                last_name='Rodriguez',
                email='carlos@email.com',
                phone='+1-555-0100',
                document_type='passport',
                document_number='A12345678',
                nationality='México',
                address='Calle Principal 123',
                city='Mexico City',
                country='México'
            ),
            Guest(
                first_name='Ana',
                last_name='Martinez',
                email='ana@email.com',
                phone='+1-555-0101',
                document_type='id',
                document_number='1234567890',
                nationality='España',
                address='Calle Segunda 456',
                city='Madrid',
                country='España'
            ),
            Guest(
                first_name='Pedro',
                last_name='Gonzalez',
                email='pedro@email.com',
                phone='+1-555-0102',
                document_type='license',
                document_number='DL12345',
                nationality='Argentina',
                city='Buenos Aires',
                country='Argentina'
            ),
        ]
        db.session.add_all(guests)
        db.session.commit()
        print("✓ Huéspedes creados")
        
        # Crear habitaciones de demostración
        rooms = [
            Room(room_number='101', room_type='single', floor=1, capacity=1, 
                 price_per_night=50, description='Habitación individual con vista a la calle',
                 amenities='WiFi, TV, AC, Baño privado', status='available'),
            Room(room_number='102', room_type='double', floor=1, capacity=2,
                 price_per_night=80, description='Habitación doble cómoda',
                 amenities='WiFi, TV, AC, Baño privado, Minibar', status='available'),
            Room(room_number='103', room_type='suite', floor=1, capacity=3,
                 price_per_night=150, description='Suite de lujo con sala de estar',
                 amenities='WiFi, TV, AC, Baño privado, Minibar, Sala', status='available'),
            Room(room_number='201', room_type='single', floor=2, capacity=1,
                 price_per_night=55, description='Habitación individual piso 2',
                 amenities='WiFi, TV, AC, Baño privado', status='available'),
            Room(room_number='202', room_type='double', floor=2, capacity=2,
                 price_per_night=85, description='Habitación doble con vista al parque',
                 amenities='WiFi, TV, AC, Baño privado, Minibar, Balcón', status='occupied'),
            Room(room_number='203', room_type='deluxe', floor=2, capacity=4,
                 price_per_night=200, description='Suite deluxe con todas las comodidades',
                 amenities='WiFi, TV, AC, Baño privado, Minibar, Jacuzzi, Sala', status='available'),
            Room(room_number='301', room_type='single', floor=3, capacity=1,
                 price_per_night=50, description='Habitación individual piso 3',
                 amenities='WiFi, TV, AC, Baño privado', status='available'),
            Room(room_number='302', room_type='double', floor=3, capacity=2,
                 price_per_night=80, description='Habitación doble piso 3',
                 amenities='WiFi, TV, AC, Baño privado, Minibar', status='maintenance'),
        ]
        db.session.add_all(rooms)
        db.session.commit()
        print("✓ Habitaciones creadas")
        
        # Crear servicios de demostración
        services = [
            Service(name='Desayuno', description='Desayuno buffet completo', 
                   price=15, category='room_service', is_active=True),
            Service(name='Spa Relajante', description='Masaje y tratamientos spa',
                   price=80, category='spa', is_active=True),
            Service(name='Lavandería Express', description='Servicio de lavandería rápido',
                   price=20, category='laundry', is_active=True),
            Service(name='Estacionamiento', description='Estacionamiento seguro por noche',
                   price=10, category='parking', is_active=True),
            Service(name='Transporte al Aeropuerto', description='Servicio de transporte',
                   price=50, category='transportation', is_active=True),
            Service(name='Cena Romántica', description='Cena romántica en la habitación',
                   price=120, category='room_service', is_active=True),
        ]
        db.session.add_all(services)
        db.session.commit()
        print("✓ Servicios creados")
        
        print("\n✅ Base de datos inicializada correctamente")
        print("\nCredenciales de demostración:")
        print("  Usuario: admin")
        print("  Contraseña: admin123")
        print("\nOtros usuarios:")
        print("  Usuario: receptionist | Contraseña: password123")
        print("  Usuario: housekeeper | Contraseña: password123")

if __name__ == '__main__':
    init_database()
