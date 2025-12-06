from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from forms import LoginForm, RegisterForm
from functools import wraps

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Acceso denegado. Se requieren permisos de administrador.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debe iniciar sesión primero.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Ruta para iniciar sesión"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Usuario o contraseña incorrectos', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('La cuenta ha sido desactivada', 'warning')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=True)
        session.permanent = True
        
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard'))
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Ruta para registrar nuevos empleados (solo admin)"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Solo administradores pueden crear nuevos empleados', 'danger')
        return redirect(url_for('auth.login'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=form.role.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Empleado {form.username.data} creado exitosamente', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Ruta para cerrar sesión"""
    logout_user()
    flash('Ha cerrado sesión exitosamente', 'info')
    return redirect(url_for('index'))
