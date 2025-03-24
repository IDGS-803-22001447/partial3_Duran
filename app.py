from flask import Flask, render_template,request,redirect,url_for,flash
from flask import flash
from werkzeug.security import check_password_hash, generate_password_hash
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from flask import g
from flask import render_template, redirect, url_for, flash
from werkzeug.security import check_password_hash
from models import User
import forms  
from io import open
import os
from models import db, DetallePizza, Pedido
from flask import render_template, request
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from models import db, User 

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf=CSRFProtect()
ARCHIVO_TEMP = "pizzas_temp.txt"
app.config.from_object(DevelopmentConfig)


login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."
login_manager.login_view = "login"

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("index"))  # Redirigir al index si ya estás autenticado
    return redirect(url_for("login"))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route("/login", methods=["GET", "POST"])
def login():
    form = forms.LoginForm()

    if form.validate_on_submit():
      
        user = User.query.filter_by(nombreUsuario=form.nombreUsuario.data).first()
        if user and check_password_hash(user.contrasenia, form.contrasenia.data):
           
            login_user(user)
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for("index"))

        flash('Usuario o contraseña incorrectos', 'danger')

    return render_template('login.html', form=form)


@app.route("/logout")
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/")
@app.route("/index", methods=["GET", "POST"])
@login_required 
def index():
    form_pizza = forms.PizzaForm(request.form)
    if request.method == "POST" and "filtro_fecha" not in request.form:
      
        if form_pizza.validate():
            tamano = form_pizza.tamano.data
            ingredientes_list = form_pizza.ingredientes.data  
            cantidad = form_pizza.cantidad.data
            precio_base = {"Chica": 40, "Mediana": 80, "Grande": 120}.get(tamano, 0)
            precio_ingredientes = len(ingredientes_list) * 10
            subtotal = (precio_base + precio_ingredientes) * cantidad
            ingredientes_str = ", ".join(ingredientes_list)
            linea = f"{tamano}|{ingredientes_str}|{cantidad}|{subtotal}\n"

            with open(ARCHIVO_TEMP, "a", encoding="utf-8") as f:
                f.write(linea)

            flash("Pizza agregada.", "success")
        else:
            flash("Error en datos de la pizza.", "danger")

    # Cargar pizzas temporales
    pizzas_temp = []
    if os.path.exists(ARCHIVO_TEMP):
        with open(ARCHIVO_TEMP, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) == 4:
                    pizzas_temp.append({
                        "tamano": parts[0],
                        "ingredientes": parts[1],
                        "cantidad": parts[2],
                        "subtotal": parts[3]
                    })

    # -------- Historial de Ventas --------
    pedidos_filtrados = []
    total_ventas = 0.0

    if request.method == "POST" and "filtro_fecha" in request.form:
        filtro = request.form.get("filtro_fecha")
        fecha = request.form.get("fecha")

        if fecha:
            import datetime
            fecha_obj = datetime.datetime.strptime(fecha, "%Y-%m-%d")

            if filtro == "dia":
                pedidos_filtrados = Pedido.query.filter(
                    db.extract('year', Pedido.fecha_pedido) == fecha_obj.year,
                    db.extract('month', Pedido.fecha_pedido) == fecha_obj.month,
                    db.extract('day', Pedido.fecha_pedido) == fecha_obj.day
                ).all()
            elif filtro == "mes":
                pedidos_filtrados = Pedido.query.filter(
                    db.extract('year', Pedido.fecha_pedido) == fecha_obj.year,
                    db.extract('month', Pedido.fecha_pedido) == fecha_obj.month
                ).all()

            total_ventas = sum(p.total for p in pedidos_filtrados)

    return render_template("index.html", 
                           form=form_pizza, 
                           pizzas=pizzas_temp, 
                           pedidos=pedidos_filtrados, 
                           total_ventas=total_ventas)


@app.route("/quitar", methods=["POST"])
def quitar():
  
    idx = request.form.get("idx")  # índice de la pizza a quitar
    if idx is not None and os.path.exists(ARCHIVO_TEMP):
        idx = int(idx)
        # Leemos todas las líneas
        with open(ARCHIVO_TEMP, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Reescribimos todas MENOS la de la posición idx
        with open(ARCHIVO_TEMP, "w", encoding="utf-8") as f:
            for i, line in enumerate(lines):
                if i != idx:
                    f.write(line)
        flash("Pizza eliminada de la orden.", "warning")

    return redirect(url_for("index"))

@app.route("/terminar", methods=["POST"])
def terminar():

    form_pizza = forms.PizzaForm(request.form)
    nombre = request.form.get("nombre")
    direccion = request.form.get("direccion")
    telefono = request.form.get("telefono")
    fecha_pedido = request.form.get("fecha_pedido")

    pizzas_temp = []
    total_general = 0.0

    if os.path.exists(ARCHIVO_TEMP):
        with open(ARCHIVO_TEMP, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) == 4:
                    tamano = parts[0]
                    ingredientes = parts[1]
                    cantidad = int(parts[2])
                    subtotal = float(parts[3])
                    pizzas_temp.append((tamano, ingredientes, cantidad, subtotal))
                    total_general += subtotal

  
    # Si no hay pizzas en pizzas_temp, no se debe crear el pedido
    if not pizzas_temp:
        flash("No hay pizzas en la orden de pedido.", "danger")
        return redirect(url_for("index"))

    # 1) Creamos un objeto Pedido
    nuevo_pedido = Pedido(
        nombre=nombre,
        direccion=direccion,
        telefono=telefono
        
    )
    nuevo_pedido.total = total_general
    db.session.add(nuevo_pedido)
    db.session.commit()

    # 2) Insertamos los DetallePizza asociados
    for (tamano, ingredientes, cantidad, subtotal) in pizzas_temp:
        detalle = DetallePizza(
            pedido_id=nuevo_pedido.id,
            tamano=tamano,
            ingredientes=ingredientes,
            cantidad=cantidad,
            subtotal=subtotal
        )
        db.session.add(detalle)

    db.session.commit()

    # 3) Borramos el archivo temporal
    if os.path.exists(ARCHIVO_TEMP):
        os.remove(ARCHIVO_TEMP)

    # 4) Mensaje flash con el total
    flash(f"Orden finalizado, el cliente debe pagar: ${total_general:.2f}", "success")

    return redirect(url_for("index"))

    """
    Al dar clic en 'Terminar':
      1) Lee las pizzas del archivo temporal
      2) Calcula el total
      3) Inserta un registro en la tabla 'pedidos' + 'detalle_pizzas'
      4) Limpia el archivo temporal
      5) Muestra flash con el total final
    """
    form_pizza = forms.PizzaForm(request.form)

    # Tomar también los datos del cliente (nombre, dirección, teléfono, fecha)
    nombre = request.form.get("nombre")
    direccion = request.form.get("direccion")
    telefono = request.form.get("telefono")
    fecha_pedido = request.form.get("fecha_pedido")

    pizzas_temp = []
    total_general = 0.0

    if os.path.exists(ARCHIVO_TEMP):
        with open(ARCHIVO_TEMP, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) == 4:
                    tamano = parts[0]
                    ingredientes = parts[1]
                    cantidad = int(parts[2])
                    subtotal = float(parts[3])
                    pizzas_temp.append((tamano, ingredientes, cantidad, subtotal))
                    total_general += subtotal

    # 1) Creamos un objeto Pedido
    nuevo_pedido = Pedido(
        nombre=nombre,
        direccion=direccion,
        telefono=telefono
        
    )
    nuevo_pedido.total = total_general
    db.session.add(nuevo_pedido)
    db.session.commit()

    # 2) Insertamos los DetallePizza asociados
    for (tamano, ingredientes, cantidad, subtotal) in pizzas_temp:
        detalle = DetallePizza(
            pedido_id=nuevo_pedido.id,
            tamano=tamano,
            ingredientes=ingredientes,
            cantidad=cantidad,
            subtotal=subtotal
        )
        db.session.add(detalle)

    db.session.commit()

    # 3) Borramos el archivo temporal
    if os.path.exists(ARCHIVO_TEMP):
        os.remove(ARCHIVO_TEMP)

    # 4) Mensaje flash con el total
    flash(f"Pedido finalizado. Total a pagar: ${total_general:.2f}", "success")

    return redirect(url_for("index"))


# ---------------------------
# filtrar ventas por día o mes
# ---------------------------
@app.route("/ventas", methods=["GET", "POST"])
def ventas():
    """
    Muestra ventas del día o del mes, dependiendo de la selección del usuario.
    """
    # Podrías crear un form en forms.py o manejar la lógica aquí directamente
    filtro = request.form.get("filtro_fecha")  # "dia" o "mes"
    fecha = request.form.get("fecha")  # Input type="date"
  
    pedidos_filtrados = []
    total_ventas = 0.0

    if request.method == "POST" and fecha:
        # Convertimos la fecha (yyyy-mm-dd) en un datetime
        import datetime
        fecha_obj = datetime.datetime.strptime(fecha, "%Y-%m-%d")

        if filtro == "dia":
            # Filtrar por año, mes y día
            pedidos_filtrados = Pedido.query.filter(
                db.extract('year', Pedido.fecha_pedido) == fecha_obj.year,
                db.extract('month', Pedido.fecha_pedido) == fecha_obj.month,
                db.extract('day', Pedido.fecha_pedido) == fecha_obj.day
            ).all()
        elif filtro == "mes":
            # Filtrar por año y mes
            pedidos_filtrados = Pedido.query.filter(
                db.extract('year', Pedido.fecha_pedido) == fecha_obj.year,
                db.extract('month', Pedido.fecha_pedido) == fecha_obj.month
            ).all()

    # Calculamos totales
    total_ventas = sum([p.total for p in pedidos_filtrados])

    return render_template("ventas.html",
                           pedidos=pedidos_filtrados,
                           total_ventas=total_ventas)
	
@app.route("/historial", methods=["GET", "POST"])
def historial():
    """
    Muestra un formulario para filtrar las ventas (pedidos) por día o por mes,
    y despliega los resultados en una tabla.
    """
    filtro = request.form.get("filtro_fecha")  # "dia" o "mes"
    fecha = request.form.get("fecha")          # Input type="date"

    pedidos_filtrados = []
    total_ventas = 0.0

    if request.method == "POST" and fecha:
        import datetime
        fecha_obj = datetime.datetime.strptime(fecha, "%Y-%m-%d")

        if filtro == "dia":
            # Filtrar por año, mes y día
            pedidos_filtrados = Pedido.query.filter(
                db.extract('year', Pedido.fecha_pedido) == fecha_obj.year,
                db.extract('month', Pedido.fecha_pedido) == fecha_obj.month,
                db.extract('day', Pedido.fecha_pedido) == fecha_obj.day
            ).all()
        elif filtro == "mes":
            # Filtrar por año y mes
            pedidos_filtrados = Pedido.query.filter(
                db.extract('year', Pedido.fecha_pedido) == fecha_obj.year,
                db.extract('month', Pedido.fecha_pedido) == fecha_obj.month
            ).all()

    # Calculamos el total de las ventas filtradas
    total_ventas = sum([p.total for p in pedidos_filtrados])

    return render_template(
        "index.html", 
        pedidos=pedidos_filtrados, 
        total_ventas=total_ventas,  
    )


if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        
        # Verificar si el usuario ya existe
        existing_user = User.query.filter_by(nombreUsuario='administrador').first()

        if not existing_user:
            # Crear un usuario de prueba con contraseña encriptada
            hashed_password = generate_password_hash('pizzeriaadmin')
            new_user = User(nombreUsuario='administrador', contrasenia=hashed_password, rol='cliente')

            # Añadir el usuario a la base de datos
            db.session.add(new_user)
            db.session.commit()
            print("Usuario de prueba creado.")
        else:
            print("El usuario de prueba ya existe.")
    
    app.run(debug=True)
