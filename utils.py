"""
Funciones utilitarias para el sistema de gestión hotelera
"""

from datetime import datetime, timedelta
from models import Reservation, Room, Payment

def get_room_status_summary():
    """Obtiene un resumen del estado de las habitaciones"""
    total_rooms = Room.query.count()
    available_rooms = Room.query.filter_by(status='available').count()
    occupied_rooms = Room.query.filter_by(status='occupied').count()
    maintenance_rooms = Room.query.filter_by(status='maintenance').count()
    cleaning_rooms = Room.query.filter_by(status='cleaning').count()
    
    return {
        'total': total_rooms,
        'available': available_rooms,
        'occupied': occupied_rooms,
        'maintenance': maintenance_rooms,
        'cleaning': cleaning_rooms,
        'occupancy_rate': (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
    }

def calculate_revenue_today():
    """Calcula los ingresos del día actual"""
    today = datetime.utcnow().date()
    payments = Payment.query.filter(
        Payment.payment_date >= datetime.combine(today, datetime.min.time()),
        Payment.payment_date <= datetime.combine(today, datetime.max.time()),
        Payment.status == 'completed'
    ).all()
    
    return sum(p.amount for p in payments)

def calculate_revenue_week():
    """Calcula los ingresos de la semana actual"""
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday())
    
    payments = Payment.query.filter(
        Payment.payment_date >= week_start,
        Payment.status == 'completed'
    ).all()
    
    return sum(p.amount for p in payments)

def get_occupancy_forecast(days_ahead=7):
    """Obtiene pronóstico de ocupación para los próximos días"""
    forecast = {}
    today = datetime.utcnow().date()
    
    for i in range(days_ahead):
        current_date = today + timedelta(days=i)
        occupied = Reservation.query.filter(
            Reservation.check_in_date <= current_date,
            Reservation.check_out_date > current_date,
            Reservation.status != 'cancelled'
        ).count()
        
        total_rooms = Room.query.count()
        occupancy_rate = (occupied / total_rooms * 100) if total_rooms > 0 else 0
        
        forecast[current_date.strftime('%d/%m')] = {
            'occupied_rooms': occupied,
            'occupancy_rate': round(occupancy_rate, 2)
        }
    
    return forecast

def get_pending_tasks_summary():
    """Obtiene resumen de tareas pendientes"""
    from models import HousekeepingTask, MaintenanceLog
    
    pending_cleaning = HousekeepingTask.query.filter(
        HousekeepingTask.status.in_(['pending', 'in_progress'])
    ).count()
    
    pending_maintenance = MaintenanceLog.query.filter(
        MaintenanceLog.status.in_(['pending', 'in_progress'])
    ).count()
    
    return {
        'pending_cleaning': pending_cleaning,
        'pending_maintenance': pending_maintenance,
        'total_pending': pending_cleaning + pending_maintenance
    }

def calculate_average_stay_duration():
    """Calcula la duración promedio de estadía"""
    from sqlalchemy import func
    
    reservations = Reservation.query.filter(
        Reservation.status.in_(['checked_out', 'completed'])
    ).all()
    
    if not reservations:
        return 0
    
    total_nights = sum((r.check_out_date - r.check_in_date).days for r in reservations)
    return total_nights / len(reservations)

def get_room_rating_by_type():
    """Obtiene estadísticas de uso por tipo de habitación"""
    room_types = {}
    
    rooms = Room.query.all()
    for room in rooms:
        if room.room_type not in room_types:
            room_types[room.room_type] = {
                'total': 0,
                'available': 0,
                'occupied': 0,
                'avg_price': 0
            }
        
        room_types[room.room_type]['total'] += 1
        if room.status == 'available':
            room_types[room.room_type]['available'] += 1
        elif room.status == 'occupied':
            room_types[room.room_type]['occupied'] += 1
        room_types[room.room_type]['avg_price'] = room.price_per_night
    
    return room_types

def export_reservations_to_csv(reservations):
    """Exporta reservaciones a formato CSV"""
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Encabezados
    writer.writerow([
        'ID', 'Huésped', 'Habitación', 'Check-in', 'Check-out',
        'Noches', 'Huéspedes', 'Total', 'Estado'
    ])
    
    # Datos
    for res in reservations:
        writer.writerow([
            res.id,
            res.guest.full_name,
            res.room.room_number,
            res.check_in_date.strftime('%d/%m/%Y'),
            res.check_out_date.strftime('%d/%m/%Y'),
            res.nights,
            res.number_of_guests,
            res.room_cost,
            res.status
        ])
    
    return output.getvalue()

def send_reservation_confirmation_email(guest, reservation):
    """Envía email de confirmación de reservación (placeholder)"""
    # Esta función puede ser expandida para enviar emails reales
    # usando Flask-Mail u otro servicio
    
    email_body = f"""
    Estimado(a) {guest.full_name},
    
    Su reservación ha sido confirmada.
    
    Detalles:
    - Habitación: {reservation.room.room_number}
    - Check-in: {reservation.check_in_date.strftime('%d/%m/%Y')}
    - Check-out: {reservation.check_out_date.strftime('%d/%m/%Y')}
    - Noches: {reservation.nights}
    - Total: ${reservation.room_cost}
    
    ¡Gracias por elegirnos!
    """
    
    return email_body
