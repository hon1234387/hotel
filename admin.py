"""
Módulo de Administración del Sistema
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_required, current_user
from models import db, User, Guest, Room, Reservation, Payment, Service, SystemSettings, Module, Permission, RolePermission
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorador para requerir rol de admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Acceso denegado. Se requieren permisos de administrador.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@login_required
@admin_required
def index():
    """Dashboard de administración"""
    total_users = User.query.count()
    total_guests = Guest.query.count()
    total_rooms = Room.query.count()
    total_reservations = Reservation.query.count()
    active_reservations = Reservation.query.filter_by(status='checked_in').count()
    total_revenue = db.session.query(db.func.sum(Payment.amount)).filter_by(status='completed').scalar() or 0
    
    # Últimos registros
    recent_guests = Guest.query.order_by(Guest.created_at.desc()).limit(5).all()
    recent_reservations = Reservation.query.order_by(Reservation.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_guests=total_guests,
                         total_rooms=total_rooms,
                         total_reservations=total_reservations,
                         active_reservations=active_reservations,
                         total_revenue=total_revenue,
                         recent_guests=recent_guests,
                         recent_reservations=recent_reservations)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Gestión de usuarios"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    role_filter = request.args.get('role', '', type=str)
    
    query = User.query
    
    if search:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.full_name.ilike(f'%{search}%')
            )
        )
    
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    users_paginated = query.paginate(page=page, per_page=10)
    
    return render_template('admin/users.html',
                         users=users_paginated.items,
                         pages=users_paginated.pages,
                         current_page=page,
                         search=search,
                         role_filter=role_filter)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Editar usuario"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        user.role = request.form.get('role')
        user.is_active = request.form.get('is_active') == 'on'
        
        db.session.commit()
        flash(f'Usuario {user.username} actualizado exitosamente', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', user=user)


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Eliminar usuario"""
    if user_id == current_user.id:
        flash('No puedes eliminar tu propia cuenta', 'danger')
        return redirect(url_for('admin.users'))
    
    user = User.query.get_or_404(user_id)
    username = user.username
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Usuario {username} eliminado exitosamente', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Cambiar estado del usuario (activo/inactivo)"""
    if user_id == current_user.id:
        flash('No puedes cambiar tu propio estado', 'danger')
        return redirect(url_for('admin.users'))
    
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    status = "activado" if user.is_active else "desactivado"
    flash(f'Usuario {user.username} {status} exitosamente', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Reportes del sistema"""
    # Ocupación de habitaciones
    total_rooms = Room.query.count()
    occupied_rooms = Room.query.filter_by(status='occupied').count()
    maintenance_rooms = Room.query.filter_by(status='maintenance').count()
    cleaning_rooms = Room.query.filter_by(status='cleaning').count()
    available_rooms = Room.query.filter_by(status='available').count()
    
    occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
    
    # Ingresos
    total_payments = db.session.query(db.func.sum(Payment.amount)).scalar() or 0
    completed_payments = db.session.query(db.func.sum(Payment.amount)).filter_by(status='completed').scalar() or 0
    pending_payments = db.session.query(db.func.sum(Payment.amount)).filter_by(status='pending').scalar() or 0
    
    # Reservaciones
    total_reservations = Reservation.query.count()
    confirmed_reservations = Reservation.query.filter_by(status='confirmed').count()
    pending_reservations = Reservation.query.filter_by(status='pending').count()
    cancelled_reservations = Reservation.query.filter_by(status='cancelled').count()
    
    return render_template('admin/reports.html',
                         total_rooms=total_rooms,
                         occupied_rooms=occupied_rooms,
                         maintenance_rooms=maintenance_rooms,
                         cleaning_rooms=cleaning_rooms,
                         available_rooms=available_rooms,
                         occupancy_rate=occupancy_rate,
                         total_payments=total_payments,
                         completed_payments=completed_payments,
                         pending_payments=pending_payments,
                         total_reservations=total_reservations,
                         confirmed_reservations=confirmed_reservations,
                         pending_reservations=pending_reservations,
                         cancelled_reservations=cancelled_reservations)


@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    """Configuración del sistema"""
    # Obtener configuración de la base de datos
    system_settings = SystemSettings.query.first()
    
    # Si no existen, crear con valores por defecto
    if not system_settings:
        system_settings = SystemSettings()
        db.session.add(system_settings)
        db.session.commit()
    
    return render_template('admin/settings.html', settings=system_settings)


@admin_bp.route('/settings/save', methods=['POST'])
@login_required
@admin_required
def save_settings():
    """Guardar configuración"""
    try:
        # Obtener datos del formulario
        hotel_name = request.form.get('hotel_name')
        hotel_address = request.form.get('hotel_address')
        hotel_phone = request.form.get('hotel_phone')
        hotel_email = request.form.get('hotel_email')
        check_in_time = request.form.get('check_in_time')
        check_out_time = request.form.get('check_out_time')
        price_per_night = request.form.get('price_per_night')
        
        # Obtener o crear configuración
        settings = SystemSettings.query.first()
        if not settings:
            settings = SystemSettings()
        
        # Actualizar datos
        settings.hotel_name = hotel_name
        settings.hotel_address = hotel_address
        settings.hotel_phone = hotel_phone
        settings.hotel_email = hotel_email
        settings.check_in_time = check_in_time
        settings.check_out_time = check_out_time
        settings.price_per_night = float(price_per_night) if price_per_night else 0
        
        # Guardar en base de datos
        db.session.add(settings)
        db.session.commit()
        
        flash('Configuración guardada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar configuración: {str(e)}', 'error')
    
    return redirect(url_for('admin.settings'))


@admin_bp.route('/modules', methods=['GET', 'POST'])
@login_required
@admin_required
def modules():
    """Gestionar módulos del sistema"""
    modules = Module.query.all()
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            icon = request.form.get('icon', 'fas fa-cube')
            
            # Verificar si el módulo ya existe
            existing = Module.query.filter_by(name=name).first()
            if existing:
                flash('El módulo ya existe', 'warning')
                return redirect(url_for('admin.modules'))
            
            module = Module(name=name, description=description, icon=icon, is_enabled=True)
            db.session.add(module)
            db.session.commit()
            flash(f'Módulo "{name}" creado exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear módulo: {str(e)}', 'error')
        
        return redirect(url_for('admin.modules'))
    
    return render_template('admin/modules.html', modules=modules)


@admin_bp.route('/modules/<int:module_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_module(module_id):
    """Activar/Desactivar módulo"""
    try:
        module = Module.query.get(module_id)
        if not module:
            return jsonify({'error': 'Módulo no encontrado'}), 404
        
        module.is_enabled = not module.is_enabled
        db.session.commit()
        
        state = 'activado' if module.is_enabled else 'desactivado'
        return jsonify({'success': True, 'message': f'Módulo {state}', 'enabled': module.is_enabled})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/modules/<int:module_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_module(module_id):
    """Eliminar módulo"""
    try:
        module = Module.query.get(module_id)
        if not module:
            flash('Módulo no encontrado', 'error')
            return redirect(url_for('admin.modules'))
        
        # Eliminar permisos asociados
        Permission.query.filter_by(module_id=module_id).delete()
        db.session.delete(module)
        db.session.commit()
        flash(f'Módulo "{module.name}" eliminado', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar módulo: {str(e)}', 'error')
    
    return redirect(url_for('admin.modules'))


@admin_bp.route('/permissions', methods=['GET', 'POST'])
@login_required
@admin_required
def permissions():
    """Gestionar permisos del sistema"""
    permissions = Permission.query.all()
    modules = Module.query.filter_by(is_enabled=True).all()
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description')
            module_id = request.form.get('module_id')
            
            # Verificar si el permiso ya existe
            existing = Permission.query.filter_by(name=name).first()
            if existing:
                flash('El permiso ya existe', 'warning')
                return redirect(url_for('admin.permissions'))
            
            permission = Permission(
                name=name,
                description=description,
                module_id=int(module_id) if module_id else None
            )
            db.session.add(permission)
            db.session.commit()
            flash(f'Permiso "{name}" creado exitosamente', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear permiso: {str(e)}', 'error')
        
        return redirect(url_for('admin.permissions'))
    
    return render_template('admin/permissions.html', permissions=permissions, modules=modules)


@admin_bp.route('/permissions/<int:permission_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_permission(permission_id):
    """Eliminar permiso"""
    try:
        permission = Permission.query.get(permission_id)
        if not permission:
            flash('Permiso no encontrado', 'error')
            return redirect(url_for('admin.permissions'))
        
        # Eliminar asignaciones de roles
        RolePermission.query.filter_by(permission_id=permission_id).delete()
        db.session.delete(permission)
        db.session.commit()
        flash(f'Permiso "{permission.name}" eliminado', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar permiso: {str(e)}', 'error')
    
    return redirect(url_for('admin.permissions'))


@admin_bp.route('/roles', methods=['GET', 'POST'])
@login_required
@admin_required
def roles():
    """Gestionar roles y permisos"""
    modules = Module.query.filter_by(is_enabled=True).all()
    return render_template('admin/roles.html', modules=modules)


@admin_bp.route('/roles/<role>/permissions', methods=['GET', 'POST'])
@login_required
@admin_required
def role_permissions(role):
    """Obtener o actualizar permisos de un rol"""
    valid_roles = ['admin', 'manager', 'staff', 'guest']
    if role not in valid_roles:
        return jsonify({'error': 'Rol inválido'}), 400
    
    if request.method == 'GET':
        # Obtener permisos asignados al rol
        role_perms = RolePermission.query.filter_by(role=role).all()
        assigned_permission_ids = [rp.permission_id for rp in role_perms]
        
        # Construir respuesta con todos los permisos organizados por módulo
        modules = Module.query.filter_by(is_enabled=True).all()
        modules_data = []
        
        for module in modules:
            perms = Permission.query.filter_by(module_id=module.id).all()
            modules_data.append({
                'id': module.id,
                'name': module.name,
                'icon': module.icon,
                'is_enabled': module.is_enabled,
                'permissions': [
                    {
                        'id': p.id,
                        'name': p.name,
                        'description': p.description
                    } for p in perms
                ]
            })
        
        return jsonify({
            'modules': modules_data,
            'assigned_permissions': assigned_permission_ids
        })
    
    elif request.method == 'POST':
        # Actualizar permisos del rol
        try:
            data = request.get_json()
            permissions = data.get('permissions', [])
            
            # Eliminar permisos anteriores
            RolePermission.query.filter_by(role=role).delete()
            
            # Agregar nuevos permisos
            for perm_id in permissions:
                permission = Permission.query.get(perm_id)
                if permission:
                    rp = RolePermission(role=role, permission_id=perm_id)
                    db.session.add(rp)
            
            db.session.commit()
            return jsonify({'success': True, 'message': f'Permisos del rol "{role}" actualizados'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

