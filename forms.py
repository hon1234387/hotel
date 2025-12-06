from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, FloatField, TextAreaField, SelectField, BooleanField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, NumberRange, Optional
from models import User, Guest, Room

class LoginForm(FlaskForm):
    """Formulario de inicio de sesión"""
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')


class RegisterForm(FlaskForm):
    """Formulario de registro de empleados"""
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Nombre Completo', validators=[DataRequired(), Length(min=3, max=120)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', 
                                      validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Rol', choices=[('receptionist', 'Recepcionista'), 
                                       ('housekeeper', 'Ama de Llaves'),
                                       ('manager', 'Gerente'),
                                       ('staff', 'Personal')], default='staff')
    phone = StringField('Teléfono', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Registrar')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('El usuario ya existe')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('El email ya está registrado')


class AddGuestForm(FlaskForm):
    """Formulario para agregar huéspedes"""
    first_name = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=80)])
    last_name = StringField('Apellido', validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Teléfono', validators=[DataRequired(), Length(min=7, max=20)])
    document_type = SelectField('Tipo de Documento', 
                               choices=[('passport', 'Pasaporte'), 
                                      ('id', 'Cédula/DNI'),
                                      ('license', 'Licencia de Conducir')],
                               validators=[DataRequired()])
    document_number = StringField('Número de Documento', validators=[DataRequired(), Length(min=5, max=50)])
    nationality = StringField('Nacionalidad', validators=[Optional(), Length(max=80)])
    address = StringField('Dirección', validators=[Optional(), Length(max=200)])
    city = StringField('Ciudad', validators=[Optional(), Length(max=80)])
    country = StringField('País', validators=[Optional(), Length(max=80)])
    submit = SubmitField('Guardar Huésped')
    
    def validate_email(self, email):
        guest = Guest.query.filter_by(email=email.data).first()
        if guest:
            raise ValidationError('El email ya está registrado')
    
    def validate_document_number(self, document_number):
        guest = Guest.query.filter_by(document_number=document_number.data).first()
        if guest:
            raise ValidationError('Este número de documento ya está registrado')


class AddRoomForm(FlaskForm):
    """Formulario para agregar habitaciones"""
    room_number = StringField('Número de Habitación', validators=[DataRequired(), Length(min=1, max=10)])
    room_type = SelectField('Tipo de Habitación', 
                           choices=[('single', 'Individual'), 
                                  ('double', 'Doble'),
                                  ('suite', 'Suite'),
                                  ('deluxe', 'Deluxe')],
                           validators=[DataRequired()])
    floor = IntegerField('Piso', validators=[DataRequired(), NumberRange(min=0, max=50)])
    capacity = IntegerField('Capacidad', validators=[DataRequired(), NumberRange(min=1, max=10)])
    price_per_night = FloatField('Precio por Noche', validators=[DataRequired(), NumberRange(min=0.01)])
    description = TextAreaField('Descripción', validators=[Optional(), Length(max=500)])
    amenities = StringField('Amenidades (separadas por comas)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Guardar Habitación')
    
    def validate_room_number(self, room_number):
        room = Room.query.filter_by(room_number=room_number.data).first()
        if room:
            raise ValidationError('Este número de habitación ya existe')


class MakeReservationForm(FlaskForm):
    """Formulario para hacer reservaciones"""
    guest_id = SelectField('Huésped', coerce=int, choices=[], validators=[DataRequired()])
    room_id = SelectField('Habitación', coerce=int, choices=[], validators=[DataRequired()])
    check_in_date = DateField('Fecha de Entrada', validators=[DataRequired()])
    check_out_date = DateField('Fecha de Salida', validators=[DataRequired()])
    number_of_guests = IntegerField('Número de Huéspedes', validators=[DataRequired(), NumberRange(min=1, max=10)])
    special_requests = TextAreaField('Solicitudes Especiales', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Crear Reservación')


class AddServiceForm(FlaskForm):
    """Formulario para agregar servicios"""
    name = StringField('Nombre del Servicio', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Descripción', validators=[Optional(), Length(max=500)])
    price = FloatField('Precio', validators=[DataRequired(), NumberRange(min=0.01)])
    category = SelectField('Categoría', 
                          choices=[('room_service', 'Servicio de Habitación'),
                                 ('spa', 'Spa'),
                                 ('laundry', 'Lavandería'),
                                 ('parking', 'Estacionamiento'),
                                 ('transportation', 'Transporte'),
                                 ('activities', 'Actividades'),
                                 ('other', 'Otro')],
                          validators=[DataRequired()])
    submit = SubmitField('Guardar Servicio')


class ProcessPaymentForm(FlaskForm):
    """Formulario para procesar pagos"""
    reservation_id = SelectField('Reservación', coerce=int, choices=[], validators=[DataRequired()])
    amount = FloatField('Monto', validators=[DataRequired(), NumberRange(min=0.01)])
    payment_method = SelectField('Método de Pago', 
                                choices=[('cash', 'Efectivo'),
                                       ('credit_card', 'Tarjeta de Crédito'),
                                       ('debit_card', 'Tarjeta de Débito'),
                                       ('check', 'Cheque')],
                                validators=[DataRequired()])
    status = SelectField('Estado',
                        choices=[('pending', 'Pendiente'),
                               ('completed', 'Completado'),
                               ('cancelled', 'Cancelado')],
                        validators=[DataRequired()])
    notes = TextAreaField('Notas', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Procesar Pago')


class CreateMaintenanceForm(FlaskForm):
    """Formulario para crear registros de mantenimiento"""
    room_id = SelectField('Habitación', coerce=int, choices=[], validators=[DataRequired()])
    issue_type = StringField('Tipo de Problema', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Descripción', validators=[DataRequired(), Length(min=5, max=500)])
    priority = SelectField('Prioridad', 
                          choices=[('low', 'Baja'),
                                 ('medium', 'Media'),
                                 ('high', 'Alta'),
                                 ('critical', 'Crítica')],
                          validators=[DataRequired()])
    assigned_to = StringField('Asignado a', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Crear Problema')


class CreateHousekeepingTaskForm(FlaskForm):
    """Formulario para crear tareas de limpieza"""
    room_id = SelectField('Habitación', coerce=int, choices=[], validators=[DataRequired()])
    task_type = SelectField('Tipo de Tarea', 
                           choices=[('cleaning', 'Limpieza'),
                                  ('inspection', 'Inspección'),
                                  ('turnover', 'Cambio de Huésped')],
                           validators=[DataRequired()])
    due_date = DateField('Fecha de Vencimiento', validators=[DataRequired()])
    assigned_to = StringField('Asignado a', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notas', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Crear Tarea')


class ExtendReservationForm(FlaskForm):
    """Formulario para extender una reservación"""
    new_check_out_date = DateField('Nueva Fecha de Salida', validators=[DataRequired()])
    notes = TextAreaField('Notas de la Extensión', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Extender Reservación')


class QuickCheckInForm(FlaskForm):
    """Formulario para check-in rápido (walk-in)"""
    first_name = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Apellido', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Teléfono', validators=[Optional(), Length(max=20)])
    document_number = StringField('Documento', validators=[Optional(), Length(max=20)])
    room_id = SelectField('Habitación', coerce=int, choices=[], validators=[DataRequired()])
    check_in_date = DateField('Fecha de Entrada', validators=[DataRequired()])
    check_out_date = DateField('Fecha de Salida', validators=[DataRequired()])
    number_of_guests = IntegerField('Número de Huéspedes', validators=[DataRequired(), NumberRange(min=1, max=10)])
    special_requests = TextAreaField('Solicitudes Especiales', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Registrar Check-in')


class WhatsAppReservationForm(FlaskForm):
    """Formulario público para reservas por WhatsApp"""
    first_name = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Apellido', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Teléfono (con código de país)', validators=[DataRequired(), Length(min=10, max=20)])
    check_in_date = DateField('Fecha de Entrada', validators=[DataRequired()])
    check_out_date = DateField('Fecha de Salida', validators=[DataRequired()])
    room_type = SelectField('Tipo de Habitación', 
                           choices=[('standard', 'Estándar'), 
                                   ('deluxe', 'Deluxe'),
                                   ('suite', 'Suite')],
                           validators=[DataRequired()])
    number_of_guests = IntegerField('Número de Huéspedes', validators=[DataRequired(), NumberRange(min=1, max=10)])
    special_requests = TextAreaField('Solicitudes Especiales', validators=[Optional(), Length(max=300)])
    submit = SubmitField('Enviar por WhatsApp')
