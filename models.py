from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Modelo para empleados del hotel"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='staff')  # admin, receptionist, housekeeper, manager
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    reservations = db.relationship('Reservation', backref='created_by_user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Guest(db.Model):
    """Modelo para huéspedes"""
    __tablename__ = 'guests'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    document_type = db.Column(db.String(20), nullable=False)  # passport, id, license
    document_number = db.Column(db.String(50), unique=True, nullable=False)
    nationality = db.Column(db.String(80))
    address = db.Column(db.String(200))
    city = db.Column(db.String(80))
    country = db.Column(db.String(80))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reservations = db.relationship('Reservation', backref='guest', lazy=True)
    
    def __repr__(self):
        return f'<Guest {self.first_name} {self.last_name}>'
    
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'


class Room(db.Model):
    """Modelo para habitaciones"""
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)  # single, double, suite, deluxe
    floor = db.Column(db.Integer, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    amenities = db.Column(db.String(500))  # comma separated
    status = db.Column(db.String(20), default='available')  # available, occupied, maintenance, cleaning
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reservations = db.relationship('Reservation', backref='room', lazy=True)
    maintenance_logs = db.relationship('MaintenanceLog', backref='room', lazy=True)
    
    def __repr__(self):
        return f'<Room {self.room_number}>'


class Reservation(db.Model):
    """Modelo para reservaciones"""
    __tablename__ = 'reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guests.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    number_of_guests = db.Column(db.Integer, nullable=False)
    special_requests = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, checked_in, checked_out, cancelled
    total_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    services = db.relationship('Service', secondary='reservation_services', backref='reservations')
    
    def __repr__(self):
        return f'<Reservation {self.id}>'
    
    @property
    def nights(self):
        return (self.check_out_date - self.check_in_date).days
    
    @property
    def room_cost(self):
        return self.room.price_per_night * self.nights


class Service(db.Model):
    """Modelo para servicios adicionales"""
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # room_service, spa, laundry, parking, etc
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Service {self.name}>'


# Tabla de asociación para reservaciones y servicios
reservation_services = db.Table('reservation_services',
    db.Column('reservation_id', db.Integer, db.ForeignKey('reservations.id'), primary_key=True),
    db.Column('service_id', db.Integer, db.ForeignKey('services.id'), primary_key=True)
)


class Payment(db.Model):
    """Modelo para pagos"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # cash, credit_card, debit_card, check
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, completed, refunded
    notes = db.Column(db.Text)
    
    reservation = db.relationship('Reservation', backref='payments')
    
    def __repr__(self):
        return f'<Payment {self.id}>'


class MaintenanceLog(db.Model):
    """Modelo para registros de mantenimiento"""
    __tablename__ = 'maintenance_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    issue_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), nullable=False)  # low, medium, high, critical
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    assigned_to = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<MaintenanceLog {self.id}>'


class HousekeepingTask(db.Model):
    """Modelo para tareas de limpieza"""
    __tablename__ = 'housekeeping_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    task_type = db.Column(db.String(50), nullable=False)  # cleaning, inspection, turnover
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, hold
    assigned_to = db.Column(db.String(100))
    due_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    room = db.relationship('Room', backref='housekeeping_tasks')
    
    def __repr__(self):
        return f'<HousekeepingTask {self.id}>'


class AuditLog(db.Model):
    """Modelo para registro de auditoría"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(200), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)
    new_values = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.id}>'


class SystemSettings(db.Model):
    """Modelo para configuración del sistema"""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    hotel_name = db.Column(db.String(120), nullable=False, default='Hotel Management System')
    hotel_address = db.Column(db.Text, nullable=False, default='Calle Principal 123, Ciudad')
    hotel_phone = db.Column(db.String(20), nullable=False, default='+1 (555) 123-4567')
    hotel_email = db.Column(db.String(120), nullable=False, default='info@hotel.com')
    check_in_time = db.Column(db.String(5), nullable=False, default='14:00')
    check_out_time = db.Column(db.String(5), nullable=False, default='11:00')
    price_per_night = db.Column(db.Float, nullable=False, default=100.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemSettings {self.hotel_name}>'


class Module(db.Model):
    """Modelo para módulos del sistema"""
    __tablename__ = 'modules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    icon = db.Column(db.String(50))
    is_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Module {self.name}>'


class Permission(db.Model):
    """Modelo para permisos del sistema"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    module = db.relationship('Module', backref='permissions')
    
    def __repr__(self):
        return f'<Permission {self.name}>'


class RolePermission(db.Model):
    """Modelo para asignar permisos a roles"""
    __tablename__ = 'role_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), nullable=False)  # admin, manager, receptionist, housekeeper, etc
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    permission = db.relationship('Permission', backref='role_permissions')
    
    def __repr__(self):
        return f'<RolePermission {self.role}-{self.permission_id}>'
