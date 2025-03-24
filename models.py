from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import datetime
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
class User(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombreUsuario = db.Column(db.String(100), unique=True, nullable=False)
    contrasenia = db.Column(db.String(300), nullable=False)
    rol= db.Column(db.String(50), nullable=False)  # Ejemplo: "admin", "cliente"


class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id = db.Column(db.Integer, primary_key=True)

    # Datos del cliente
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)

    # Fecha de pedido y total
    fecha_pedido = db.Column(db.DateTime, default=datetime.datetime.now)
    total = db.Column(db.Float, default=0.0)

    # Relación: un Pedido -> varios DetallePizza
    detalle_pizzas = db.relationship(
        'DetallePizza',
        backref='pedido',
        lazy=True,
        cascade="all, delete-orphan"
    )

class DetallePizza(db.Model):
    __tablename__ = 'detalle_pizzas'
    id = db.Column(db.Integer, primary_key=True)

    # FK que referencia la tabla 'pedidos'
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)

    # Datos de la pizza
    tamano = db.Column(db.String(20), nullable=False)   # "Chica", "Mediana", "Grande"
    ingredientes = db.Column(db.String(200), nullable=True)
    cantidad = db.Column(db.Integer, default=1)
    subtotal = db.Column(db.Float, default=0.0)
