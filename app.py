import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import json
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from google_drive_utils import descargar_excel_drive

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///buscador.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de Usuario
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    es_admin = db.Column(db.Boolean, default=False)

# Modelo de Configuración
class Configuracion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    config_json = db.Column(db.Text, nullable=False)

# Decorador para requerir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicie sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorador para requerir admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicie sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        user = Usuario.query.get(session['user_id'])
        if not user or not user.es_admin:
            flash('No tiene permisos para acceder a esta página', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Ruta al archivo Excel
EXCEL_PATH = os.path.join(os.path.dirname(__file__), '../productos_actualizados.xlsx')

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config_financiacion.json')

CARPETA_DRIVE_ID = '16ggHd0Qi32Rlh3tibbKcL-9iJgWsrnsg'
NOMBRE_EXCEL = 'productos_actualizados.xlsx'

def cargar_productos():
    try:
        # Intentar descargar el archivo (solo se descargará si hay una versión más nueva)
        descargar_excel_drive(CARPETA_DRIVE_ID, NOMBRE_EXCEL, NOMBRE_EXCEL)
        
        # Cargar el archivo Excel
        df = pd.read_excel(NOMBRE_EXCEL)
        
        # Verificar que el DataFrame tenga las columnas necesarias
        columnas_requeridas = ['Nombre', 'Categorías', 'Stock', 'Precio costo', 'Precio']
        for col in columnas_requeridas:
            if col not in df.columns:
                raise Exception(f"El archivo Excel no contiene la columna requerida: {col}")
        
        print("Columnas del Excel:", df.columns)
        print("Primeras filas del Excel:\n", df.head())
        print("Cantidad de filas:", len(df))
        return df
    except Exception as e:
        print(f"Error al cargar el archivo: {e}")
        return None

def cargar_configuracion():
    try:
        config = Configuracion.query.first()
        if config:
            return json.loads(config.config_json)
        else:
            # Configuración por defecto
            config_default = {
                "tipos_financiacion": {
                    "MN": {
                        "nombre": "MN",
                        "tarjetas": {
                            "Tarjeta Bancaria": {
                                "planes": [
                                    {"cuotas": "3", "nombre": "", "usar_nombre": False, "interes": 10.24},
                                    {"cuotas": "6", "nombre": "", "usar_nombre": False, "interes": 18.60}
                                ]
                            },
                            "Naranja X": {
                                "planes": [
                                    {"cuotas": "3", "nombre": "Plan Z", "usar_nombre": True, "interes": 12.25},
                                    {"cuotas": "5", "nombre": "", "usar_nombre": False, "interes": 18.67},
                                    {"cuotas": "8", "nombre": "", "usar_nombre": False, "interes": 27.85}
                                ]
                            }
                        }
                    }
                }
            }
            # Guardar configuración por defecto
            nueva_config = Configuracion(config_json=json.dumps(config_default))
            db.session.add(nueva_config)
            db.session.commit()
            return config_default
    except Exception as e:
        print(f"Error al cargar la configuración: {e}")
        return {"tipos_financiacion": {}}

def guardar_configuracion(config):
    try:
        config_obj = Configuracion.query.first()
        if config_obj:
            config_obj.config_json = json.dumps(config)
        else:
            config_obj = Configuracion(config_json=json.dumps(config))
            db.session.add(config_obj)
        db.session.commit()
    except Exception as e:
        print(f"Error al guardar la configuración: {e}")
        db.session.rollback()

@app.route('/')
def index():
    return render_template('index.html', active='buscador')

@app.route('/cotizacion', methods=['GET', 'POST'])
def cotizacion():
    config = cargar_configuracion()
    tipos = list(config["tipos_financiacion"].keys())
    tipo_sel = tipos[0] if tipos else None
    mensaje = ''
    if request.method == 'POST':
        precio = float(request.form.get('precio', 0))
        cantidad = int(request.form.get('cantidad', 1))
        tipo = request.form.get('tipo')
        tipo_sel = tipo
        if not precio or not tipo or tipo not in config["tipos_financiacion"]:
            mensaje = 'Por favor complete todos los campos.'
        else:
            total = precio * cantidad
            mensaje = ''
            tarjetas = list(config["tipos_financiacion"][tipo]["tarjetas"].items())
            for tarjeta, datos in tarjetas:
                mensaje += f'Con {tarjeta}\n'
                planes = datos["planes"]
                for plan in planes:
                    valor_cuota = (total * (1 + plan["interes"] / 100)) / int(plan["cuotas"])
                    if plan.get("usar_nombre", False) and plan.get("nombre"):
                        mensaje += f'{plan["nombre"]} {plan["cuotas"]} cuotas de $' + f'{valor_cuota:,.2f}'.replace(",", ".").replace(".", ",", 1) + '\n'
                    else:
                        mensaje += f'{plan["cuotas"]} cuotas de $' + f'{valor_cuota:,.2f}'.replace(",", ".").replace(".", ",", 1) + '\n'
                mensaje += '\n'
            mensaje = mensaje.strip()
    return render_template('cotizacion.html', tipos=tipos, tipo_sel=tipo_sel, mensaje=mensaje)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Usuario.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('¡Bienvenido!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Sesión cerrada', 'info')
    return redirect(url_for('index'))

@app.route('/configuracion')
@admin_required
def configuracion():
    config = cargar_configuracion()
    tipos = list(config["tipos_financiacion"].keys())
    tipo_sel = tipos[0] if tipos else None
    tarjetas = list(config["tipos_financiacion"][tipo_sel]["tarjetas"].keys()) if tipo_sel else []
    tarjeta_sel = tarjetas[0] if tarjetas else None
    return render_template('configuracion.html', tipos=tipos, tipo_sel=tipo_sel, tarjeta_sel=tarjeta_sel, plan_idx=None, config=config)

@app.route('/configuracion/columna_tipos')
@admin_required
def columna_tipos():
    config = cargar_configuracion()
    tipos = list(config["tipos_financiacion"].keys())
    tipo_sel = request.args.get('tipo')
    if not tipo_sel and tipos:
        tipo_sel = tipos[0]
    return render_template('columna_tipos.html', tipos=tipos, tipo_sel=tipo_sel)

@app.route('/configuracion/columna_tarjetas')
@admin_required
def columna_tarjetas():
    config = cargar_configuracion()
    tipo_sel = request.args.get('tipo')
    if not tipo_sel or tipo_sel not in config["tipos_financiacion"]:
        return '<h5 id="tarjetas-anchor">Tarjetas</h5><div class="text-muted">Seleccione un tipo</div>'
    tarjetas = list(config["tipos_financiacion"][tipo_sel]["tarjetas"].keys())
    tarjeta_sel = request.args.get('tarjeta')
    if not tarjeta_sel and tarjetas:
        tarjeta_sel = tarjetas[0]
    return render_template('columna_tarjetas.html', tipo_sel=tipo_sel, tarjetas=tarjetas, tarjeta_sel=tarjeta_sel)

@app.route('/configuracion/columna_planes')
@admin_required
def columna_planes():
    config = cargar_configuracion()
    tipo_sel = request.args.get('tipo')
    tarjeta_sel = request.args.get('tarjeta')
    plan_idx = request.args.get('plan_idx')
    if not tipo_sel or tipo_sel not in config["tipos_financiacion"]:
        return '<h5 id="planes-anchor">Planes</h5><div class="text-muted">Seleccione un tipo</div>'
    if not tarjeta_sel or tarjeta_sel not in config["tipos_financiacion"][tipo_sel]["tarjetas"]:
        return '<h5 id="planes-anchor">Planes</h5><div class="text-muted">Seleccione una tarjeta</div>'
    planes = config["tipos_financiacion"][tipo_sel]["tarjetas"][tarjeta_sel]["planes"]
    if plan_idx is not None:
        plan_idx = int(plan_idx)
    elif planes:
        plan_idx = 0
    return render_template('columna_planes.html', tipo_sel=tipo_sel, tarjeta_sel=tarjeta_sel, planes=planes, plan_idx=plan_idx)

@app.route('/configuracion/agregar_tipo', methods=['POST'])
@admin_required
def agregar_tipo():
    config = cargar_configuracion()
    nuevo_tipo = request.form.get('nuevo_tipo')
    
    if not nuevo_tipo:
        return jsonify({"success": False, "error": "El nombre es requerido"})
    
    if nuevo_tipo in config["tipos_financiacion"]:
        return jsonify({"success": False, "error": "Este tipo ya existe"})
    
    config["tipos_financiacion"][nuevo_tipo] = {
        "nombre": nuevo_tipo,
        "tarjetas": {}
    }
    guardar_configuracion(config)
    
    tipos = list(config["tipos_financiacion"].keys())
    html = render_template('columna_tipos.html', tipos=tipos)
    return jsonify({"success": True, "html": html})

@app.route('/configuracion/editar_tipo', methods=['POST'])
@admin_required
def editar_tipo():
    config = cargar_configuracion()
    tipo_actual = request.form.get('tipo_actual')
    tipo_nuevo = request.form.get('tipo_nuevo')
    
    if not tipo_actual or not tipo_nuevo:
        return jsonify({"success": False, "error": "Los nombres son requeridos"})
    
    if tipo_nuevo in config["tipos_financiacion"] and tipo_nuevo != tipo_actual:
        return jsonify({"success": False, "error": "Este nombre ya existe"})
    
    if tipo_actual not in config["tipos_financiacion"]:
        return jsonify({"success": False, "error": "Tipo no encontrado"})
    
    datos_actuales = config["tipos_financiacion"][tipo_actual]
    datos_actuales["nombre"] = tipo_nuevo
    config["tipos_financiacion"][tipo_nuevo] = datos_actuales
    del config["tipos_financiacion"][tipo_actual]
    
    guardar_configuracion(config)
    
    tipos = list(config["tipos_financiacion"].keys())
    html = render_template('columna_tipos.html', tipos=tipos)
    return jsonify({"success": True, "html": html})

@app.route('/configuracion/eliminar_tipo', methods=['POST'])
@admin_required
def eliminar_tipo():
    config = cargar_configuracion()
    tipo = request.form.get('tipo')
    
    if not tipo:
        return jsonify({"success": False, "error": "El tipo es requerido"})
    
    if tipo not in config["tipos_financiacion"]:
        return jsonify({"success": False, "error": "Tipo no encontrado"})
    
    if len(config["tipos_financiacion"]) <= 1:
        return jsonify({"success": False, "error": "Debe haber al menos un tipo de financiación"})
    
    del config["tipos_financiacion"][tipo]
    guardar_configuracion(config)
    
    tipos = list(config["tipos_financiacion"].keys())
    html = render_template('columna_tipos.html', tipos=tipos)
    return jsonify({"success": True, "html": html})

@app.route('/configuracion/agregar_tarjeta', methods=['POST'])
@admin_required
def agregar_tarjeta():
    config = cargar_configuracion()
    tipo = request.form.get('tipo')
    nueva_tarjeta = request.form.get('nueva_tarjeta')
    
    if not tipo or not nueva_tarjeta:
        return jsonify({"success": False, "error": "Los campos son requeridos"})
    
    if tipo not in config["tipos_financiacion"]:
        return jsonify({"success": False, "error": "Tipo no encontrado"})
    
    if nueva_tarjeta in config["tipos_financiacion"][tipo]["tarjetas"]:
        return jsonify({"success": False, "error": "Esta tarjeta ya existe"})
    
    config["tipos_financiacion"][tipo]["tarjetas"][nueva_tarjeta] = {
        "planes": []
    }
    guardar_configuracion(config)
    
    tarjetas = list(config["tipos_financiacion"][tipo]["tarjetas"].keys())
    html = render_template('columna_tarjetas.html', tipo_sel=tipo, tarjetas=tarjetas)
    return jsonify({"success": True, "html": html})

@app.route('/configuracion/editar_tarjeta', methods=['POST'])
@admin_required
def editar_tarjeta():
    config = cargar_configuracion()
    tipo = request.form.get('tipo')
    tarjeta_actual = request.form.get('tarjeta_actual')
    tarjeta_nueva = request.form.get('tarjeta_nueva')
    
    if not tipo or not tarjeta_actual or not tarjeta_nueva:
        return jsonify({"success": False, "error": "Los campos son requeridos"})
    
    if tipo not in config["tipos_financiacion"]:
        return jsonify({"success": False, "error": "Tipo no encontrado"})
    
    if tarjeta_nueva in config["tipos_financiacion"][tipo]["tarjetas"] and tarjeta_nueva != tarjeta_actual:
        return jsonify({"success": False, "error": "Este nombre ya existe"})
    
    if tarjeta_actual not in config["tipos_financiacion"][tipo]["tarjetas"]:
        return jsonify({"success": False, "error": "Tarjeta no encontrada"})
    
    config["tipos_financiacion"][tipo]["tarjetas"][tarjeta_nueva] = \
        config["tipos_financiacion"][tipo]["tarjetas"].pop(tarjeta_actual)
    
    guardar_configuracion(config)
    
    tarjetas = list(config["tipos_financiacion"][tipo]["tarjetas"].keys())
    html = render_template('columna_tarjetas.html', tipo_sel=tipo, tarjetas=tarjetas)
    return jsonify({"success": True, "html": html})

@app.route('/configuracion/eliminar_tarjeta', methods=['POST'])
@admin_required
def eliminar_tarjeta():
    config = cargar_configuracion()
    tipo = request.form.get('tipo')
    tarjeta = request.form.get('tarjeta')
    
    if not tipo or not tarjeta:
        return jsonify({"success": False, "error": "Los campos son requeridos"})
    
    if tipo not in config["tipos_financiacion"]:
        return jsonify({"success": False, "error": "Tipo no encontrado"})
    
    if tarjeta not in config["tipos_financiacion"][tipo]["tarjetas"]:
        return jsonify({"success": False, "error": "Tarjeta no encontrada"})
    
    if len(config["tipos_financiacion"][tipo]["tarjetas"]) <= 1:
        return jsonify({"success": False, "error": "Debe haber al menos una tarjeta"})
    
    del config["tipos_financiacion"][tipo]["tarjetas"][tarjeta]
    guardar_configuracion(config)
    
    tarjetas = list(config["tipos_financiacion"][tipo]["tarjetas"].keys())
    html = render_template('columna_tarjetas.html', tipo_sel=tipo, tarjetas=tarjetas)
    return jsonify({"success": True, "html": html})

@app.route('/configuracion/agregar_plan', methods=['POST'])
@admin_required
def agregar_plan():
    config = cargar_configuracion()
    tipo = request.form.get('tipo')
    tarjeta = request.form.get('tarjeta')
    nombre = request.form.get('nombre', '')
    cuotas = request.form.get('cuotas')
    interes = request.form.get('interes')
    usar_nombre = request.form.get('usar_nombre') == '1'
    
    if not tipo or not tarjeta or not cuotas or not interes:
        return jsonify({"success": False, "error": "Los campos son requeridos"})
    
    if tipo not in config["tipos_financiacion"]:
        return jsonify({"success": False, "error": "Tipo no encontrado"})
    
    if tarjeta not in config["tipos_financiacion"][tipo]["tarjetas"]:
        return jsonify({"success": False, "error": "Tarjeta no encontrada"})
    
    try:
        cuotas = int(cuotas)
        interes = float(interes)
    except ValueError:
        return jsonify({"success": False, "error": "Valores inválidos"})
    
    planes = config["tipos_financiacion"][tipo]["tarjetas"][tarjeta]["planes"]
    planes.append({
        "cuotas": str(cuotas),
        "nombre": nombre,
        "usar_nombre": usar_nombre,
        "interes": interes
    })
    guardar_configuracion(config)
    nuevo_idx = len(planes) - 1
    html = render_template('columna_planes.html', tipo_sel=tipo, tarjeta_sel=tarjeta, planes=planes, plan_idx=nuevo_idx)
    return jsonify({"success": True, "html": html, "plan_idx": nuevo_idx})

@app.route('/configuracion/editar_plan', methods=['POST'])
@admin_required
def editar_plan():
    config = cargar_configuracion()
    tipo = request.form.get('tipo')
    tarjeta = request.form.get('tarjeta')
    plan_idx = request.form.get('plan_idx')
    nombre = request.form.get('nombre', '')
    cuotas = request.form.get('cuotas')
    interes = request.form.get('interes')
    usar_nombre = request.form.get('usar_nombre') == '1'
    
    if not tipo or not tarjeta or not plan_idx or not cuotas or not interes:
        return jsonify({"success": False, "error": "Los campos son requeridos"})
    
    if tipo not in config["tipos_financiacion"]:
        return jsonify({"success": False, "error": "Tipo no encontrado"})
    
    if tarjeta not in config["tipos_financiacion"][tipo]["tarjetas"]:
        return jsonify({"success": False, "error": "Tarjeta no encontrada"})
    
    try:
        plan_idx = int(plan_idx)
        cuotas = int(cuotas)
        interes = float(interes)
    except ValueError:
        return jsonify({"success": False, "error": "Valores inválidos"})
    
    planes = config["tipos_financiacion"][tipo]["tarjetas"][tarjeta]["planes"]
    if plan_idx < 0 or plan_idx >= len(planes):
        return jsonify({"success": False, "error": "Plan no encontrado"})
    
    planes[plan_idx] = {
        "cuotas": str(cuotas),
        "nombre": nombre,
        "usar_nombre": usar_nombre,
        "interes": interes
    }
    guardar_configuracion(config)
    html = render_template('columna_planes.html', tipo_sel=tipo, tarjeta_sel=tarjeta, planes=planes, plan_idx=plan_idx)
    return jsonify({"success": True, "html": html, "plan_idx": plan_idx})

@app.route('/configuracion/eliminar_plan', methods=['POST'])
@admin_required
def eliminar_plan():
    config = cargar_configuracion()
    tipo = request.form.get('tipo')
    tarjeta = request.form.get('tarjeta')
    plan_idx = request.form.get('plan_idx')
    
    if not tipo or not tarjeta or not plan_idx:
        return jsonify({"success": False, "error": "Los campos son requeridos"})
    
    if tipo not in config["tipos_financiacion"]:
        return jsonify({"success": False, "error": "Tipo no encontrado"})
    
    if tarjeta not in config["tipos_financiacion"][tipo]["tarjetas"]:
        return jsonify({"success": False, "error": "Tarjeta no encontrada"})
    
    try:
        plan_idx = int(plan_idx)
    except ValueError:
        return jsonify({"success": False, "error": "Valor inválido"})
    
    planes = config["tipos_financiacion"][tipo]["tarjetas"][tarjeta]["planes"]
    if plan_idx < 0 or plan_idx >= len(planes):
        return jsonify({"success": False, "error": "Plan no encontrado"})
    
    del planes[plan_idx]
    guardar_configuracion(config)
    # Seleccionar el anterior, o el primero si era el primero, o ninguno si no quedan
    nuevo_idx = plan_idx
    if nuevo_idx >= len(planes):
        nuevo_idx = len(planes) - 1
    if len(planes) == 0:
        nuevo_idx = None
    html = render_template('columna_planes.html', tipo_sel=tipo, tarjeta_sel=tarjeta, planes=planes, plan_idx=nuevo_idx)
    return jsonify({"success": True, "html": html, "plan_idx": nuevo_idx})

@app.route('/configuracion/mover_tipo', methods=['POST'])
@admin_required
def mover_tipo():
    config = cargar_configuracion()
    tipo = request.form.get('tipo')
    direccion = int(request.form.get('direccion', 0))
    tipos = list(config["tipos_financiacion"].keys())
    if tipo not in tipos:
        return jsonify({"success": False, "error": "Tipo no encontrado"})
    idx = tipos.index(tipo)
    nuevo_idx = idx + direccion
    if nuevo_idx < 0 or nuevo_idx >= len(tipos):
        return jsonify({"success": False, "error": "Movimiento fuera de rango"})
    # Reordenar
    tipos.insert(nuevo_idx, tipos.pop(idx))
    # Reconstruir el diccionario en el nuevo orden
    config["tipos_financiacion"] = {k: config["tipos_financiacion"][k] for k in tipos}
    guardar_configuracion(config)
    html = render_template('columna_tipos.html', tipos=tipos, tipo_sel=tipo)
    return jsonify({"success": True, "html": html})

@app.route('/configuracion/mover_tarjeta', methods=['POST'])
@admin_required
def mover_tarjeta():
    config = cargar_configuracion()
    tipo = request.form.get('tipo')
    tarjeta = request.form.get('tarjeta')
    direccion = int(request.form.get('direccion', 0))
    if tipo not in config["tipos_financiacion"]:
        return jsonify({"success": False, "error": "Tipo no encontrado"})
    tarjetas = list(config["tipos_financiacion"][tipo]["tarjetas"].keys())
    if tarjeta not in tarjetas:
        return jsonify({"success": False, "error": "Tarjeta no encontrada"})
    idx = tarjetas.index(tarjeta)
    nuevo_idx = idx + direccion
    if nuevo_idx < 0 or nuevo_idx >= len(tarjetas):
        return jsonify({"success": False, "error": "Movimiento fuera de rango"})
    # Reordenar
    tarjetas.insert(nuevo_idx, tarjetas.pop(idx))
    # Reconstruir el diccionario en el nuevo orden
    config["tipos_financiacion"][tipo]["tarjetas"] = {k: config["tipos_financiacion"][tipo]["tarjetas"][k] for k in tarjetas}
    guardar_configuracion(config)
    html = render_template('columna_tarjetas.html', tipo_sel=tipo, tarjetas=tarjetas, tarjeta_sel=tarjeta)
    return jsonify({"success": True, "html": html})

@app.route('/configuracion/mover_plan', methods=['POST'])
@admin_required
def mover_plan():
    config = cargar_configuracion()
    tipo = request.form.get('tipo')
    tarjeta = request.form.get('tarjeta')
    plan_idx = int(request.form.get('plan_idx', 0))
    direccion = int(request.form.get('direccion', 0))
    if tipo not in config["tipos_financiacion"]:
        return jsonify({"success": False, "error": "Tipo no encontrado"})
    if tarjeta not in config["tipos_financiacion"][tipo]["tarjetas"]:
        return jsonify({"success": False, "error": "Tarjeta no encontrada"})
    planes = config["tipos_financiacion"][tipo]["tarjetas"][tarjeta]["planes"]
    nuevo_idx = plan_idx + direccion
    if nuevo_idx < 0 or nuevo_idx >= len(planes):
        return jsonify({"success": False, "error": "Movimiento fuera de rango"})
    # Reordenar
    planes.insert(nuevo_idx, planes.pop(plan_idx))
    guardar_configuracion(config)
    html = render_template('columna_planes.html', tipo_sel=tipo, tarjeta_sel=tarjeta, planes=planes, plan_idx=nuevo_idx)
    return jsonify({"success": True, "html": html})

@app.route('/buscar', methods=['POST'])
def buscar():
    medida = request.form.get('medida', '').strip()
    if not medida:
        flash('Por favor ingrese una medida', 'warning')
        return redirect(url_for('index'))
    df = cargar_productos()
    if df is None:
        flash('No se pudo cargar el archivo de productos', 'danger')
        return redirect(url_for('index'))
    medida = medida.upper()
    patrones = [
        medida.replace('/', '').replace(' ', ''),
        medida.replace('/', '-'),
        medida
    ]
    resultados = pd.DataFrame()
    for patron in patrones:
        mask_nombre = df['Nombre'].str.contains(patron, case=False, na=False)
        mask_categoria = df['Categorías'].str.contains(patron, case=False, na=False)
        resultados = pd.concat([resultados, df[mask_nombre | mask_categoria]])
    resultados = resultados.drop_duplicates()
    resultados = resultados[resultados['Stock'] > 0]
    resultados['Precio costo'] = pd.to_numeric(resultados['Precio costo'], errors='coerce')
    resultados = resultados[(resultados['Precio costo'].notna()) & (resultados['Precio costo'] > 0)]
    resultados = resultados.sort_values('Precio')
    
    # Limpiar los nombres de productos
    def limpiar_nombre(nombre, medida):
        print(f"\nProcesando nombre: {nombre}")
        print(f"Medida a buscar: {medida}")
        print(f"¿Es medida de carga?: {medida.endswith('C')}")
        
        # Si la medida es de carga (termina en C), no la limpiamos
        if medida.endswith('C'):
            print("Es medida de carga, manteniendo nombre original")
            return nombre
            
        # Crear variantes de la medida para buscar
        variantes = [
            medida,
            medida.replace(' ', ''),
            medida.replace(' ', '-'),
            medida.replace('/', ''),
            medida.replace('/', '-'),
            # Agregar variantes con ZR
            medida.replace('R', 'ZR'),
            medida.replace('R', ' ZR'),
            medida.replace('R', '-ZR'),
        ]
        
        print(f"Variantes a buscar: {variantes}")
        
        # Eliminar la medida y sus variantes del nombre
        nombre_limpio = nombre
        for variante in variantes:
            # No eliminar si es una medida de carga
            if not variante.endswith('C'):
                nombre_limpio = nombre_limpio.replace(variante, '')
                print(f"Reemplazando variante: {variante}")
                print(f"Nombre después de reemplazo: {nombre_limpio}")
        
        # Limpiar espacios y guiones extra
        nombre_limpio = ' '.join(nombre_limpio.split())
        nombre_limpio = nombre_limpio.strip('- ')
        
        print(f"Nombre final: {nombre_limpio}")
        return nombre_limpio
    
    # Aplicar la limpieza a los nombres
    resultados['Nombre'] = resultados['Nombre'].apply(lambda x: limpiar_nombre(x, medida))
    
    productos = resultados[['Nombre', 'Precio']].to_dict(orient='records')
    
    # Generar mensaje con el mismo formato que la app de escritorio
    if productos:
        mensaje = f"En {medida} tenemos en promoción lo que es:\n"
        for p in productos:
            mensaje += f"{p['Nombre']} en ${p['Precio']:.0f}\n"
    else:
        mensaje = "No se encontraron productos para esa medida."
    return render_template('index.html', medida=medida, productos=productos, mensaje=mensaje)

if __name__ == '__main__':
    from werkzeug.security import generate_password_hash
    with app.app_context():
        db.create_all()
        # Crear usuario admin si no existe
        if not Usuario.query.filter_by(username='admin').first():
            admin = Usuario(
                username='admin',
                password_hash=generate_password_hash('admin123'),  # Cambia esto en producción
                es_admin=True
            )
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True) 