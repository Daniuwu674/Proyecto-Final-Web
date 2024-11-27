from flask import Flask, render_template, request, redirect, url_for,session, flash, jsonify
from flask_mysqldb import MySQL
import hashlib
from datetime import datetime
import random
from decimal import Decimal 

app = Flask(__name__, template_folder='.', static_folder='static')

# Configuración de la clave secreta para manejar sesiones y flash
app.config['SECRET_KEY'] = 'tu_clave_secreta_unica_y_segura'

# Configuración de MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Leonxd674'
app.config['MYSQL_DB'] = 'tienda'

mysql = MySQL(app)

@app.route('/')
def index():
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM producto")
    productos_raw = cur.fetchall()

    cur.execute("SELECT * FROM categoria")
    categorias_raw = cur.fetchall()
    cur.close()

    productos = []
    for producto in productos_raw:
        productos.append({
            'id': producto[0],
            'nombre': producto[1],
            'descripcion': producto[2],
            'precio': producto[3],
            'imagen': producto[5]
        })
    for producto in productos:
        print(f"URL completa de imagen: {url_for('static', filename='images/' + producto['imagen'], _external=True)}")

    categorias = []
    for categoria in categorias_raw:
        categorias.append({
            'id': categoria[0],
            'nombre': categoria[1],
            'descripcion': categoria[2],
        })
    return render_template('index.html', productos=productos, categorias=categorias)

@app.route('/ofertas')
def ofertas():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_Producto, nombre_producto, descripcion, precio, imagen FROM producto")
    productos = cur.fetchall()

    cantidad_ofertas = min(5, len(productos))
    productos_oferta = random.sample(productos, cantidad_ofertas)

    ofertas = []
    for producto in productos_oferta:
        precio_original = producto[3]
        descuento = Decimal("0.8") 
        precio_oferta = round(precio_original * descuento, 2)

        ofertas.append({
            'id': producto[0],
            'nombre': producto[1],
            'descripcion': producto[2],
            'precio_original': precio_original,
            'precio_oferta': precio_oferta,
            'imagen': producto[4]
        })

    return render_template('ofertas.html', ofertas=ofertas)

@app.route('/hacer-pedido/<int:producto_id>')
def hacer_pedido(producto_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM producto WHERE id_Producto = %s", (producto_id,))
    producto = cur.fetchone()
    cur.close()
    return render_template('hacer_pedido.html', producto=producto)

@app.route('/procesar-pedido', methods=['POST'])
def procesar_pedido():
    if request.method == 'POST':
        producto_id = request.form['producto_id']
        nombre = request.form['nombre']
        email = request.form['email']
        direccion = request.form['direccion']
        cantidad = request.form['cantidad']

        cur = mysql.connection.cursor()
        id_usuario = 1
        fecha_pedido = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("INSERT INTO pedido (id_usuario, fecha_pedido) VALUES (%s, %s)", (id_usuario, fecha_pedido))

        mysql.connection.commit()
        id_pedido = cur.lastrowid

        cur.execute("SELECT precio FROM producto WHERE id_Producto = %s", (producto_id,))
        precio_unitario = cur.fetchone()[0]

        cur.execute("INSERT INTO detalle_pedido(id_pedido, id_producto, cantidad, precio_unitario) VALUES (%s,%s,%s,%s)",
                    (id_pedido, producto_id, cantidad, precio_unitario))
        mysql.connection.commit()
        cur.close()

        return render_template('pedido_exitoso.html')

@app.route('/categoria/<int:categoria_id>')
def productos_por_categoria(categoria_id):
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT p.id_Producto, p.nombre_producto, p.descripcion, p.precio, p.imagen
        FROM producto p
        WHERE p.id_categoria = %s
    """, (categoria_id,))
    productos_raw = cur.fetchall()
    print(productos_raw)

    cur.execute("SELECT * FROM categoria")
    categorias_raw = cur.fetchall()
    cur.close()

    productos = []
    for producto in productos_raw:
        print(productos_raw)
        productos.append({
            'id': producto[0],
            'nombre': producto[1],
            'descripcion': producto[2],
            'precio': producto[3],
            'imagen': producto[4]
        })
    categorias = []
    for categoria in categorias_raw:
        categorias.append({
            'id': categoria[0],
            'nombre': categoria[1],
            'descripcion': categoria[2]
        })
    return render_template('index.html', productos=productos, categorias=categorias, categoria_selecionada=categoria_id)

@app.route('/buscar', methods=['GET'])
def buscar():
    query = request.args.get('q')
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM producto WHERE nombre_producto LIKE %s OR descripcion LIKE %s", ('%' + query + '%', '%' + query + '%'))
    productos_raw = cur.fetchall()
    cur.close()

    productos = []
    for producto in productos_raw:
        productos.append({
            'id': producto[0],
            'nombre': producto[1],
            'descripcion': producto[2],
            'precio': producto[3],
            'imagen': producto[5],
        })

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM categoria")
    categorias_raw = cur.fetchall()
    cur.close()

    categorias = []
    for categoria in categorias_raw:
        categorias.append({
            'id': categoria[0],
            'nombre': categoria[1],
            'descripcion': categoria[2],
        })
    return render_template('index.html', productos=productos, categorias=categorias)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        contraseña = request.form['contraseña']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuario WHERE email = %s", (email,))
        usuario_existente = cur.fetchone()

        if usuario_existente:
            flash("El email ya está registrado, prueba con otro.", "error")
            return redirect(url_for('registro'))

        contraseña_hashed = hashlib.sha256(contraseña.encode()).hexdigest()

        cur.execute("INSERT INTO usuario (nombre, email, contraseña) VALUES (%s, %s, %s)",
                    (nombre, email, contraseña_hashed))
        mysql.connection.commit()
        cur.close()

        flash("Usuario registrado con éxito.", "success")
        return redirect(url_for('index'))

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        contraseña = request.form['contraseña']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuario WHERE email = %s", (email,))
        usuario = cur.fetchone()
        cur.close()

        if usuario and usuario[3] == hashlib.sha256(contraseña.encode()).hexdigest():
            flash(f"¡Bienvenido, {usuario[1]}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Email o contraseña incorrectos.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.before_request
def inicializar_carrito():
    if 'carrito' not in session:
        session['carrito'] = []

@app.route('/agregar-al-carrito/<int:producto_id>', methods=['POST', 'GET'])
def agregar_al_carrito(producto_id):
    cantidad = int(request.form.get('cantidad', 1))
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_Producto, nombre_producto, precio FROM producto WHERE id_Producto = %s", (producto_id,))
    producto = cur.fetchone()
    cur.close()

    if producto:
        carrito = session.get('carrito', [])
        for item in carrito:
            if item['id'] == producto[0]:
                item['cantidad'] += cantidad
                break
        else:
            carrito.append({
                'id': producto[0],
                'nombre': producto[1],
                'precio': producto[2],
                'cantidad': cantidad
            })
        session['carrito'] = carrito
        flash('Producto agregado al carrito.', 'success')
    else:
        flash('Producto no encontrado.', 'error')

    return redirect(url_for('index'))

@app.route('/ver_carrito')
def ver_carrito():
    carrito = session.get('carrito', [])

    for item in carrito:
        item['precio'] = float(item['precio'])  
        item['cantidad'] = int(item['cantidad'])  
    total = sum(item['precio'] * item['cantidad'] for item in carrito)
    
    return render_template('carrito.html', carrito=carrito, total=total)

@app.route('/eliminar-del-carrito/<int:producto_id>', methods=['POST'])
def eliminar_del_carrito(producto_id):
    carrito = session.get('carrito', [])
    carrito = [item for item in carrito if item['id'] != producto_id]
    session['carrito'] = carrito
    flash('Producto eliminado del carrito.', 'success')
    return redirect(url_for('ver_carrito'))

@app.route('/vaciar-carrito')
def vaciar_carrito():
    session['carrito'] = []
    flash('Carrito vaciado', 'info')
    return redirect(url_for('ver_carrito'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
