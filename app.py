from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, current_user
from config import config
from models import db, User
from auth import auth_bp, staff_required
from admin import admin_bp
from routes import (reservations_bp, guests_bp, rooms_bp, services_bp, 
                    payments_bp, maintenance_bp, housekeeping_bp, whatsapp_bp)
import os

def create_app(config_name='development'):
    """Factory function para crear la aplicación Flask"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicie sesión primero'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    # Context processor para pasar configuración a todos los templates
    @app.context_processor
    def inject_config():
        try:
            from models import SystemSettings, Module
            settings = SystemSettings.query.first()
            if not settings:
                settings = SystemSettings()
            # Pasar todos los módulos con acceso por nombre
            all_modules = Module.query.all()
            modules_dict = {module.name: module for module in all_modules}
            return {'hotel_settings': settings, 'modules_dict': modules_dict}
        except Exception:
            # En caso de error (BD no inicializada), retornar valores por defecto
            return {'hotel_settings': None, 'modules_dict': {}}
    
    # Crear contexto de la aplicación
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Error creando tablas: {e}")
    
    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reservations_bp)
    app.register_blueprint(guests_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(housekeeping_bp)
    app.register_blueprint(whatsapp_bp)
    
    # Rutas principales
    @app.route('/')
    def index():
        """Página de inicio"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('whatsapp.booking_link'))
    
    @app.route('/dashboard')
    @staff_required
    def dashboard():
        """Dashboard principal"""
        from models import Reservation, Room, HousekeepingTask, MaintenanceLog
        from datetime import date
        from flask import make_response
        
        # Estadísticas
        total_rooms = Room.query.count()
        occupied_rooms = Room.query.filter_by(status='occupied').count()
        available_rooms = Room.query.filter_by(status='available').count()
        maintenance_rooms = Room.query.filter_by(status='maintenance').count()
        cleaning_rooms = Room.query.filter_by(status='cleaning').count()
        
        # Reservaciones de hoy
        today_checkins = Reservation.query.filter(
            Reservation.check_in_date == date.today(),
            Reservation.status != 'cancelled'
        ).count()
        
        today_checkouts = Reservation.query.filter(
            Reservation.check_out_date == date.today(),
            Reservation.status != 'cancelled'
        ).count()
        
        # Tareas pendientes
        pending_tasks = HousekeepingTask.query.filter(
            HousekeepingTask.status.in_(['pending', 'in_progress']),
            HousekeepingTask.due_date >= date.today()
        ).count()
        
        # Mantenimiento pendiente
        pending_maintenance = MaintenanceLog.query.filter(
            MaintenanceLog.status.in_(['pending', 'in_progress'])
        ).count()
        
        # Próximas reservaciones
        upcoming_reservations = Reservation.query.filter(
            Reservation.check_in_date >= date.today(),
            Reservation.status != 'cancelled'
        ).order_by(Reservation.check_in_date).limit(5).all()
        
        response = make_response(render_template('dashboard.html',
                             total_rooms=total_rooms,
                             occupied_rooms=occupied_rooms,
                             available_rooms=available_rooms,
                             maintenance_rooms=maintenance_rooms,
                             cleaning_rooms=cleaning_rooms,
                             today_checkins=today_checkins,
                             today_checkouts=today_checkouts,
                             pending_tasks=pending_tasks,
                             pending_maintenance=pending_maintenance,
                             upcoming_reservations=upcoming_reservations))
        
        # No cachear el dashboard
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Manejador de error 404"""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Manejador de error 403"""
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        """Manejador de error 500"""
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Context processor para variables globales
    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)
    
    return app

# Crear instancia de la app para Vercel
flask_env = os.getenv('FLASK_ENV', 'development')
config_name = 'production' if flask_env == 'production' else 'development'
app = create_app(config_name)

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5000)
