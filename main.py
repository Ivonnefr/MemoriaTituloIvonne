import datetime
import subprocess
from click import DateTime
from flask import Flask, make_response, render_template, request, url_for, redirect, jsonify, session, flash
from flask_wtf import FlaskForm,CSRFProtect
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required, set_access_cookies
from wtforms import FileField, SubmitField, PasswordField, StringField, DateField, BooleanField, validators
from werkzeug.utils import secure_filename
import os, re
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
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_SECURE'] = True
app.config['JWT_COOKIE_CSRF_PROTECT'] = True
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(minutes=10)
app.config['WTF_CSRF_SECRET_KEY']= 'secret'
app.config['WTF_CSRF_CHECK_DEFAULT']= False
jwt=JWTManager(app)
UPLOAD_FOLDER = 'uploads' #Ruta donde se guardan los archivos subidos para los ejercicios
ALLOWED_EXTENSIONS = {'md'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
csrf = CSRFProtect()
csrf.init_app(app)

# Formularios de Flask-WTF
class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Upload File")


class SerieForm(FlaskForm):
    nombre = StringField('Nombre')
    fecha = DateField('Fecha')
    activa = BooleanField('Activa')
    csrf=False


class LoginForm(FlaskForm):
    correo = StringField('Correo', [validators.DataRequired()])
    password = PasswordField('Contraseña', [validators.DataRequired()])

#Ruta inicio
@app.route('/', methods=['GET'])
def home():
    form = LoginForm()  # Crear una instancia del formulario
    return render_template('inicio.html', form=form)

@app.route('/login', methods=['POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        correo = form.correo.data
        password = form.password.data

    if not correo or not password:
        return jsonify(message='El correo electrónico y la contraseña son requeridos.'), 400

    # Buscar al usuario en la base de datos
    estudiante = Estudiante.query.filter_by(correo=correo).first()
    supervisor = Supervisor.query.filter_by(correo=correo).first()

    # Verificar las credenciales del usuario según su rol
    if estudiante and check_password_hash(estudiante.password, password):
        # Autenticación exitosa para un estudiante: crea el token de acceso con el rol 'estudiante'
        #access_token = create_access_token(identity=estudiante.id, additional_claims={'role': 'estudiante'})
        access_token = create_access_token(identity={'id': estudiante.id, 'role': 'estudiante'})
        # Almacena el token en una cookie segura y luego redirige al usuario a su perfil
        resp = make_response(redirect(url_for('dashEstudiante', estudiante_id=estudiante.id)))
        set_access_cookies(resp, access_token)
        return resp


    elif supervisor and check_password_hash(supervisor.password, password):
        # Autenticación exitosa para un supervisor: crea el token de acceso con el rol 'supervisor'
        access_token = create_access_token(identity={'id': supervisor.id, 'role': 'supervisor'})
        # Almacena el token en una cookie segura y luego redirige al usuario a su perfil
        resp = make_response(redirect(url_for('ver_supervisor', supervisor_id=supervisor.id)))
        set_access_cookies(resp, access_token)
        return resp


    else:
        return jsonify(message='Por favor revise sus datos de acceso e intente de nuevo.'), 401

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

@app.route('/supervisores/<int:supervisor_id>', methods=['GET'])
@csrf.exempt
@jwt_required()  # Protege esta ruta con el decorador jwt_required
def ver_supervisor(supervisor_id):

    # Verificar el rol del usuario
    current_user_role = get_jwt_identity().get('role')

    # Obtener el id del usuario autenticado desde el token
    current_user_id = get_jwt_identity().get('id')

    # Verificar si el usuario autenticado es un supervisor y coincide con el id en la ruta
    if current_user_role == 'supervisor' and current_user_id == supervisor_id:
        
        # Obtiene solo las series activas
        series = Serie.query.filter_by(activa=True).all()
        
        # Crea un diccionario donde las llaves son los id de las series y los valores son listas de ejercicios
        ejercicios_por_serie = {serie.id: [] for serie in series}
        
        # Obtiene todos los ejercicios
        ejercicios = Ejercicio.query.all()
        
        # Agrega los ejercicios a las listas correspondientes en el diccionario
        for ejercicio in ejercicios:
            if ejercicio.id_serie in ejercicios_por_serie:  # Asegúrate de que el ejercicio pertenezca a una serie activa
                ejercicios_por_serie[ejercicio.id_serie].append(ejercicio)

        form = SerieForm()
        return render_template("vistaDocente.html", form=form, series=series, ejercicios_por_serie=ejercicios_por_serie, supervisor_id=supervisor_id)

    else:
        error_message = 'Acceso no autorizado a este supervisor.'
        return render_template('404.html', error_message=error_message)


@app.route('/supervisores/<int:supervisor_id>', methods=['POST'])
@csrf.exempt
@jwt_required()  # Proteger esta ruta con el decorador jwt_required

def procesar_supervisor(supervisor_id):
    # Verificar el rol del usuario
    current_user_role = get_jwt_identity().get('role')

    # Obtener el id del usuario autenticado desde el token
    current_user_id = get_jwt_identity().get('id')

    # Verificar si el usuario autenticado es un supervisor y coincide con el id en la ruta
    if current_user_role == 'supervisor' and current_user_id == supervisor_id:
        
        form = SerieForm()
        if form.validate_on_submit():
            nombre = form.nombre.data
            fecha = form.fecha.data
            activa = form.activa.data
            print(request.form)
            # Crear el nuevo objeto Serie
            nueva_serie = Serie(nombre=nombre, fecha=fecha, activa=activa)

            # Agregar y guardar la nueva Serie en la base de datos
            db.session.add(nueva_serie)
            db.session.commit()
 
            # Redirigir a la vista original o mostrar un mensaje de éxito (depende de tu diseño)
            print(request.form.get('csrf_token'))
            return redirect(url_for('ver_supervisor', supervisor_id=get_jwt_identity(id)))
        else:
            print(form.errors)
    else:
        # Si el acceso no está autorizado, mostrar un mensaje de error en la plantilla
        
        error_message = 'Acceso no autorizado a este supervisor.'
        return render_template('404.html', error_message=error_message)

    
@app.route('/vistaEstudiante/<int:estudiante_id>', methods=['GET'])
@jwt_required()  # Proteger esta ruta con el decorador jwt_required
def dashEstudiante(estudiante_id):
    # Verificar el rol del usuario
    current_user_role = get_jwt_identity().get('role')
    # Obtener el id del usuario autenticado desde el token
    current_user_id = get_jwt_identity().get('id')

    # Verificar si el usuario autenticado es un supervisor y coincide con el id en la ruta
    if current_user_role == 'estudiante' and current_user_id == estudiante_id:
        series = Serie.query.filter_by(activa=True).all()
        ejercicios_por_serie={serie.id: [] for serie in series }
        ejercicios = Ejercicio.query.all()
        for ejercicio in ejercicios:
            if ejercicio.id_serie in ejercicios_por_serie:
                ejercicios_por_serie[ejercicio.id_serie].append(ejercicio)

        return render_template('vistaEstudiante.html')
    else:
        error_message= 'Acceso no autorizado a este estudiante.'
        return render_template('404.html', error_message=error_message)
@app.route('/vistaEstudiante/<int:estudiante_id>', methods=['POST'])
@jwt_required()  # Proteger esta ruta con el decorador jwt_required
def procesar_estudiante(estudiante_id):
    # Verificar el rol del usuario
    current_user_role = get_jwt_identity().get('role')

    # Obtener el id del usuario autenticado desde el token
    current_user_id = get_jwt_identity().get('id')


    # Verificar si el usuario autenticado es un supervisor y coincide con el id en la ruta
    if current_user_role == 'estudiante' and current_user_id == estudiante_id:
        # Aquí puedes procesar los datos enviados en la solicitud POST
        data = request.form.get('data')  # Supongamos que los datos se envían con el campo 'data'
        # Realizar las operaciones necesarias con los datos recibidos...

        # Devolver una respuesta o redireccionar a otra página después de procesar los datos
        return jsonify(message='Datos recibidos y procesados exitosamente.')

    else:
        # Si el acceso no está autorizado, mostrar un mensaje de error en la plantilla
        error_message = 'Acceso no autorizado a este supervisor.'
        return render_template('404.html', error_message=error_message)


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



# Ruta para editar una serie
@app.route('/vistaDocente/editarSerie', methods=['GET', 'POST'])
def editar_serie():
    return render_template('editarSerie.html')




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

# #lsof -i:PUERTO //para revisar todos los procesos que estan usando el puerto
# #kill -9 PID //para matar el proceso que esta usando el puerto
#source /home/ivonne/Documentos/GitHub/MemoriaTituloIvonne/venv/bin/activate


#serie activa por grupos, asignar la serie a un grupo de estudiantes


#Ruta donde debe quedar el archivo del alumno plantillaMaven/src/main/java/org/example/
# Ruta donde debe quedar el archivo de los test del profesor plantillaMaven/src/test/java/org/example/