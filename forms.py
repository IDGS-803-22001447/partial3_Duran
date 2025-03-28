# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, RadioField, DateField
from wtforms import SelectMultipleField, widgets
from wtforms.validators import DataRequired, Length, NumberRange
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    nombreUsuario = StringField('Usuario', validators=[DataRequired()])
    contrasenia = PasswordField('Contraseña', validators=[DataRequired()])
    
class MultiCheckboxField(SelectMultipleField):
    """
    Campo personalizado para renderizar cada choice como un checkbox independiente.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class PizzaForm(FlaskForm):
    # Datos del cliente
    nombre = StringField('Nombre', validators=[
        DataRequired(message='El nombre es requerido'),
        Length(min=4, max=50, message='El nombre debe tener entre 4 y 50 caracteres')
    ])
    direccion = StringField('Dirección', validators=[
        DataRequired(message='La dirección es requerida')
    ])
    telefono = StringField('Teléfono', validators=[
        DataRequired(message='El teléfono es requerido')
    ])
    fecha_pedido = DateField('Fecha de Pedido', format='%Y-%m-%d', validators=[
        DataRequired(message='La fecha de pedido es requerida')
    ])

    # Tamaño (RadioField)
    tamano = RadioField('Tamaño', choices=[
        ('Chica', 'Chica $40'),
        ('Mediana', 'Mediana $80'),
        ('Grande', 'Grande $120')
    ], validators=[DataRequired(message='Selecciona un tamaño de pizza')])

    # Ingredientes: usando MultiCheckboxField
    ingredientes = MultiCheckboxField(
        'Ingredientes Extras ($10 c/u)',
        choices=[
            ('Jamón', 'Jamón'),
            ('Piña', 'Piña'),
            ('Champiñones', 'Champiñones')
        ]
    )

    cantidad = IntegerField('Cantidad de Pizzas', validators=[
        DataRequired(message='Ingresa cuántas pizzas de este tipo'),
        NumberRange(min=1, message='La cantidad mínima es 1')
    ])
