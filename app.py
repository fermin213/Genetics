from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://animalesdb_user:z1xIETnjgzHv4GZXEDNQlRC9Cq0tDJfX@dpg-d29unpndiees738f42u0-a.oregon-postgres.render.com/animalesdb_6g2y'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secreto_muy_fuerte'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELOS ---

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    razas = db.relationship('Raza', backref='usuario', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Raza(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    animales = db.relationship('Animal', backref='raza', lazy=True, cascade="all, delete-orphan")
    __table_args__ = (db.UniqueConstraint('nombre', 'user_id', name='uq_raza_nombre_user'),)

class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    raza_id = db.Column(db.Integer, db.ForeignKey('raza.id'), nullable=False)
    rp = db.Column(db.String(50), nullable=True)
    hba = db.Column(db.String(50))
    nombre = db.Column(db.String(100))
    sexo = db.Column(db.String(10))
    fecha_nac = db.Column(db.Date)
    nacimiento = db.Column(db.String(10))
    color = db.Column(db.String(50))
    padre = db.Column(db.String(100))
    madre = db.Column(db.String(100))
    abuelo_paterno = db.Column(db.String(100))
    abuelo_materno = db.Column(db.String(100))
    familia = db.Column(db.String(100))
    f = db.Column(db.String(20))
    tamano = db.Column(db.String(30))
    pezuñas = db.Column(db.Float)
    articulacion = db.Column(db.Float)
    ap_delanteros = db.Column(db.String(50))
    ap_traseros = db.Column(db.String(50))
    curv_garrones = db.Column(db.String(50))
    apert_posterior = db.Column(db.String(50))
    ubres_pezones = db.Column(db.String(50))
    forma_testicular = db.Column(db.String(50))
    desplazamiento = db.Column(db.String(50))
    clase = db.Column(db.Float)
    impresion_general = db.Column(db.String(100))
    musculatura = db.Column(db.String(50))
    anchura = db.Column(db.String(50))
    costilla = db.Column(db.String(50))
    docilidad = db.Column(db.String(50))
    valoracion = db.Column(db.String(50))
    observaciones = db.Column(db.Text)
    premios = db.Column(db.Text)
    epd_nac = db.Column(db.String(50))
    epd_dest = db.Column(db.String(50))
    epd_leche = db.Column(db.String(50))
    epd_18m = db.Column(db.String(50))
    epd_pa_v = db.Column(db.String(50))
    epd_ce = db.Column(db.String(50))
    epd_aob = db.Column(db.String(50))
    epd_egs = db.Column(db.String(50))
    epd_marb = db.Column(db.String(50))
    val_14m = db.Column(db.String(100))
    val_18m = db.Column(db.String(100))
    val_ternero = db.Column(db.String(100))
    val_adulto = db.Column(db.String(100))
    __table_args__ = (db.UniqueConstraint('rp', 'raza_id', name='uq_animal_rp_raza'),)

with app.app_context():
    db.create_all()

# --- CONFIGURACIÓN DE LOGIN Y HELPERS ---

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_form_value(data, key, numeric=False):
    val = (data.get(key, '') or '').strip()
    if not val or val.lower() == 'none': return None
    if numeric:
        try: return float(val.replace(',', '.'))
        except (ValueError, TypeError): return None
    return val

def get_form_date(data, key):
    val = data.get(key, '').strip()
    if not val: return None
    try: return datetime.strptime(val, '%Y-%m-%d').date()
    except ValueError:
        flash(f'Formato de fecha incorrecto para {key}. Use AAAA-MM-DD.', 'danger')
        return None

# --- RUTAS DE USUARIO ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('razas'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Usuario y contraseña requeridos.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe.', 'warning')
            return render_template('register.html')
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('razas'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('razas'))
        else:
            flash('Usuario o contraseña inválidos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('login'))

# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
@login_required
def index():
    return redirect(url_for('razas'))

@app.route('/razas')
@login_required
def razas():
    razas_usuario = Raza.query.filter_by(user_id=current_user.id).order_by(Raza.nombre.asc()).all()
    return render_template('razas.html', razas=razas_usuario)

@app.route('/agregar_raza', methods=['GET', 'POST'])
@login_required
def agregar_raza():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip().capitalize()
        if not nombre:
            flash('El nombre de la raza no puede estar vacío.', 'danger')
            return render_template('agregar_raza.html')
        if Raza.query.filter_by(nombre=nombre, user_id=current_user.id).first():
            flash('Ya tienes una raza con ese nombre.', 'warning')
            return render_template('agregar_raza.html')
        nueva_raza = Raza(nombre=nombre, user_id=current_user.id)
        db.session.add(nueva_raza)
        db.session.commit()
        flash('Raza agregada correctamente.', 'success')
        return redirect(url_for('razas'))
    return render_template('agregar_raza.html')

@app.route('/eliminar_raza/<int:raza_id>', methods=['POST'])
@login_required
def eliminar_raza(raza_id):
    raza = Raza.query.filter_by(id=raza_id, user_id=current_user.id).first_or_404()
    if raza.animales:
        flash('No se puede eliminar una raza con animales registrados.', 'danger')
    else:
        db.session.delete(raza)
        db.session.commit()
        flash('Raza eliminada correctamente.', 'success')
    return redirect(url_for('razas'))

@app.route('/raza/<int:raza_id>')
@login_required
def ver_raza(raza_id):
    raza = Raza.query.filter_by(id=raza_id, user_id=current_user.id).first_or_404()
    
    query = Animal.query.filter_by(raza_id=raza.id)
    filtros = request.args

    for campo in ['rp', 'nombre', 'padre', 'madre']:
        valor = filtros.get(campo, '').strip()
        if valor:
            query = query.filter(getattr(Animal, campo).ilike(f'%{valor}%'))
    
    sexo = filtros.get('sexo', '').strip()
    if sexo:
        query = query.filter(Animal.sexo == sexo)

    for campo in ['pezuñas', 'articulacion', 'valoracion']:
        min_v = filtros.get(f'{campo}_min', '').strip()
        max_v = filtros.get(f'{campo}_max', '').strip()
        if min_v:
            try:
                query = query.filter(getattr(Animal, campo) >= float(min_v.replace(',', '.')))
            except (ValueError, TypeError):
                flash(f'El valor "{min_v}" no es un número válido para {campo} (mínimo).', 'danger')
        if max_v:
            try:
                query = query.filter(getattr(Animal, campo) <= float(max_v.replace(',', '.')))
            except (ValueError, TypeError):
                flash(f'El valor "{max_v}" no es un número válido para {campo} (máximo).', 'danger')

    fecha_min = filtros.get('fecha_nac_min', '').strip()
    fecha_max = filtros.get('fecha_nac_max', '').strip()
    if fecha_min:
        try:
            query = query.filter(Animal.fecha_nac >= datetime.strptime(fecha_min, '%Y-%m-%d').date())
        except (ValueError, TypeError):
            flash(f'El valor "{fecha_min}" no es una fecha válida (mínima).', 'danger')
    if fecha_max:
        try:
            query = query.filter(Animal.fecha_nac <= datetime.strptime(fecha_max, '%Y-%m-%d').date())
        except (ValueError, TypeError):
            flash(f'El valor "{fecha_max}" no es una fecha válida (máxima).', 'danger')

    animales = query.all()
    
    def rp_key(animal):
        if not animal.rp: return (2, "")
        rp_str = str(animal.rp).strip()
        if rp_str.isdigit(): return (0, int(rp_str))
        return (1, rp_str.upper())

    orden = request.args.get('orden', 'asc')
    animales = sorted(animales, key=rp_key, reverse=(orden == 'desc'))

    return render_template('raza.html', raza=raza, animales=animales, total=len(animales), orden=orden)

@app.route('/raza/<int:raza_id>/registrar', methods=['GET', 'POST'])
@login_required
def registrar_animal(raza_id):
    raza = Raza.query.filter_by(id=raza_id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        data = request.form
        rp = get_form_value(data, 'rp')
        if rp and Animal.query.filter_by(rp=rp, raza_id=raza.id).first():
            flash(f'Ya existe un animal con el RP "{rp}" en esta raza.', 'warning')
            return render_template('registrar.html', raza=raza, form_data=data)

        nuevo_animal = Animal(
            raza_id=raza.id, rp=rp, hba=get_form_value(data, 'hba'), nombre=get_form_value(data, 'nombre'),
            sexo=get_form_value(data, 'sexo'), fecha_nac=get_form_date(data, 'fecha_nac'), nacimiento=get_form_value(data, 'nacimiento'),
            color=get_form_value(data, 'color'), padre=get_form_value(data, 'padre'), madre=get_form_value(data, 'madre'),
            abuelo_paterno=get_form_value(data, 'abuelo_paterno'), abuelo_materno=get_form_value(data, 'abuelo_materno'),
            familia=get_form_value(data, 'familia'), f=get_form_value(data, 'f'), tamano=get_form_value(data, 'tamano'),
            pezuñas=get_form_value(data, 'pezuñas', numeric=True), articulacion=get_form_value(data, 'articulacion', numeric=True),
            ap_delanteros=get_form_value(data, 'ap_delanteros'), ap_traseros=get_form_value(data, 'ap_traseros'),
            curv_garrones=get_form_value(data, 'curv_garrones'), apert_posterior=get_form_value(data, 'apert_posterior'),
            ubres_pezones=get_form_value(data, 'ubres_pezones'), forma_testicular=get_form_value(data, 'forma_testicular'),
            desplazamiento=get_form_value(data, 'desplazamiento'), clase=get_form_value(data, 'clase', numeric=True),
            impresion_general=get_form_value(data, 'impresion_general'), musculatura=get_form_value(data, 'musculatura'),
            anchura=get_form_value(data, 'anchura'), costilla=get_form_value(data, 'costilla'), docilidad=get_form_value(data, 'docilidad'),
            valoracion=get_form_value(data, 'valoracion'), observaciones=get_form_value(data, 'observaciones'),
            premios=get_form_value(data, 'premios'), epd_nac=get_form_value(data, 'epd_nac'), epd_dest=get_form_value(data, 'epd_dest'),
            epd_leche=get_form_value(data, 'epd_leche'), epd_18m=get_form_value(data, 'epd_18m'), epd_pa_v=get_form_value(data, 'epd_pa_v'),
            epd_ce=get_form_value(data, 'epd_ce'), epd_aob=get_form_value(data, 'epd_aob'), epd_egs=get_form_value(data, 'epd_egs'),
            epd_marb=get_form_value(data, 'epd_marb'), val_14m=get_form_value(data, 'val_14m'), val_18m=get_form_value(data, 'val_18m'),
            val_ternero=get_form_value(data, 'val_ternero'), val_adulto=get_form_value(data, 'val_adulto')
        )
        db.session.add(nuevo_animal)
        db.session.commit()
        flash('Animal registrado con éxito.', 'success')
        return redirect(url_for('ver_raza', raza_id=raza.id))
    return render_template('registrar.html', raza=raza)

@app.route('/animal/<int:id>')
@login_required
def ficha_animal(id):
    animal = Animal.query.get_or_404(id)
    if animal.raza.user_id != current_user.id:
        flash('No tienes permiso para ver este animal.', 'danger')
        return redirect(url_for('razas'))
    
    hijos = []
    if animal.nombre:
        hijos = Animal.query.filter(
            Animal.raza_id.in_([r.id for r in current_user.razas]),
            (Animal.padre == animal.nombre) | (Animal.madre == animal.nombre)
        ).all()
        
    return render_template('ficha.html', animal=animal, hijos=hijos)

@app.route('/animal/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_animal(id):
    animal = Animal.query.get_or_404(id)
    if animal.raza.user_id != current_user.id:
        flash('No tienes permiso para editar este animal.', 'danger')
        return redirect(url_for('razas'))
    if request.method == 'POST':
        data = request.form
        animal.rp = get_form_value(data, 'rp')
        animal.hba = get_form_value(data, 'hba')
        animal.nombre = get_form_value(data, 'nombre')
        animal.sexo = get_form_value(data, 'sexo')
        animal.fecha_nac = get_form_date(data, 'fecha_nac')
        animal.nacimiento = get_form_value(data, 'nacimiento')
        animal.color = get_form_value(data, 'color')
        animal.padre = get_form_value(data, 'padre')
        animal.madre = get_form_value(data, 'madre')
        animal.abuelo_paterno = get_form_value(data, 'abuelo_paterno')
        animal.abuelo_materno = get_form_value(data, 'abuelo_materno')
        animal.familia = get_form_value(data, 'familia')
        animal.f = get_form_value(data, 'f')
        animal.tamano = get_form_value(data, 'tamano')
        animal.pezuñas = get_form_value(data, 'pezuñas', numeric=True)
        animal.articulacion = get_form_value(data, 'articulacion', numeric=True)
        animal.ap_delanteros = get_form_value(data, 'ap_delanteros')
        animal.ap_traseros = get_form_value(data, 'ap_traseros')
        animal.curv_garrones = get_form_value(data, 'curv_garrones')
        animal.apert_posterior = get_form_value(data, 'apert_posterior')
        animal.ubres_pezones = get_form_value(data, 'ubres_pezones')
        animal.forma_testicular = get_form_value(data, 'forma_testicular')
        animal.desplazamiento = get_form_value(data, 'desplazamiento')
        animal.clase = get_form_value(data, 'clase', numeric=True)
        animal.impresion_general = get_form_value(data, 'impresion_general')
        animal.musculatura = get_form_value(data, 'musculatura')
        animal.anchura = get_form_value(data, 'anchura')
        animal.costilla = get_form_value(data, 'costilla')
        animal.docilidad = get_form_value(data, 'docilidad')
        animal.valoracion = get_form_value(data, 'valoracion')
        animal.observaciones = get_form_value(data, 'observaciones')
        animal.premios = get_form_value(data, 'premios')
        animal.epd_nac = get_form_value(data, 'epd_nac')
        animal.epd_dest = get_form_value(data, 'epd_dest')
        animal.epd_leche = get_form_value(data, 'epd_leche')
        animal.epd_18m = get_form_value(data, 'epd_18m')
        animal.epd_pa_v = get_form_value(data, 'epd_pa_v')
        animal.epd_ce = get_form_value(data, 'epd_ce')
        animal.epd_aob = get_form_value(data, 'epd_aob')
        animal.epd_egs = get_form_value(data, 'epd_egs')
        animal.epd_marb = get_form_value(data, 'epd_marb')
        animal.val_14m = get_form_value(data, 'val_14m')
        animal.val_18m = get_form_value(data, 'val_18m')
        animal.val_ternero = get_form_value(data, 'val_ternero')
        animal.val_adulto = get_form_value(data, 'val_adulto')

        db.session.commit()
        flash('Animal actualizado correctamente.', 'success')
        return redirect(url_for('ficha_animal', id=animal.id))
    return render_template('editar.html', animal=animal)

@app.route('/animal/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_animal(id):
    animal = Animal.query.get_or_404(id)
    if animal.raza.user_id != current_user.id:
        flash('No tienes permiso para eliminar este animal.', 'danger')
        return redirect(url_for('razas'))
    raza_id = animal.raza_id
    db.session.delete(animal)
    db.session.commit()
    flash('Animal eliminado correctamente.', 'success')
    return redirect(url_for('ver_raza', raza_id=raza_id))

@app.route('/raza/<int:raza_id>/actualizar_epds_excel', methods=['POST'])
@login_required
def actualizar_epds_excel(raza_id):
    raza = Raza.query.filter_by(id=raza_id, user_id=current_user.id).first_or_404()

    if 'archivo' not in request.files or request.files['archivo'].filename == '':
        flash('No se seleccionó ningún archivo.', 'danger')
        return redirect(url_for('ver_raza', raza_id=raza_id))

    archivo = request.files['archivo']
    
    # ✅ CORREGIDO: El mapa de columnas ahora coincide con tu archivo Excel.
    COLUMN_MAP = {
        'DEP Peso Nacer': 'epd_nac',
        'DEP Peso Destete': 'epd_dest',
        'DEP Peso 18M': 'epd_18m',
        'DEP Peso Adulto Vaca': 'epd_pa_v',
        'DEP Circ. Escrotal': 'epd_ce',
        'DEP Hab. Materna / Leche': 'epd_leche',
        'DEP AOB': 'epd_aob',
        'DEP EGS / grasa': 'epd_egs',
        'DEP Marbling': 'epd_marb',
    }

    try:
        file_content = archivo.read(); archivo.seek(0)
        df_raw = pd.read_excel(io.BytesIO(file_content), engine='openpyxl', header=None)
        header_row_idx = next((idx for idx, row in df_raw.iterrows() if any(str(cell).strip().upper() == "RP" for cell in row)), None)
        if header_row_idx is None:
            flash('No se encontró la columna "RP" en el archivo Excel.', 'danger')
            return redirect(url_for('ver_raza', raza_id=raza_id))
        df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl', header=header_row_idx)
        if "RP" not in df.columns:
            flash('La fila de encabezado detectada no contiene la columna "RP".', 'danger')
            return redirect(url_for('ver_raza', raza_id=raza_id))
    except Exception as e:
        flash(f'Error al procesar el archivo Excel: {e}', 'danger')
        return redirect(url_for('ver_raza', raza_id=raza_id))

    actualizados, no_encontrados = 0, []

    def clean_rp(val):
        if pd.isnull(val): return ''
        if isinstance(val, (int, float)): return str(int(val))
        return str(val).strip()

    def commit_batch():
        try:
            db.session.commit()
        except OperationalError:
            db.session.rollback()
            db.session.remove()
            db.session.commit()

    try:
        for _, row in df.iterrows():
            rp = clean_rp(row.get('RP'))
            if not rp: continue

            try:
                animal = Animal.query.filter_by(rp=rp, raza_id=raza.id).first()
            except OperationalError:
                db.session.rollback()
                db.session.remove()
                animal = Animal.query.filter_by(rp=rp, raza_id=raza.id).first()

            if animal:
                for excel_col, db_field in COLUMN_MAP.items():
                    if excel_col in row and not pd.isnull(row[excel_col]):
                        setattr(animal, db_field, str(row[excel_col]))
                db.session.add(animal)
                actualizados += 1
                if actualizados % 50 == 0:
                    commit_batch()
            else:
                no_encontrados.append(rp)

        commit_batch()
    except OperationalError as e:
        db.session.rollback()
        flash(f'Error de conexión a la base de datos: {e}', 'danger')
        return redirect(url_for('ver_raza', raza_id=raza_id))

    flash(f'Proceso completado. Se actualizaron {actualizados} animales.', 'success')
    if no_encontrados:
        flash(f'ADVERTENCIA: No se encontraron los siguientes RPs: {", ".join(no_encontrados)}', 'warning')

    return redirect(url_for('ver_raza', raza_id=raza_id))

if __name__ == '__main__':
    app.run(debug=True)


