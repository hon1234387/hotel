from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Guest, Room, Reservation, Service, Payment, MaintenanceLog, HousekeepingTask, AuditLog
from forms import AddGuestForm, AddRoomForm, MakeReservationForm, AddServiceForm, ProcessPaymentForm, CreateMaintenanceForm, CreateHousekeepingTaskForm, ExtendReservationForm, QuickCheckInForm, WhatsAppReservationForm
from datetime import datetime, date
from sqlalchemy import and_, or_
from auth import staff_required, admin_required
import json

reservations_bp = Blueprint('reservations', __name__, url_prefix='/reservations')
guests_bp = Blueprint('guests', __name__, url_prefix='/guests')
rooms_bp = Blueprint('rooms', __name__, url_prefix='/rooms')
services_bp = Blueprint('services', __name__, url_prefix='/services')
payments_bp = Blueprint('payments', __name__, url_prefix='/payments')
maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')
housekeeping_bp = Blueprint('housekeeping', __name__, url_prefix='/housekeeping')
whatsapp_bp = Blueprint('whatsapp', __name__, url_prefix='/whatsapp')

def log_action(action, entity_type, entity_id, old_values=None, new_values=None):
    """Función para registrar acciones en auditoría"""
    audit = AuditLog(
        user_id=current_user.id if current_user.is_authenticated else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=json.dumps(old_values) if old_values else None,
        new_values=json.dumps(new_values) if new_values else None,
        ip_address=request.remote_addr
    )
    db.session.add(audit)
    db.session.commit()

# ==================== GUESTS ====================
@guests_bp.route('/')
@staff_required
def list_guests():
    """Lista todos los huéspedes"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Guest.query
    if search:
        query = query.filter(or_(
            Guest.first_name.ilike(f'%{search}%'),
            Guest.last_name.ilike(f'%{search}%'),
            Guest.email.ilike(f'%{search}%'),
            Guest.document_number.ilike(f'%{search}%')
        ))
    
    guests = query.paginate(page=page, per_page=10)
    return render_template('guests/list_guests.html', guests=guests, search=search)


@guests_bp.route('/add', methods=['GET', 'POST'])
@staff_required
def add_guest():
    """Agregar nuevo huésped"""
    form = AddGuestForm()
    if form.validate_on_submit():
        guest = Guest(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            document_type=form.document_type.data,
            document_number=form.document_number.data,
            nationality=form.nationality.data,
            address=form.address.data,
            city=form.city.data,
            country=form.country.data
        )
        
        db.session.add(guest)
        db.session.commit()
        
        log_action('CREATE', 'Guest', guest.id, new_values={'name': guest.full_name})
        flash(f'Huésped {guest.full_name} creado exitosamente', 'success')
        return redirect(url_for('guests.list_guests'))
    
    return render_template('guests/add_guest.html', form=form)


@guests_bp.route('/<int:guest_id>')
@staff_required
def view_guest(guest_id):
    """Ver detalles del huésped"""
    guest = Guest.query.get_or_404(guest_id)
    return render_template('guests/view_guest.html', guest=guest)


@guests_bp.route('/<int:guest_id>/edit', methods=['GET', 'POST'])
@staff_required
def edit_guest(guest_id):
    """Editar información del huésped"""
    guest = Guest.query.get_or_404(guest_id)
    form = AddGuestForm()
    
    if form.validate_on_submit():
        old_values = {
            'first_name': guest.first_name,
            'last_name': guest.last_name,
            'email': guest.email
        }
        
        guest.first_name = form.first_name.data
        guest.last_name = form.last_name.data
        guest.email = form.email.data
        guest.phone = form.phone.data
        guest.document_type = form.document_type.data
        guest.document_number = form.document_number.data
        guest.nationality = form.nationality.data
        guest.address = form.address.data
        guest.city = form.city.data
        guest.country = form.country.data
        
        db.session.commit()
        
        new_values = {
            'first_name': guest.first_name,
            'last_name': guest.last_name,
            'email': guest.email
        }
        log_action('UPDATE', 'Guest', guest_id, old_values, new_values)
        
        flash('Información del huésped actualizada', 'success')
        return redirect(url_for('guests.view_guest', guest_id=guest_id))
    
    elif request.method == 'GET':
        form.first_name.data = guest.first_name
        form.last_name.data = guest.last_name
        form.email.data = guest.email
        form.phone.data = guest.phone
        form.document_type.data = guest.document_type
        form.document_number.data = guest.document_number
        form.nationality.data = guest.nationality
        form.address.data = guest.address
        form.city.data = guest.city
        form.country.data = guest.country
    
    return render_template('guests/edit_guest.html', form=form, guest=guest)


@guests_bp.route('/<int:guest_id>/delete', methods=['POST'])
@admin_required
def delete_guest(guest_id):
    """Eliminar un huésped (solo admin)"""
    guest = Guest.query.get_or_404(guest_id)
    guest_name = guest.full_name
    
    # Verificar si el huésped tiene reservaciones
    reservations = Reservation.query.filter_by(guest_id=guest_id).all()
    if reservations:
        flash(f'No se puede eliminar a {guest_name}. Tiene {len(reservations)} reservación(es) asociada(s).', 'warning')
        return redirect(url_for('guests.view_guest', guest_id=guest_id))
    
    db.session.delete(guest)
    db.session.commit()
    
    log_action('DELETE', 'Guest', guest_id, old_values={'name': guest_name})
    flash(f'Huésped {guest_name} eliminado', 'success')
    return redirect(url_for('guests.list_guests'))


# ==================== ROOMS ====================
@rooms_bp.route('/')
@staff_required
def list_rooms():
    """Lista todas las habitaciones"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    room_type = request.args.get('type', '')
    
    query = Room.query
    if status:
        query = query.filter_by(status=status)
    if room_type:
        query = query.filter_by(room_type=room_type)
    
    rooms = query.paginate(page=page, per_page=12)
    return render_template('rooms/list_rooms.html', rooms=rooms, current_status=status, current_type=room_type)


@rooms_bp.route('/add', methods=['GET', 'POST'])
@staff_required
def add_room():
    """Agregar nueva habitación"""
    form = AddRoomForm()
    if form.validate_on_submit():
        room = Room(
            room_number=form.room_number.data,
            room_type=form.room_type.data,
            floor=form.floor.data,
            capacity=form.capacity.data,
            price_per_night=form.price_per_night.data,
            description=form.description.data,
            amenities=form.amenities.data,
            status='available'
        )
        
        db.session.add(room)
        db.session.commit()
        
        log_action('CREATE', 'Room', room.id, new_values={'room_number': room.room_number})
        flash(f'Habitación {room.room_number} creada exitosamente', 'success')
        return redirect(url_for('rooms.list_rooms'))
    
    return render_template('rooms/add_room.html', form=form)


@rooms_bp.route('/<int:room_id>')
@staff_required
def view_room(room_id):
    """Ver detalles de la habitación"""
    room = Room.query.get_or_404(room_id)
    
    # Obtener reservaciones próximas
    upcoming_reservations = Reservation.query.filter(
        Reservation.room_id == room_id,
        Reservation.check_in_date >= date.today(),
        Reservation.status != 'cancelled'
    ).order_by(Reservation.check_in_date).limit(5).all()
    
    return render_template('rooms/view_room.html', room=room, reservations=upcoming_reservations)


@rooms_bp.route('/<int:room_id>/edit', methods=['GET', 'POST'])
@staff_required
def edit_room(room_id):
    """Editar información de la habitación"""
    room = Room.query.get_or_404(room_id)
    form = AddRoomForm()
    
    if form.validate_on_submit():
        old_values = {
            'room_number': room.room_number,
            'price_per_night': room.price_per_night,
            'status': room.status
        }
        
        room.room_type = form.room_type.data
        room.floor = form.floor.data
        room.capacity = form.capacity.data
        room.price_per_night = form.price_per_night.data
        room.description = form.description.data
        room.amenities = form.amenities.data
        
        db.session.commit()
        
        new_values = {
            'room_number': room.room_number,
            'price_per_night': room.price_per_night,
            'status': room.status
        }
        log_action('UPDATE', 'Room', room_id, old_values, new_values)
        
        flash('Información de la habitación actualizada', 'success')
        return redirect(url_for('rooms.view_room', room_id=room_id))
    
    elif request.method == 'GET':
        form.room_number.data = room.room_number
        form.room_type.data = room.room_type
        form.floor.data = room.floor
        form.capacity.data = room.capacity
        form.price_per_night.data = room.price_per_night
        form.description.data = room.description
        form.amenities.data = room.amenities
    
    return render_template('rooms/edit_room.html', form=form, room=room)


@rooms_bp.route('/<int:room_id>/change-status', methods=['POST'])
@staff_required
def change_room_status(room_id):
    """Cambiar estado de la habitación"""
    room = Room.query.get_or_404(room_id)
    new_status = request.json.get('status')
    
    if new_status not in ['available', 'occupied', 'maintenance', 'cleaning']:
        return jsonify({'error': 'Estado inválido'}), 400
    
    old_status = room.status
    room.status = new_status
    db.session.commit()
    
    log_action('UPDATE', 'Room', room_id, {'status': old_status}, {'status': new_status})
    return jsonify({'success': True, 'message': 'Estado actualizado'})


@rooms_bp.route('/<int:room_id>/delete', methods=['POST'])
@admin_required
def delete_room(room_id):
    """Eliminar una habitación (solo admin)"""
    room = Room.query.get_or_404(room_id)
    room_number = room.room_number
    
    # Verificar si la habitación tiene reservaciones activas
    active_reservations = Reservation.query.filter(
        Reservation.room_id == room_id,
        Reservation.status.in_(['confirmed', 'checked_in'])
    ).all()
    
    if active_reservations:
        flash(f'No se puede eliminar la habitación {room_number}. Tiene reservaciones activas.', 'warning')
        return redirect(url_for('rooms.view_room', room_id=room_id))
    
    db.session.delete(room)
    db.session.commit()
    
    log_action('DELETE', 'Room', room_id, old_values={'room_number': room_number})
    flash(f'Habitación {room_number} eliminada', 'success')
    return redirect(url_for('rooms.list_rooms'))


# ==================== RESERVATIONS ====================
@reservations_bp.route('/')
@staff_required
def list_reservations():
    """Lista todas las reservaciones"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Reservation.query
    if status:
        query = query.filter_by(status=status)
    
    reservations = query.order_by(Reservation.check_in_date.desc()).paginate(page=page, per_page=10)
    return render_template('reservations/list_reservations.html', reservations=reservations, current_status=status)


@reservations_bp.route('/create', methods=['GET', 'POST'])
@staff_required
def create_reservation():
    """Crear nueva reservación"""
    # Cargar datos para el formulario PRIMERO
    guests = Guest.query.all()
    rooms = Room.query.filter_by(status='available').all()
    
    form = MakeReservationForm()
    # Asignar opciones INMEDIATAMENTE después de crear el formulario
    form.guest_id.choices = [(g.id, g.full_name) for g in guests]
    form.room_id.choices = [(r.id, f"{r.room_number} - {r.room_type}") for r in rooms]
    
    if form.validate_on_submit():
        # Validar disponibilidad
        existing = Reservation.query.filter(
            Reservation.room_id == form.room_id.data,
            Reservation.status != 'cancelled',
            or_(
                and_(Reservation.check_in_date <= form.check_in_date.data, Reservation.check_out_date > form.check_in_date.data),
                and_(Reservation.check_in_date < form.check_out_date.data, Reservation.check_out_date >= form.check_out_date.data),
                and_(Reservation.check_in_date >= form.check_in_date.data, Reservation.check_out_date <= form.check_out_date.data)
            )
        ).first()
        
        if existing:
            flash('La habitación no está disponible en esas fechas', 'danger')
            return redirect(url_for('reservations.create_reservation'))
        
        # Validar fechas
        if form.check_out_date.data <= form.check_in_date.data:
            flash('La fecha de salida debe ser posterior a la de entrada', 'danger')
            return redirect(url_for('reservations.create_reservation'))
        
        room = Room.query.get(form.room_id.data)
        if form.number_of_guests.data > room.capacity:
            flash(f'La habitación solo puede alojar {room.capacity} huéspedes', 'warning')
            return redirect(url_for('reservations.create_reservation'))
        
        reservation = Reservation(
            guest_id=form.guest_id.data,
            room_id=form.room_id.data,
            check_in_date=form.check_in_date.data,
            check_out_date=form.check_out_date.data,
            number_of_guests=form.number_of_guests.data,
            special_requests=form.special_requests.data,
            status='confirmed',
            total_price=form.number_of_guests.data,
            created_by_id=current_user.id
        )
        
        db.session.add(reservation)
        db.session.commit()
        
        log_action('CREATE', 'Reservation', reservation.id, new_values={'guest_id': form.guest_id.data})
        flash(f'Reservación creada exitosamente', 'success')
        return redirect(url_for('reservations.view_reservation', reservation_id=reservation.id))
    
    return render_template('reservations/create_reservation.html', form=form)


@reservations_bp.route('/<int:reservation_id>')
@staff_required
def view_reservation(reservation_id):
    """Ver detalles de la reservación"""
    reservation = Reservation.query.get_or_404(reservation_id)
    total_services_cost = sum(s.price for s in reservation.services)
    total_paid = sum(p.amount for p in reservation.payments if p.status == 'completed')
    
    return render_template('reservations/view_reservation.html', 
                         reservation=reservation, 
                         total_services_cost=total_services_cost,
                         total_paid=total_paid)


@reservations_bp.route('/<int:reservation_id>/change-status', methods=['POST'])
@staff_required
def change_reservation_status(reservation_id):
    """Cambiar estado de la reservación"""
    reservation = Reservation.query.get_or_404(reservation_id)
    new_status = request.json.get('status')
    
    valid_statuses = ['pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({'error': 'Estado inválido'}), 400
    
    old_status = reservation.status
    reservation.status = new_status
    
    # Cambiar estado de la habitación
    if new_status == 'checked_in':
        reservation.room.status = 'occupied'
    elif new_status in ['checked_out', 'cancelled']:
        reservation.room.status = 'cleaning'
        
        # Crear automáticamente una tarea de limpieza
        from datetime import datetime, timedelta
        housekeeping_task = HousekeepingTask(
            room_id=reservation.room_id,
            task_type='cleaning',
            status='pending',
            due_date=datetime.utcnow() + timedelta(hours=2),  # Vencimiento en 2 horas
            notes=f'Limpieza post-checkout - Reserva #{reservation.id}'
        )
        db.session.add(housekeeping_task)
    
    db.session.commit()
    
    log_action('UPDATE', 'Reservation', reservation_id, {'status': old_status}, {'status': new_status})
    return jsonify({'success': True, 'message': 'Estado actualizado'})


@reservations_bp.route('/<int:reservation_id>/add-service', methods=['POST'])
@staff_required
def add_service_to_reservation(reservation_id):
    """Agregar servicio a la reservación"""
    reservation = Reservation.query.get_or_404(reservation_id)
    service_id = request.json.get('service_id')
    
    service = Service.query.get_or_404(service_id)
    if service not in reservation.services:
        reservation.services.append(service)
        db.session.commit()
        log_action('UPDATE', 'Reservation', reservation_id, new_values={'action': 'add_service'})
        return jsonify({'success': True})
    
    return jsonify({'error': 'Servicio ya agregado'}), 400


@reservations_bp.route('/<int:reservation_id>/remove-service', methods=['POST'])
@staff_required
def remove_service_from_reservation(reservation_id):
    """Remover servicio de la reservación"""
    reservation = Reservation.query.get_or_404(reservation_id)
    service_id = request.json.get('service_id')
    
    service = Service.query.get_or_404(service_id)
    if service in reservation.services:
        reservation.services.remove(service)
        db.session.commit()
        log_action('UPDATE', 'Reservation', reservation_id, new_values={'action': 'remove_service'})
        return jsonify({'success': True})
    
    return jsonify({'error': 'Servicio no encontrado'}), 404


@reservations_bp.route('/<int:reservation_id>/extend', methods=['GET', 'POST'])
@staff_required
def extend_reservation(reservation_id):
    """Extender una reservación existente"""
    reservation = Reservation.query.get_or_404(reservation_id)
    form = ExtendReservationForm()
    
    if form.validate_on_submit():
        old_checkout = reservation.check_out_date
        new_checkout = form.new_check_out_date.data
        
        # Validar que la nueva fecha sea posterior a la actual
        if new_checkout <= reservation.check_out_date:
            flash('La nueva fecha debe ser posterior a la fecha actual de salida', 'danger')
            return redirect(url_for('reservations.extend_reservation', reservation_id=reservation_id))
        
        # Verificar que la habitación esté disponible en las nuevas fechas
        conflicting_reservations = Reservation.query.filter(
            Reservation.id != reservation_id,
            Reservation.room_id == reservation.room_id,
            Reservation.status.in_(['confirmed', 'checked_in']),
            Reservation.check_in_date < new_checkout,
            Reservation.check_out_date > reservation.check_out_date
        ).first()
        
        if conflicting_reservations:
            flash('La habitación no está disponible para las fechas solicitadas', 'warning')
            return redirect(url_for('reservations.extend_reservation', reservation_id=reservation_id))
        
        # Calcular costo adicional
        additional_nights = (new_checkout - reservation.check_out_date).days
        additional_cost = additional_nights * reservation.room.price_per_night
        
        # Actualizar la reservación
        old_total = reservation.total_price or 0
        reservation.check_out_date = new_checkout
        reservation.total_price = old_total + additional_cost
        
        db.session.commit()
        
        log_action('UPDATE', 'Reservation', reservation_id, 
                  old_values={'check_out_date': str(old_checkout), 'total_price': old_total},
                  new_values={'check_out_date': str(new_checkout), 'total_price': reservation.total_price})
        
        flash(f'Reservación extendida exitosamente. Costo adicional: ${additional_cost:.2f}', 'success')
        return redirect(url_for('reservations.view_reservation', reservation_id=reservation_id))
    
    return render_template('reservations/extend_reservation.html', form=form, reservation=reservation)


@reservations_bp.route('/quick-checkin', methods=['GET', 'POST'])
@staff_required
def quick_checkin():
    """Check-in rápido para clientes sin reservación previa (walk-in)"""
    # Cargar solo habitaciones disponibles
    available_rooms = Room.query.filter_by(status='available').all()
    
    form = QuickCheckInForm()
    # Asignar choices ANTES de validar
    form.room_id.choices = [(r.id, f"{r.room_number} - {r.room_type} (${r.price_per_night}/noche)") for r in available_rooms]
    
    if form.validate_on_submit():
        # Crear o obtener el huésped
        guest = Guest.query.filter_by(email=form.email.data).first() if form.email.data else None
        
        if not guest:
            guest = Guest(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data or '',
                phone=form.phone.data or '',
                document_number=form.document_number.data or '',
                document_type='passport'
            )
            db.session.add(guest)
            db.session.flush()  # Para obtener el ID del huésped
        
        # Crear la reservación
        room = Room.query.get(form.room_id.data)
        num_nights = (form.check_out_date.data - form.check_in_date.data).days
        total_price = num_nights * room.price_per_night
        
        reservation = Reservation(
            guest_id=guest.id,
            room_id=form.room_id.data,
            check_in_date=form.check_in_date.data,
            check_out_date=form.check_out_date.data,
            number_of_guests=form.number_of_guests.data,
            special_requests=form.special_requests.data,
            total_price=total_price,
            status='checked_in'  # Ya está marcado como checked in
        )
        
        # Marcar la habitación como ocupada
        room.status = 'occupied'
        
        # Agregar la reservación primero para obtener el ID
        db.session.add(reservation)
        db.session.flush()  # Obtener el ID sin hacer commit
        
        # Crear un pago automático para el check-in
        payment = Payment(
            reservation_id=reservation.id,
            amount=total_price,
            payment_method='cash',
            status='completed',
            notes='Check-in rápido - Walk-in (Pago en efectivo)'
        )
        
        db.session.add(payment)
        db.session.commit()
        
        log_action('CREATE', 'Reservation', reservation.id, new_values={'status': 'checked_in', 'guest': guest.full_name})
        log_action('CREATE', 'Payment', payment.id, new_values={'amount': total_price, 'status': 'completed'})
        
        flash(f'Cliente {guest.full_name} registrado en habitación {room.room_number}', 'success')
        return redirect(url_for('reservations.view_reservation', reservation_id=reservation.id))
    
    return render_template('reservations/quick_checkin.html', form=form)


@reservations_bp.route('/add', methods=['GET', 'POST'])
@staff_required
def add_reservation():
    """Redirige /add a /create para compatibilidad"""
    return redirect(url_for('reservations.create_reservation'))


@reservations_bp.route('/<int:reservation_id>/delete', methods=['POST'])
@admin_required
def delete_reservation(reservation_id):
    """Eliminar una reservación (solo admin)"""
    reservation = Reservation.query.get_or_404(reservation_id)
    guest_name = reservation.guest.full_name
    room_number = reservation.room.room_number
    
    # No permitir eliminar reservaciones activas
    if reservation.status in ['checked_in', 'confirmed']:
        flash(f'No se puede eliminar una reservación activa. Cambie el estado primero.', 'warning')
        return redirect(url_for('reservations.view_reservation', reservation_id=reservation_id))
    
    db.session.delete(reservation)
    db.session.commit()
    
    log_action('DELETE', 'Reservation', reservation_id, old_values={'guest': guest_name, 'room': room_number})
    flash(f'Reservación de {guest_name} eliminada', 'success')
    return redirect(url_for('reservations.list_reservations'))


# ==================== SERVICES ====================
@services_bp.route('/')
@staff_required
def list_services():
    """Lista todos los servicios"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    
    query = Service.query
    if category:
        query = query.filter_by(category=category)
    
    services = query.paginate(page=page, per_page=10)
    return render_template('services/list_services.html', services=services, current_category=category)


@services_bp.route('/add', methods=['GET', 'POST'])
@staff_required
def add_service():
    """Agregar nuevo servicio"""
    form = AddServiceForm()
    if form.validate_on_submit():
        service = Service(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            category=form.category.data
        )
        
        db.session.add(service)
        db.session.commit()
        
        log_action('CREATE', 'Service', service.id, new_values={'name': service.name})
        flash(f'Servicio {service.name} creado exitosamente', 'success')
        return redirect(url_for('services.list_services'))
    
    return render_template('services/add_service.html', form=form)


@services_bp.route('/<int:service_id>/edit', methods=['GET', 'POST'])
@staff_required
def edit_service(service_id):
    """Editar servicio"""
    service = Service.query.get_or_404(service_id)
    form = AddServiceForm()
    
    if form.validate_on_submit():
        old_values = {'name': service.name, 'price': service.price}
        
        service.name = form.name.data
        service.description = form.description.data
        service.price = form.price.data
        service.category = form.category.data
        
        db.session.commit()
        
        new_values = {'name': service.name, 'price': service.price}
        log_action('UPDATE', 'Service', service_id, old_values, new_values)
        
        flash('Servicio actualizado', 'success')
        return redirect(url_for('services.list_services'))
    
    elif request.method == 'GET':
        form.name.data = service.name
        form.description.data = service.description
        form.price.data = service.price
        form.category.data = service.category
    
    return render_template('services/edit_service.html', form=form, service=service)


@services_bp.route('/<int:service_id>/toggle-status', methods=['POST'])
@staff_required
def toggle_service_status(service_id):
    """Activar/desactivar servicio"""
    service = Service.query.get_or_404(service_id)
    service.is_active = not service.is_active
    db.session.commit()
    
    log_action('UPDATE', 'Service', service_id, new_values={'is_active': service.is_active})
    return jsonify({'success': True, 'is_active': service.is_active})


@services_bp.route('/<int:service_id>/delete', methods=['POST'])
@admin_required
def delete_service(service_id):
    """Eliminar un servicio (solo admin)"""
    service = Service.query.get_or_404(service_id)
    service_name = service.name
    
    db.session.delete(service)
    db.session.commit()
    
    log_action('DELETE', 'Service', service_id, old_values={'name': service_name})
    flash(f'Servicio {service_name} eliminado', 'success')
    return redirect(url_for('services.list_services'))


# ==================== PAYMENTS ====================
@payments_bp.route('/')
@staff_required
def list_payments():
    """Listar todos los pagos"""
    page = request.args.get('page', 1, type=int)
    payments = Payment.query.paginate(page=page, per_page=10)
    
    return render_template('payments/list_payments.html', 
                         payments=payments.items,
                         pages=payments.pages,
                         current_page=page)


@payments_bp.route('/<int:reservation_id>')
@staff_required
def process_payment(reservation_id):
    """Procesar pago para una reservación"""
    reservation = Reservation.query.get_or_404(reservation_id)
    form = ProcessPaymentForm()
    
    total_services_cost = sum(s.price for s in reservation.services)
    total_amount = reservation.room_cost + total_services_cost
    total_paid = sum(p.amount for p in reservation.payments if p.status == 'completed')
    pending_amount = total_amount - total_paid
    
    if form.validate_on_submit():
        if form.amount.data > pending_amount:
            flash('El monto excede el saldo pendiente', 'warning')
            return redirect(url_for('payments.process_payment', reservation_id=reservation_id))
        
        payment = Payment(
            reservation_id=reservation_id,
            amount=form.amount.data,
            payment_method=form.payment_method.data,
            status='completed',
            notes=form.notes.data
        )
        
        db.session.add(payment)
        db.session.commit()
        
        log_action('CREATE', 'Payment', payment.id, new_values={'amount': form.amount.data})
        flash(f'Pago de ${form.amount.data} procesado exitosamente', 'success')
        return redirect(url_for('reservations.view_reservation', reservation_id=reservation_id))
    
    return render_template('payments/process_payment.html', 
                         form=form, 
                         reservation=reservation,
                         total_amount=total_amount,
                         total_paid=total_paid,
                         pending_amount=pending_amount)


@payments_bp.route('/add', methods=['GET', 'POST'])
@staff_required
def add_payment():
    """Agregar un nuevo pago manualmente"""
    # Cargar reservaciones disponibles
    reservations = Reservation.query.filter(Reservation.status.in_(['confirmed', 'checked_in'])).all()
    
    form = ProcessPaymentForm()
    # Asignar choices ANTES de validar
    form.reservation_id.choices = [(r.id, f"Reserv. #{r.id} - Hab. {r.room.room_number} - {r.guest.full_name}") for r in reservations]
    
    if form.validate_on_submit():
        reservation = Reservation.query.get(form.reservation_id.data)
        
        payment = Payment(
            reservation_id=form.reservation_id.data,
            amount=form.amount.data,
            payment_method=form.payment_method.data,
            status=form.status.data,
            notes=form.notes.data
        )
        
        # Si el pago se marca como completado, actualizar la habitación a ocupada
        if form.status.data == 'completed':
            reservation.status = 'checked_in'
            reservation.room.status = 'occupied'
        
        db.session.add(payment)
        db.session.commit()
        
        log_action('CREATE', 'Payment', payment.id, new_values={'amount': form.amount.data})
        flash('Pago registrado exitosamente', 'success')
        return redirect(url_for('payments.list_payments'))
    
    return render_template('payments/add_payment.html', form=form)


@payments_bp.route('/<int:payment_id>/view')
@staff_required
def view_payment(payment_id):
    """Ver detalles de un pago"""
    payment = Payment.query.get_or_404(payment_id)
    return render_template('payments/view_payment.html', payment=payment)


@payments_bp.route('/<int:payment_id>/edit', methods=['GET', 'POST'])
@staff_required
def edit_payment(payment_id):
    """Editar un pago"""
    payment = Payment.query.get_or_404(payment_id)
    form = ProcessPaymentForm()
    
    if form.validate_on_submit():
        payment.amount = form.amount.data
        payment.payment_method = form.payment_method.data
        payment.notes = form.notes.data
        
        db.session.commit()
        
        log_action('UPDATE', 'Payment', payment.id, new_values={'amount': payment.amount})
        flash('Pago actualizado exitosamente', 'success')
        return redirect(url_for('payments.view_payment', payment_id=payment_id))
    
    elif request.method == 'GET':
        form.amount.data = payment.amount
        form.payment_method.data = payment.payment_method
        form.notes.data = payment.notes
    
    return render_template('payments/edit_payment.html', form=form, payment=payment)


@payments_bp.route('/<int:payment_id>/delete', methods=['POST'])
@admin_required
def delete_payment(payment_id):
    """Eliminar un pago (solo admin)"""
    payment = Payment.query.get_or_404(payment_id)
    payment_amount = payment.amount
    
    db.session.delete(payment)
    db.session.commit()
    
    log_action('DELETE', 'Payment', payment_id, old_values={'amount': payment_amount})
    flash(f'Pago de ${payment_amount:.2f} eliminado', 'success')
    return redirect(url_for('payments.list_payments'))


# ==================== MAINTENANCE ====================
@maintenance_bp.route('/')
@staff_required
def list_maintenance():
    """Lista todos los problemas de mantenimiento"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    
    query = MaintenanceLog.query
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    
    maintenance_logs = query.order_by(MaintenanceLog.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('maintenance/list_maintenance.html', maintenance_logs=maintenance_logs, current_status=status, current_priority=priority)


@maintenance_bp.route('/create', methods=['GET', 'POST'])
@staff_required
def create_maintenance():
    """Crear reporte de mantenimiento"""
    # Cargar datos ANTES de crear el formulario
    rooms = Room.query.all()
    form = CreateMaintenanceForm()
    # Asignar choices INMEDIATAMENTE después de crear el formulario
    form.room_id.choices = [(r.id, f"{r.room_number} - Piso {r.floor}") for r in rooms]
    
    if form.validate_on_submit():
        maintenance_log = MaintenanceLog(
            room_id=form.room_id.data,
            issue_type=form.issue_type.data,
            description=form.description.data,
            priority=form.priority.data,
            assigned_to=form.assigned_to.data
        )
        
        # Cambiar estado de la habitación si es crítico
        if form.priority.data == 'critical':
            room = Room.query.get(form.room_id.data)
            room.status = 'maintenance'
        
        db.session.add(maintenance_log)
        db.session.commit()
        
        log_action('CREATE', 'MaintenanceLog', maintenance_log.id, new_values={'issue_type': form.issue_type.data})
        flash('Reporte de mantenimiento creado', 'success')
        return redirect(url_for('maintenance.list_maintenance'))
    
    return render_template('maintenance/create_maintenance.html', form=form)


@maintenance_bp.route('/<int:log_id>/complete', methods=['POST'])
@staff_required
def complete_maintenance(log_id):
    """Marcar un problema de mantenimiento como completado"""
    maintenance_log = MaintenanceLog.query.get_or_404(log_id)
    
    old_status = maintenance_log.status
    maintenance_log.status = 'completed'
    maintenance_log.completed_at = datetime.utcnow()
    
    # Cambiar estado de la habitación de vuelta a disponible si es necesario
    room = maintenance_log.room
    if room.status == 'maintenance':
        room.status = 'available'
    
    db.session.commit()
    
    log_action('UPDATE', 'MaintenanceLog', log_id, {'status': old_status}, {'status': 'completed'})
    flash('Problema de mantenimiento marcado como completado', 'success')
    return redirect(url_for('maintenance.list_maintenance'))


@maintenance_bp.route('/add', methods=['GET', 'POST'])
def add_maintenance_redirect():
    """Redirige /add a /create para compatibilidad"""
    return redirect(url_for('maintenance.create_maintenance'))


@maintenance_bp.route('/<int:maintenance_id>/update-status', methods=['POST'])
@staff_required
def update_maintenance_status(maintenance_id):
    """Actualizar estado del mantenimiento"""
    maintenance_log = MaintenanceLog.query.get_or_404(maintenance_id)
    new_status = request.json.get('status')
    
    valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({'error': 'Estado inválido'}), 400
    
    old_status = maintenance_log.status
    maintenance_log.status = new_status
    
    if new_status == 'completed':
        maintenance_log.completed_at = datetime.utcnow()
        # Cambiar estado de la habitación a disponible
        maintenance_log.room.status = 'available'
    
    db.session.commit()
    
    log_action('UPDATE', 'MaintenanceLog', maintenance_id, {'status': old_status}, {'status': new_status})
    return jsonify({'success': True})


# ==================== HOUSEKEEPING ====================
@housekeeping_bp.route('/')
@staff_required
def list_housekeeping_tasks():
    """Lista todas las tareas de limpieza"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    task_type = request.args.get('type', '')
    
    query = HousekeepingTask.query
    if status:
        query = query.filter_by(status=status)
    if task_type:
        query = query.filter_by(task_type=task_type)
    
    tasks = query.order_by(HousekeepingTask.due_date).paginate(page=page, per_page=10)
    return render_template('housekeeping/list_tasks.html', tasks=tasks, current_status=status, current_type=task_type)


@housekeeping_bp.route('/create', methods=['GET', 'POST'])
@staff_required
def create_housekeeping_task():
    """Crear tarea de limpieza"""
    # Cargar datos ANTES de crear el formulario
    rooms = Room.query.all()
    form = CreateHousekeepingTaskForm()
    # Asignar choices INMEDIATAMENTE después de crear el formulario
    form.room_id.choices = [(r.id, f"{r.room_number} - {r.room_type}") for r in rooms]
    
    if form.validate_on_submit():
        task = HousekeepingTask(
            room_id=form.room_id.data,
            task_type=form.task_type.data,
            due_date=form.due_date.data,
            assigned_to=form.assigned_to.data,
            notes=form.notes.data
        )
        
        db.session.add(task)
        db.session.commit()
        
        log_action('CREATE', 'HousekeepingTask', task.id, new_values={'task_type': form.task_type.data})
        flash('Tarea de limpieza creada', 'success')
        return redirect(url_for('housekeeping.list_housekeeping_tasks'))
    
    return render_template('housekeeping/create_task.html', form=form)


@housekeeping_bp.route('/<int:task_id>/update-status', methods=['POST'])
@staff_required
def update_housekeeping_status(task_id):
    """Actualizar estado de la tarea"""
    task = HousekeepingTask.query.get_or_404(task_id)
    new_status = request.json.get('status')
    
    valid_statuses = ['pending', 'in_progress', 'completed', 'hold']
    if new_status not in valid_statuses:
        return jsonify({'error': 'Estado inválido'}), 400
    
    old_status = task.status
    task.status = new_status
    
    if new_status == 'completed':
        task.completed_at = datetime.utcnow()
    
    db.session.commit()
    
    log_action('UPDATE', 'HousekeepingTask', task_id, {'status': old_status}, {'status': new_status})
    return jsonify({'success': True})


@housekeeping_bp.route('/<int:task_id>/complete', methods=['POST'])
@staff_required
def complete_housekeeping_task(task_id):
    """Marcar una tarea como completada"""
    task = HousekeepingTask.query.get_or_404(task_id)
    room = task.room
    
    # Actualizar estado de la habitación a "available"
    room.status = 'available'
    
    # Eliminar la tarea
    db.session.delete(task)
    db.session.commit()
    
    log_action('UPDATE', 'Room', room.id, {'status': 'cleaning'}, {'status': 'available'})
    log_action('DELETE', 'HousekeepingTask', task_id)
    flash('Tarea completada y habitación disponible', 'success')
    return redirect(url_for('housekeeping.list_housekeeping_tasks'))


@housekeeping_bp.route('/add', methods=['GET', 'POST'])
@staff_required
def add_housekeeping_task():
    """Redirige /add a /create para compatibilidad"""
    return redirect(url_for('housekeeping.create_housekeeping_task'))


# ==================== WHATSAPP RESERVATIONS ====================
@whatsapp_bp.route('/reservation', methods=['GET', 'POST'])
def whatsapp_reservation():
    """Formulario público de reserva por WhatsApp"""
    form = WhatsAppReservationForm()
    
    if form.validate_on_submit():
        # Generar mensaje para WhatsApp
        check_in = form.check_in_date.data.strftime('%d/%m/%Y')
        check_out = form.check_out_date.data.strftime('%d/%m/%Y')
        
        # Calcular noches
        noches = (form.check_out_date.data - form.check_in_date.data).days
        
        mensaje = f"""Hola! 👋 Me gustaría realizar una reserva en el hotel.

📋 Datos personales:
• Nombre: {form.first_name.data} {form.last_name.data}
• Email: {form.email.data}
• Teléfono: {form.phone.data}

🛏️ Detalles de la reserva:
• Tipo de habitación: {form.room_type.data}
• Fecha de entrada: {check_in}
• Fecha de salida: {check_out}
• Número de noches: {noches}
• Número de huéspedes: {form.number_of_guests.data}

{'💬 Solicitudes especiales: ' + form.special_requests.data if form.special_requests.data else ''}

Espero confirmación. ¡Gracias! 🙏"""
        
        # Limpiar teléfono (remover espacios, guiones, paréntesis)
        phone = form.phone.data.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Construir URL de WhatsApp
        # Usa la API de WhatsApp Web para iniciar un chat
        whatsapp_url = f"https://wa.me/{phone}?text={mensaje.replace(chr(10), '%0a').replace(' ', '%20')}"
        
        # Aquí también podrías guardar la solicitud en la BD si quieres llevar registro
        
        return redirect(whatsapp_url)
    
    return render_template('whatsapp/reservation.html', form=form)


@whatsapp_bp.route('/booking-link')
def booking_link():
    """Página para compartir el link de reservas"""
    return render_template('whatsapp/booking_link.html')
