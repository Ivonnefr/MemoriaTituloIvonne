import datetime
import os
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
from funciones_archivo.copy_maven_folder import agregarCarpetaMavenEstudiante, crear_carpeta_serie, crear_carpeta_ejercicio
from funciones_archivo.add_java_file import agregar_archivo_java
from funciones_archivo.add_packages import agregar_package
from funciones_archivo.process_surefire_reports import procesar_surefire_reports
from werkzeug.security import check_password_hash, generate_password_hash
from DBManager import db, init_app
from basedatos.modelos import Supervisor, Grupo, Serie, Estudiante, Ejercicio, Test, Supervision, Serie_asignada, Ejercicio_realizado, Curso, Envio
from pathlib import Path
import markdown
import csv
#inicializar la aplicacion
app = Flask(__name__)
init_app(app)
app.config['SECRET_KEY'] = 'secret-key-goes-here'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Nombre de la vista para iniciar sesión

UPLOAD_FOLDER = 'uploads' #Ruta donde se guardan los archivos subidos para los ejercicios
ALLOWED_EXTENSIONS = {'md','xml','csv'}

# Encuentra la ruta del directorio del archivo actual
current_directory = os.path.dirname(os.path.abspath(__file__))

# Define la ruta UPLOAD_FOLDER en relación a ese directorio
UPLOAD_FOLDER = os.path.join(current_directory, "uploads")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Se define que tipo de arhivos se pueden recibir
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def procesar_archivo_csv(filename, curso_id):
    estudiantes_repetidos = []  # Lista para almacenar estudiantes repetidos

    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Saltar la primera fila
        for row in reader:
            matricula, nombres, apellidos, correo, carrera = row
            password = generate_password_hash(matricula)  # Contraseña por defecto

            estudiante = Estudiante(
                matricula=matricula,
                nombres=nombres,
                apellidos=apellidos,
                correo=correo,
                password=password,
                carrera=carrera
            )

            # Verificar si el correo o matrícula ya existen en la base de datos
            estudiante_existente = Estudiante.query.filter_by(correo=correo).first()
            if estudiante_existente:
                # El estudiante con el mismo correo ya existe
                flash(f'El estudiante con correo {correo} ya está registrado en la base de datos.', 'warning')
                estudiantes_repetidos.append(estudiante)  # Agregar a la lista de repetidos
            else:
                # Añade el nuevo estudiante a la base de datos
                db.session.add(estudiante)

        try:
            db.session.commit()
        except Exception as e:
            flash('Error al guardar en la bd', 'danger')
            db.session.rollback()

    if estudiantes_repetidos:
        # Si hay estudiantes repetidos, puedes manejarlos de acuerdo a tus necesidades
        # Por ejemplo, puedes crear un archivo CSV con los estudiantes repetidos
        # y guardarlos en algún lugar para su revisión
        archivo_repetidos = 'estudiantes_repetidos.csv'  # Nombre del archivo
        ruta_archivo_repetidos = os.path.join(app.config['UPLOAD_FOLDER'], archivo_repetidos)

    with open(ruta_archivo_repetidos, 'w', newline='') as csvfile:
        fieldnames = ['Matrícula', 'Nombres', 'Apellidos', 'Correo', 'Carrera']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for est in estudiantes_repetidos:
            writer.writerow({
                'Matrícula': est.matricula,
                'Nombres': est.nombres,
                'Apellidos': est.apellidos,
                'Correo': est.correo,
                'Carrera': est.carrera
            })

    #flash(f'Se han encontrado estudiantes repetidos. Consulta el archivo {archivo_repetidos} para más detalles.', 'warning')
    #Falta crear el hipervinculo para abrir el archivo.
@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith("e"):
        user = db.session.get(Estudiante, int(user_id[1:]))
    elif user_id.startswith("s"):
        user = db.session.get(Supervisor, int(user_id[1:]))
    else:
        return None

    return user

# Verifica que el usuario logueado es un Supervisor
def verify_supervisor(supervisor_id):
    
    if not isinstance(current_user, Supervisor):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return False

    # Asegura que el Supervisor está tratando de acceder a su propio dashboard
    if current_user.id != supervisor_id:
        flash('No tienes permiso para acceder a este dashboard.', 'danger')
        return False

    return True

# Verifica que el usuario logueado es un Estudiante
def verify_estudiante(estudiante_id):
    
    if not isinstance(current_user, Estudiante):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Estudiante.', 'danger')
        return False
    # Asegura que el Estudiante está tratando de acceder a su propio dashboard
    if current_user.id != estudiante_id:
        flash('No tienes permiso para acceder a este dashboard.', 'danger')
        return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        password = request.form['password']
        
        # Primero verifica si las credenciales son de un estudiante o un supervisor.
        estudiante = Estudiante.query.filter_by(correo=correo).first()
        supervisor = Supervisor.query.filter_by(correo=correo).first()

        # Si es estudiante y las credenciales son correctas.
        if estudiante and check_password_hash(estudiante.password, password):
            login_user(estudiante)
            flash('Has iniciado sesión exitosamente', 'success')
            return redirect(url_for('dashEstudiante', estudiante_id=estudiante.id))
        
        # Si es supervisor y las credenciales son correctas.
        elif supervisor and check_password_hash(supervisor.password, password):
            login_user(supervisor)
            flash('Has iniciado sesión exitosamente', 'success')
            return redirect(url_for('dashDocente', supervisor_id=supervisor.id))
        
        # Si las credenciales no coinciden con ningún usuario.
        flash('Credenciales inválidas', 'danger')
    
    return render_template('inicio.html')

@app.route('/logout')
def logout():
    logout_user()  # Cierra la sesión del usuario actual.
    return redirect(url_for('login'))  # Redirige al usuario a la página de inicio de sesión.

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('inicio.html')

@app.route('/registerSupervisor', methods=['GET'])
def register_page():
    return render_template('register.html')

@app.route('/registersupervisor', methods=['POST'])
def register():

    # Obtén los datos del formulario
    nombres= request.form.get('nombres')
    apellidos = request.form.get('apellidos')
    correo = request.form.get('correo')
    password = request.form.get('password')

    if not nombres or not apellidos or not correo or not password:
        flash('Todos los campos son requeridos.', 'danger')
        return render_template('registersupervisor.html')  # Asume que así se llama tu plantilla

    # Verifica si ya existe un supervisor con ese correo
    supervisor = Supervisor.query.filter_by(correo=correo).first()
    if supervisor:
        flash('Ya existe un supervisor con ese correo.', 'warning')
        return render_template('registersupervisor.html')  # Asume que así se llama tu plantilla

    # Crea el nuevo supervisor
    new_supervisor = Supervisor(
        nombres=nombres,
        apellidos=apellidos,
        correo=correo,
        password=generate_password_hash(password)  # Almacena la contraseña de forma segura
    )

    # Añade el nuevo supervisor a la base de datos
    db.session.add(new_supervisor)
    db.session.commit()

    flash('Supervisor registrado exitosamente.', 'success')
    return redirect(url_for('home'))  # Asumiendo que 'home' es la función que maneja tu página de inicio.

@app.route('/dashDocente/<int:supervisor_id>', methods=['GET', 'POST'])
@login_required
def dashDocente(supervisor_id):
    # Usa la función de verificación
    if not verify_supervisor(supervisor_id):
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

        return render_template("vistaDocente.html", supervisor_id=supervisor_id, series=series, ejercicios_por_serie=ejercicios_por_serie)

    # Aquí va el resto de la lógica para mostrar el dashboard del Supervisor, por ejemplo:
    return render_template('vistaDocente.html')


@app.route('/dashDocente/<int:supervisor_id>/agregarSerie', methods=['GET', 'POST'])
@login_required
def agregarSerie(supervisor_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('login'))

    if request.method == 'POST':
        nombreSerie= request.form.get('nombreSerie')
        activa_value = True if request.form.get('activa') == "true" else False

        if not (nombreSerie):
            flash('Por favor, complete todos los campos.', 'danger')
            return redirect(url_for('agregarSerie', supervisor_id=supervisor_id))
        
        nueva_serie = Serie(nombre=nombreSerie, activa=activa_value)
        db.session.add(nueva_serie)
        db.session.commit()  # Primero confirmamos en la base de datos para obtener el ID
        
        try:
            # Intentar crear carpeta de la serie con el ID y el nombre
            crear_carpeta_serie(nueva_serie.id, nueva_serie.nombre)
            flash('Serie agregada con éxito', 'success')
            return redirect(url_for('dashDocente', supervisor_id=supervisor_id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar la serie: {str(e)}', 'danger')
            return render_template('agregarSerie.html', supervisor_id=supervisor_id)
    
    return render_template('agregarSerie.html', supervisor_id=supervisor_id)

@app.route('/dashDocente/<int:supervisor_id>/agregarEjercicio', methods = ['GET', 'POST'])
def agregarEjercicio(supervisor_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('login'))

    series = Serie.query.all()

    if request.method == 'POST':
        nombreEjercicio = request.form.get('nombreEjercicio')
        id_serie = request.form.get('id_serie')
        serie_actual = db.session.get(Serie, int(id_serie))
        enunciadoFile = request.files.get('enunciadoFile')

        if not enunciadoFile:
            flash('Por favor, carga un archivo .md.', 'danger')
            return render_template('agregarEjercicio.html', supervisor_id=supervisor_id, series=series)

        filename = secure_filename(enunciadoFile.filename)

        nuevo_ejercicio = Ejercicio(nombre=nombreEjercicio, path_ejercicio="", enunciado=filename, id_serie=id_serie)

        try:
            db.session.add(nuevo_ejercicio)
            db.session.flush()  # Esto genera el id sin confirmar en la base de datos

            ruta_ejercicio, mensaje = crear_carpeta_ejercicio(id_serie, serie_actual.nombre, nuevo_ejercicio.id)

            if ruta_ejercicio is None:
                raise Exception(mensaje)
            
            filepath_ejercicio = os.path.join(ruta_ejercicio, filename)
            
            enunciadoFile.save(filepath_ejercicio)
            
            nuevo_ejercicio.path_ejercicio = filepath_ejercicio
            db.session.commit()

        except Exception as e:
            db.session.rollback()

            if 'filepath_ejercicio' in locals() and os.path.exists(filepath_ejercicio):
                os.remove(filepath_ejercicio)
            
            flash(f'Ocurrió un error al agregar el ejercicio: {str(e)}', 'danger')
            return render_template('agregarEjercicio.html', supervisor_id=supervisor_id, series=series)

        flash('Ejercicio agregado con éxito', 'success')
        return redirect(url_for('dashDocente', supervisor_id=supervisor_id))

    return render_template('agregarEjercicio.html', supervisor_id=supervisor_id, series=series)


@app.route('/dashDocente/<int:supervisor_id>/serie/<int:id>')
@login_required
def detallesSeries(supervisor_id, id):
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))
    serie = Serie.query.get(id)
    ejercicios = Ejercicio.query.filter_by(id_serie=id).all()
    return render_template('detallesSerie.html', serie=serie, ejercicios=ejercicios, supervisor_id=supervisor_id)


@app.route('/dashDocente/<int:supervisor_id>/ejercicio/<int:id>')
@login_required
def detallesEjercicio(supervisor_id, id):
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))
    ejercicio = Ejercicio.query.get(id)
    return render_template('detallesEjercicios.html', ejercicio=ejercicio, supervisor_id=supervisor_id)


@app.route('/dashDocente/<int:supervisor_id>/registrarEstudiante', methods=['GET', 'POST'])
@login_required
def registrarEstudiantes(supervisor_id):
    # Ruta para recibir un archivo csv con los datos de los estudiantes y registrarlos en la base de datos
    # Usa la función de verificación
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))

    cursos = Curso.query.all()

    if request.method == 'GET':
        cursos = Curso.query.all()
        return render_template('registrarEstudiantes.html', supervisor_id=supervisor_id, cursos=cursos)
    
    if request.method == 'POST':
        accion= request.form['accion']
        
        if accion == 'crearCurso':
            #Procesar el formulario y agregarlo a la base de datos
            nombre_curso= request.form['nombreCurso']
            nuevo_curso= Curso(
                nombre=nombre_curso
            )
            db.session.add(nuevo_curso)
            db.session.commit()
            flash('Has creado exitosamente un nuevo Curso', 'success')
            return redirect(url_for('registrarEstudiantes', supervisor_id=supervisor_id))
        
        elif accion == 'registrarEstudiantes':
            
            id_curso=request.form['curso']
            listaClases = request.files['listaClases']
            if listaClases and allowed_file(listaClases.filename, ALLOWED_EXTENSIONS):
                filename = secure_filename(listaClases.filename)
                listaClases.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # Procesa el archivo y agrega a la bd
                procesar_archivo_csv(filename, id_curso)

                return redirect(url_for('dashDocente', supervisor_id=supervisor_id))
            
    return render_template('registrarEstudiantes.html', supervisor_id=supervisor_id)

@app.route('/dashDocente/<int:supervisor_id>/asignarGrupos', methods=['GET', 'POST'])
@login_required
def asignarGrupos(supervisor_id):
    # Ruta para asignar los grupos al curso respectivo seleccionado
    # Usa la función de verificación
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))

    cursos = Curso.query.all()
    estudiantes = Estudiante.query.all()

    if not cursos:
        flash('No existen cursos, por favor crear un curso', 'danger')
        return redirect(url_for('dashDocente',supervisor_id=supervisor_id))

    if request.method=='POST':
        id_curso = request.form['curso']
        nuevo_grupo_nombre = request.form['nuevoGrupo']
        estudiantes_seleccionados_ids = request.form.getlist('estudiantes[]')

        # Buscar el curso y crear un nuevo grupo
        curso = Curso.query.get(id_curso)

        if not curso:
            flash('Curso no encontrado', 'danger')
            return redirect(url_for('asignarGrupos', supervisor_id=supervisor_id))

        nuevo_grupo = Grupo(nombre=nuevo_grupo_nombre)
        curso.grupos.append(nuevo_grupo)

        # Asigna estudiantes seleccionados al nuevo grupo
        estudiantes_seleccionados = Estudiante.query.filter(Estudiante.id.in_(estudiantes_seleccionados_ids)).all()
        nuevo_grupo.estudiantes.extend(estudiantes_seleccionados)

        try:
            db.session.commit()
            flash('Grupos asignados con éxito', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error al asignar grupos', 'danger')

        return redirect(url_for('asignarGrupos', supervisor_id=supervisor_id))

    return render_template('asignarGrupos.html', supervisor_id=supervisor_id, cursos=cursos, estudiantes=estudiantes)















# DashBoard del estudiante. Aquí se muestran las series activas y las que ya han sido completadas
@app.route('/dashEstudiante/<int:estudiante_id>', methods=['GET, POST'])
@login_required
def dashEstudiante(estudiante_id):
    # Uso la funcion de verificacion
    if not verify_estudiante(estudiante_id):
        return redirect(url_for('login'))
    # Si el método es get muestra el dashBoard del Estudiante
    if request.method == 'GET':
        return render_template('vistaEstudiante.html', estudiante_id=estudiante_id)

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


#Funcion para ejecutar el script 404
def pagina_no_encontrada(error):
    return render_template('404.html'), 404
    #return redirect(url_for('index')) #te devuelve a esa página


#Ruta para ejecutar el script
if __name__ == '__main__':
    #app.register_error_handler(404, pagina_no_encontrada)
    app.run(host='0.0.0.0',debug=True, port=3000)
    debug=True

# #lsof -i:PUERTO //para revisar todos los procesos que estan usando el puerto
# #kill -9 PID //para matar el proceso que esta usando el puerto
#source /home/ivonne/Documentos/GitHub/MemoriaTituloIvonne/venv/bin/activate


#serie activa por grupos, asignar la serie a un grupo de estudiantes


#Ruta donde debe quedar el archivo del alumno plantillaMaven/src/main/java/org/example/
# Ruta donde debe quedar el archivo de los test del profesor plantillaMaven/src/test/java/org/example/

# @app.route('/registerEstudiante', methods=['GET'])
# def estudianteRegisterPage():
#     return render_template('registerEstudiante.html')

# @app.route('/registerEstudiante', methods=['POST'])
# def registerEstudiante():
#     matricula=request.form.get('matricula')
#     nombres=request.form.get('nombres')
#     apellidos=request.form.get('apellidos')
#     correo=request.form.get('correo')
#     password=request.form.get('password')
#     carrera=request.form.get('carrera')
#     if not nombres or not apellidos or not correo or not password or not matricula:
#         return jsonify(message='Todos los campos son requeridos.'), 400
#         # Verifica si ya existe un estudiante con ese correo
    
#     estudiante = Estudiante.query.filter_by(correo=correo).first()
#     if estudiante:
#         return jsonify(message='Ya existe un estudiante con ese correo.'), 400

#     # Crea el nuevo esstudiante
#     new_estudiante = Estudiante(
#         matricula=matricula,
#         nombres=nombres,
#         apellidos=apellidos,
#         correo=correo,
#         password=generate_password_hash(password),  # Almacena la contraseña de forma segura
#         carrera=carrera
#     )

#     # Añade el nuevo estudiante a la base de datos
#     db.session.add(new_estudiante)
#     db.session.commit()

#     flash('Estudiante registrado exitosamente.', 'success')
#     return redirect(url_for('home'))