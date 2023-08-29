import datetime
from click import DateTime
from flask import Flask, make_response, render_template, request, url_for, redirect, jsonify, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from wtforms import FileField, SubmitField, PasswordField, StringField, DateField, BooleanField, validators
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired, Length, ValidationError
from funciones_archivo.compile_java import compilar_archivo_java
from funciones_archivo.run_unit_test import ejecutar_test_unitario
from funciones_archivo.delete_packages import eliminar_packages
from funciones_archivo.copy_maven_folder import agregarCarpetaMavenEstudiante, agregarCarpetaMavenPropuesta
from funciones_archivo.add_java_file import agregar_archivo_java
from funciones_archivo.add_packages import agregar_package
from funciones_archivo.process_surefire_reports import procesar_surefire_reports
from werkzeug.security import check_password_hash, generate_password_hash
from DBManager import db, init_app
from basedatos.modelos import Supervisor, Grupo, Serie, Estudiante, Ejercicio, Test, Supervision, Serie_asignada, Ejercicio_realizado, Comprobacion_ejercicio
from pathlib import Path
import markdown
#inicializar la aplicacion
app = Flask(__name__)
init_app(app)
app.config['SECRET_KEY'] = 'secret-key-goes-here'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Nombre de la vista para iniciar sesión

UPLOAD_FOLDER = 'uploads' #Ruta donde se guardan los archivos subidos para los ejercicios
ALLOWED_EXTENSIONS = {'md'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Se define que tipo de arhivos se pueden recibir
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@login_manager.user_loader
def load_user(user_id):
    user = Estudiante.query.get(int(user_id))
    if user:
        return user
    
    user = Supervisor.query.get(int(user_id))
    if user:
        return user

    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        password = request.form['password']
        
        user = Estudiante.query.filter_by(correo=correo).first() or Supervisor.query.filter_by(correo=correo).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Has iniciado sesión exitosamente', 'success')
            if isinstance(user, Estudiante):
                return redirect(url_for('dashEstudiante', estudiante_id=user.id))
            else:
                return redirect(url_for('dashDocente', supervisor_id=user.id))
        flash('Credenciales inválidas', 'danger')
    
    return render_template('inicio.html')

@app.route('/logout')
def logout():
    logout_user()  # Cierra la sesión del usuario actual.
    return redirect(url_for('login'))  # Redirige al usuario a la página de inicio de sesión.

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('inicio.html')

@app.route('/dashEstudiante/<int:estudiante_id>', methods=['GET, POST'])
@login_required
def dashEstudiante(estudiante_id):
    # Aquí primero aseguramos que el usuario logueado está tratando de acceder a su propio dashboard
    if current_user.id != estudiante_id:
        flash('No tienes permiso para acceder a este dashboard.', 'danger')
        return redirect(url_for('login'))
    return render_template('vistaEstudiante.html')

@app.route('/dashDocente/<int:supervisor_id>', methods=['GET', 'POST'])
@login_required
def dashDocente(supervisor_id):
    print("Dentro de dashDocente")  # Solo para depuración
    # Aquí nos aseguramos que el usuario logueado es un Supervisor
    if not isinstance(current_user, Supervisor):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))

    # Luego, aseguramos que el Supervisor está tratando de acceder a su propio dashboard
    if current_user.id != supervisor_id:
        flash('No tienes permiso para acceder a este dashboard.', 'danger')
        return redirect(url_for('login'))
    
    # Si el método es get: muestra el dashboard del Supervisor
    if request.method == 'GET':
        # Obtiene todas las series
        series = Serie.query.all()
            
        # Crea un diccionario donde las llaves son los id de las series y los valores son listas de ejercicios
        ejercicios_por_serie = {serie.id: [] for serie in series}

        # Obtiene todos los ejercicios
        ejercicios = Ejercicio.query.all()
            
        # Agrega los ejercicios a las listas correspondientes en el diccionario
        for ejercicio in ejercicios:
            if ejercicio.id_serie in ejercicios_por_serie:
                ejercicios_por_serie[ejercicio.id_serie].append(ejercicio)

        return render_template("vistaDocente.html", series=series, ejercicios_por_serie=ejercicios_por_serie)

    # Aquí va el resto de la lógica para mostrar el dashboard del Supervisor, por ejemplo:
    return render_template('vistaDocente.html')

@app.route('/registerSupervisor', methods=['GET'])
def register_page():
    return render_template('register.html')

@app.route('/registersupervisor', methods=['POST'])
def register():
    # Obtén los datos del formulario
    nombre = request.form.get('nombre')
    apellido_paterno = request.form.get('apellido_paterno')
    apellido_materno = request.form.get('apellido_materno')
    correo = request.form.get('correo')
    password = request.form.get('password')

    if not nombre or not apellido_paterno or not apellido_materno or not correo or not password:
        return jsonify(message='Todos los campos son requeridos.'), 400

    # Verifica si ya existe un supervisor con ese correo
    supervisor = Supervisor.query.filter_by(correo=correo).first()
    if supervisor:
        return jsonify(message='Ya existe un supervisor con ese correo.'), 400

    # Crea el nuevo supervisor
    new_supervisor = Supervisor(
        nombre=nombre,
        apellido_paterno=apellido_paterno,
        apellido_materno=apellido_materno,
        correo=correo,
        password=generate_password_hash(password)  # Almacena la contraseña de forma segura
    )

    # Añade el nuevo supervisor a la base de datos
    db.session.add(new_supervisor)
    db.session.commit()

    return jsonify(message='Supervisor registrado exitosamente.'), 201


@app.route('/registerEstudiante', methods=['GET'])
def estudianteRegisterPage():
    return render_template('registerEstudiante.html')

@app.route('/registerEstudiante', methods=['POST'])
def registerEstudiante():
    matricula=request.form.get('matricula')
    nombre=request.form.get('nombre')
    apellido_paterno=request.form.get('apellido_paterno')
    apellido_materno=request.form.get('apellido_materno')
    correo=request.form.get('correo')
    password=request.form.get('password')

    if not nombre or not apellido_paterno or not apellido_materno or not correo or not password or not matricula:
        return jsonify(message='Todos los campos son requeridos.'), 400
        # Verifica si ya existe un estudiante con ese correo
        
    estudiante = Estudiante.query.filter_by(correo=correo).first()
    if estudiante:
        return jsonify(message='Ya existe un estudiante con ese correo.'), 400

    # Crea el nuevo esstudiante
    new_estudiante = Estudiante(
        matricula=matricula,
        nombre=nombre,
        apellido_paterno=apellido_paterno,
        apellido_materno=apellido_materno,
        correo=correo,
        password=generate_password_hash(password)  # Almacena la contraseña de forma segura
    )

    # Añade el nuevo supervisor a la base de datos
    db.session.add(new_estudiante)
    db.session.commit()

    return jsonify(message='Estudiante registrado exitosamente.'), 201

# @app.route('/supervisores/<int:supervisor_id>', methods=['GET'])
# def ver_supervisor(supervisor_id):

#     # Obtiene solo las series activas
#     series = Serie.query.all()
        
#     # Crea un diccionario donde las llaves son los id de las series y los valores son listas de ejercicios
#     ejercicios_por_serie = {serie.id: [] for serie in series}
        
#     # Obtiene todos los ejercicios
#     ejercicios = Ejercicio.query.all()
        
#     # Agrega los ejercicios a las listas correspondientes en el diccionario
#     for ejercicio in ejercicios:
#         if ejercicio.id_serie in ejercicios_por_serie:
#             ejercicios_por_serie[ejercicio.id_serie].append(ejercicio)

#     return render_template("vistaDocente.html", series=series, ejercicios_por_serie=ejercicios_por_serie, supervisor_id=supervisor_id)

# @app.route('/supervisores/<int:supervisor_id>/series/<int:serie_id>/toggle', methods=['POST'])
# @jwt_required()
# def toggle_serie(supervisor_id, serie_id):
#     # Verificar el rol del usuario y obtener ID
#     current_user_role = get_jwt_identity().get('role')
#     current_user_id = get_jwt_identity().get('id')

#     # Verificar si el usuario autenticado es un supervisor y coincide con el id en la ruta
#     if not (current_user_role == 'supervisor' and current_user_id == supervisor_id):
#         return jsonify(message="Acceso no autorizado"), 403

#     # Luego de verificar que es un supervisor, procede con el cambio de estado de la serie
#     serie = Serie.query.get_or_404(serie_id)
#     serie.activa = not serie.activa
#     db.session.commit()

#     flash(f"La serie '{serie.nombre}' ha sido {'activada' if serie.activa else 'desactivada'} con éxito.", 'success')
#     return redirect(url_for('ver_supervisor', supervisor_id=supervisor_id))


# @app.route('/supervisores/<int:supervisor_id>/agregarSerie', methods=['GET', 'POST'])
# @jwt_required()
# def agregarSerie(supervisor_id):
#     # Si es un POST, entonces procesa el formulario
#     if request.method == 'POST':
#         # Recibe del formulario los datos de la serie
#         nombre = request.form.get('nombre')
#         fecha = request.form.get('fecha')
#         activa = request.form.get('activa')

#         # Validación simple para comprobar si los campos no están vacíos
#         if not (nombre and fecha and activa):
#             flash('Por favor, complete todos los campos.', 'danger')
#             return redirect(url_for('agregarSerie', supervisor_id=supervisor_id))

#         # Crea el nuevo objeto Serie
#         nueva_serie = Serie(nombre=nombre, fecha=fecha, activa=activa)
        
#         # Agregar y guardar la nueva Serie en la base de datos
#         db.session.add(nueva_serie)
#         db.session.commit()

#         flash('Serie agregada con éxito.', 'success')
#         # Redirigir a la vista original o mostrar un mensaje de éxito (depende de tu diseño)
#         return redirect(url_for('ver_supervisor', supervisor_id=supervisor_id))
    
#     # Si es un GET, muestra el formulario
#     return render_template('agregarSerie.html', supervisor_id=supervisor_id)



# Ruta para cambiar el estado de una serie
@app.route('/cambiar_estado_serie', methods=['POST'])
def cambiar_estado_serie():
    data = request.get_json()  # Recibe la data de la petición
    serie_id = data['id']
    new_status = data['activa']

    serie = db.session.get(Serie, serie_id)  # Obtiene la serie desde la base de datos

    if serie is None:
        return jsonify({"error": "No se encontró la serie"}), 404

    serie.activa = new_status
    db.session.commit()  # Guarda los cambios en la base de datos

    return jsonify({"message": "Estado actualizado con éxito"}), 200


@app.route('/series_activas', methods=['GET'])
def series_activas():
    series = Serie.query.filter_by(activa=True).all()
    series_activas = [serie.nombre for serie in series]
    return jsonify(series_activas), 200



#Ruta para agregar una serie
@app.route('/vistaDocente/agregarSerie', methods=['GET', 'POST'])
def agregar_serie():
    # Muestra un formulario para agregar una serie
    if request.method == 'POST':
        nombreSerie = request.form.get('nombre')
        fecha_str = request.form.get('fecha')
        # Convertir la fecha a un objeto date
        fecha = datetime.date.fromisoformat(fecha_str)

        # Validar los datos ingresados
        if not nombreSerie or not fecha:
            flash('El nombre de la serie y la fecha de creacion son requeridos.')
            return redirect(url_for('vistaDocente.agregar_serie'))

        # Verificar si el nombre de la serie ya existe en la base de datos
        serie_existente = Serie.query.filter_by(nombre=nombreSerie).first()
        if serie_existente:
            flash('El nombre de la serie ya existe.')
            return redirect(url_for('vistaDocente.agregar_serie'))

        # Crear una nueva instancia de la Serie
        nueva_serie = Serie(nombre=nombreSerie, fecha=fecha)

        # Guardar la nueva serie en la base de datos
        db.session.add(nueva_serie)
        db.session.commit()

        # Crear una nueva carpeta con el nombre `id_serie` en la carpeta `ejerciciosPropuestos`
        nueva_carpeta = Path('ejerciciosPropuestos') / str(nueva_serie.id)
        nueva_carpeta.mkdir(parents=True, exist_ok=True)

        # Redireccionar a '/vistaDocente' después de agregar la serie exitosamente
        return redirect(url_for('rutaDocente'))
    return render_template('agregarSerie.html')


# Ruta para agregar un nuevo ejercicio
@app.route('/vistaDocente/agregarEjercicio', methods=['GET', 'POST'])
def agregar_ejercicio():
    if request.method == 'POST':
        # Obtener los datos del formulario y guardar en la base de datos
        nombre = request.form['nombre']
        path_ejercicio = request.form['path_ejercicio']
        enunciado = request.form['enunciado']
        id_serie = int(request.form['id_serie'])  # Convertir el id de serie a entero
    
        nuevo_ejercicio = Ejercicio(nombre=nombre, path_ejercicio=path_ejercicio, enunciado=enunciado, id_serie=id_serie)

        db.session.add(nuevo_ejercicio)
        db.session.commit()

        # Obtener el ID del ejercicio recién creado
        id_ejercicio = nuevo_ejercicio.id

        # Creamos la carpeta con el id del ejercicio en la serie correspondiente llamando a la funcion agregarCarpetaMavenPropuesta
        ruta_ejercicio=agregarCarpetaMavenPropuesta(id_serie, id_ejercicio)

        # Actualizamos en la base de datos el path del ejercicio
        nuevo_ejercicio.path_ejercicio = ruta_ejercicio
        db.session.commit()

        # Devolver una respuesta JSON indicando que la operación fue exitosa
        return jsonify({'message': 'Ejercicio guardado exitosamente'})

    else:
        # Renderizar la plantilla con la lista de series disponibles
        series_disponibles = Serie.query.all()
        return render_template('agregarEjercicio.html', series=series_disponibles)

# Ruta para mostrar las series que el alumno tiene asignadas
@app.route('/serie/<int:serie_id>')
def mostrar_serie(serie_id):
    serie = Serie.query.get(serie_id)
    
    # Verificar si la serie existe en la base de datos.
    if serie is None:
        return "Serie no encontrada", 404

    # Verificar si la serie está activa.
    if not serie.activa:
        return "Serie no activa", 403

    return render_template('mostrar_serie.html', serie=serie)


#ruta para que el alumno vea los ejercicios que tiene asignados
@app.route('/serie/<int:serie_id>/ejercicio/<int:ejercicio_id>')
def mostrar_ejercicio_serie(serie_id, ejercicio_id):
    ejercicio = Ejercicio.query.filter_by(id=ejercicio_id, id_serie=serie_id).first()
    
    # Verificar si el ejercicio existe en la base de datos.
    if ejercicio is None:
        return "Ejercicio no encontrado en esta serie", 404
    
    return render_template('mostrar_ejercicio.html', ejercicio=ejercicio)


@app.route('/ejercicios', methods=['GET', 'POST'])
def listar_ejercicios():
    # Obtiene todas las series que son activas
    seriesActivas = Serie.query.filter_by(activa=True).all()

    # Crea un diccionario donde las llaves son los id de las series y los valores son listas de ejercicios
    ejercicios_por_serie = {serie.id: [] for serie in seriesActivas}

    # Obtiene todos los ejercicios
    ejercicios = Ejercicio.query.all()

    # Agrega los ejercicios a las listas correspondientes en el diccionario
    for ejercicio in ejercicios:
        if ejercicio.id_serie in ejercicios_por_serie:
            ejercicios_por_serie[ejercicio.id_serie].append(ejercicio)

    # Devuelve la plantilla con el diccionario de ejercicios por serie
    return render_template('listadoEjercicios.html', series=seriesActivas, ejercicios_por_serie=ejercicios_por_serie)

# @app.route('/ejercicio/<int:id>', methods=['GET', 'POST'])
# def show_ejercicio(id):
#     ejercicio = Ejercicio.query.get_or_404(id)
#     with open(ejercicio.path_ejercicio, 'r') as file:
#         content = file.read()
#         enunciado_html = markdown.markdown(content)
#     return render_template('ejercicio.html', enunciado=enunciado_html)


# #Ruta para subir archivo java
# @app.route('/upload_file', methods=['GET',"POST"])
# def upload_file():  
#     form = UploadFileForm()
#     if form.validate_on_submit():
#         file = form.file.data # Obtengo los datos del archivo
        
#         if file and file.filename.endswith('.java'): # Revisa si el archivo tiene la extesion .java
#             filepath= os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))
#             file.save(filepath)
#             print(filepath)
#             #Cuando se sube un archivo se compila y luego se quitan los packages
#             #Revisar que el archivo compile exitosamente
#             eliminar_packages(filepath)
            
#             compilar_archivo_java(filepath)
#             #luego de esto debería redireccionarme a la siguiente página que sería algo como : /upload_file/<nombre_alumno>/<pregunta>
#         else:
#             #Hacer esto en la misma página y no como return
#             return "Tipo de archivo invalido, enviar solo archivos .java ."

#         # file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))) # Then save the file
#         # return "File has been uploaded."
    
#     return render_template('upload_file.html', form=form)




# #Ruta siguiente despues de subir el archivo, donde se muestran los resultados de aplicar los test unitarios
# @app.route('/upload_file/pregunta', methods=["POST"])
# def pregunta():

#     return render_template('pregunta.html')




#Funcion para ejecutar el script 404
def pagina_no_encontrada(error):
    return render_template('404.html'), 404
    #return redirect(url_for('index')) #te devuelve a esa página


#Ruta para ejecutar el script
if __name__ == '__main__':
    app.register_error_handler(404, pagina_no_encontrada)
    app.run(host='0.0.0.0',debug=True, port=3000)
    debug=True

# #lsof -i:PUERTO //para revisar todos los procesos que estan usando el puerto
# #kill -9 PID //para matar el proceso que esta usando el puerto
#source /home/ivonne/Documentos/GitHub/MemoriaTituloIvonne/venv/bin/activate


#serie activa por grupos, asignar la serie a un grupo de estudiantes


#Ruta donde debe quedar el archivo del alumno plantillaMaven/src/main/java/org/example/
# Ruta donde debe quedar el archivo de los test del profesor plantillaMaven/src/test/java/org/example/