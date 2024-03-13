from datetime import datetime, timedelta
import os, shutil
from sqlite3 import IntegrityError
from click import DateTime
from flask import Flask, make_response, render_template, request, url_for, redirect, jsonify, session, flash, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from wtforms import FileField, SubmitField, PasswordField, StringField, DateField, BooleanField, validators, FileField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired, Length, ValidationError
from funciones_archivo.manejoArchivosJava import eliminarPackages, agregarPackage
from funciones_archivo.manejoCarpetas import agregarCarpetaSerieEstudiante,crearCarpetaSerie, crearCarpetaEjercicio, crearArchivadorEstudiante, agregarCarpetaEjercicioEstudiante
from funciones_archivo.manejoMaven import ejecutarTestUnitario
from werkzeug.security import check_password_hash, generate_password_hash, check_password_hash
from DBManager import db, init_app
from basedatos.modelos import Supervisor, Grupo, Serie, Estudiante, Ejercicio, Ejercicio_asignado, Curso, serie_asignada, inscripciones, estudiantes_grupos, supervisores_grupos
from pathlib import Path
import markdown
import csv
import logging
from logging.config import dictConfig
from ansi2html import Ansi2HTMLConverter
import json


dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'errores.log',
            'formatter': 'default',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',  # Puedes ajustar este nivel según tus necesidades
            'propagate': True,
        },
    },
})


#inicializar la aplicacion
app = Flask(__name__)
init_app(app)
app.config['SECRET_KEY'] = 'secret-key-goes-here'


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Nombre de la vista para iniciar sesión

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=120)

UPLOAD_FOLDER = 'uploads' #Ruta donde se guardan los archivos subidos para los ejercicios
ALLOWED_EXTENSIONS = {'md','xml','csv','png','jpg', 'jpeg'}

# Encuentra la ruta del directorio del archivo actual
current_directory = os.path.dirname(os.path.abspath(__file__))

# Define la ruta UPLOAD_FOLDER en relación a ese directorio
UPLOAD_FOLDER = os.path.join(current_directory, "uploads")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Se define que tipo de arhivos se pueden recibir
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def procesar_archivo_csv(filename, curso_id):
    # ----->>>Falta borrar los flash de depuracion :)<<<<------
    # Procesa el archivo
    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Saltar la primera fila
        for row in reader:
            if len(row) != 5:
                # Manejar el error, por ejemplo, omitiendo esta fila o mostrando un mensaje de advertencia
                current_app.logger.warning(f"La fila no tiene el formato esperado: {row}")
                continue  # Saltar esta fila y continuar con la próxima
            
            # Por cada fila, extraer los datos
            matricula, apellidos, nombres, correo, carrera = row
            password = generate_password_hash(matricula)  # Contraseña por defecto: hash de la matrícula
            # Verificar si el estudiante ya existe en la base de datos:
            estudiante_existente = Estudiante.query.filter_by(matricula=matricula).first()
            
            if estudiante_existente:
                # El estudiante con el mismo correo ya existe
                #flash(f'El estudiante con matrícula {matricula} ya está registrado en la base de datos.', 'warning')
                # Revisar si el estudiante ya está asignado a curso_id
                # Usando tabla de inscripciones
                relacion_existente = db.session.query(inscripciones).filter_by(id_estudiante=estudiante_existente.id, id_curso=curso_id).first()
                if relacion_existente:
                    flash(f'El estudiante con matrícula {matricula} ya está inscrito en el curso {curso_id}.', 'warning')
                    continue

                try:
                    nueva_inscripcion = inscripciones.insert().values(id_estudiante=estudiante_existente.id, id_curso=curso_id)
                    db.session.execute(nueva_inscripcion)
                    db.session.commit()
                    flash(f'El estudiante con matrícula {matricula} ha sido inscrito en el curso.', 'success')
                except IntegrityError as e:
                    db.session.rollback()
                    flash(f'Error al registrar en el curso {curso_id} al estudiante {matricula} .', 'warning')
                    continue
            
            # Si el estudiantes no existe, se crea
            elif not estudiante_existente:

                estudiante = Estudiante(
                matricula=matricula,
                apellidos=apellidos,
                nombres=nombres,
                correo=correo,
                password=password,
                carrera=carrera)
                # Crear el nuevo estudiante en la base de datos
                try:
                    db.session.add(estudiante)
                    db.session.flush()  # Esto genera el id sin confirmar en la base de datos
                    estudiante_id = estudiante.id  # Obtener el id del estudiante recién creado
                    db.session.commit()
                    flash(f'El estudiante con matrícula {matricula} ha sido registrado en la base de datos.', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error al crear al registrar {nombres} {apellidos} .', 'warning')
                    continue

                # Si el estudiante se creó correctamente en la bd, se inscribe en el curso
                try:
                    nueva_inscripcion = inscripciones.insert().values(id_estudiante=estudiante_id, id_curso=curso_id)
                    db.session.execute(nueva_inscripcion)
                    db.session.commit()
                    flash(f'El estudiante con matrícula {matricula} ha sido inscrito en el curso.', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error al inscribir a {nombres} {apellidos} en el curso.', 'warning')
                    continue

def calcular_calificacion(total_puntos, puntos_obtenidos):
    if total_puntos == 0:
        return "No hay ejercicios asignados"  # O cualquier mensaje de error adecuado
    else:
        porcentaje = (puntos_obtenidos / total_puntos) * 100

        if porcentaje >= 60:
            # Calcular la calificación para el rango de 4 a 7
            calificacion = 4 + (3 / 40) * (porcentaje - 60)
        else:
            # Calcular la calificación para el rango de 1 a 4
            calificacion = 1 + (3 / 60) * porcentaje

        calificacion = max(1, min(calificacion, 7))

        # Redondear a dos decimales
        calificacion = round(calificacion, 2)

        return calificacion


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
    return True

def verify_ayudante(supervisor_id):

    if not isinstance(current_user, Supervisor):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return False
    if current_user.id != supervisor_id:
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
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

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
        return render_template('registersupervisor.html')
    
    # Verifica si ya existe un supervisor con ese correo
    supervisor = Supervisor.query.filter_by(correo=correo).first()
    if supervisor:
        flash('Ya existe un supervisor con ese correo.', 'warning')
        return render_template('register.html')
    
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
    return redirect(url_for('login'))

@app.route('/dashDocente/<int:supervisor_id>', methods=['GET', 'POST'])
@login_required
def dashDocente(supervisor_id):
    # Usa la función de verificación
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('login'))
    
    series = Serie.query.all()
    cursos = Curso.query.all()
    ejercicios = Ejercicio.query.all()
    ejercicios_por_serie = {}

    # Verificar si hay cursos, series y ejercicios
    curso_seleccionado_id=None
    grupos = []
    if not cursos:
        flash('No existen cursos, por favor crear un curso', 'danger')
        id_curso_seleccionado=None

    if not series:
        flash('No existen series, por favor crear una serie', 'danger')

    if not ejercicios:
        flash('No existen ejercicios, por favor crear un ejercicio', 'danger')

    # Si no se selecciona un curso o se selecciona el primer curso, busca los grupos del primer curso en tu base de datos.
    if curso_seleccionado_id is None or curso_seleccionado_id == 1:  # Ajusta el 1 al ID del primer curso en tu base de datos
        # primer_curso = Curso.query.get(1)  # Obtén el primer curso por ID
        primer_curso = session.get(1)
        if primer_curso:
            grupos = Grupo.query.filter_by(id_curso=curso_seleccionado_id)

    if request.method == 'POST':
        if request.form['accion']=='seleccionarCurso':
            curso_seleccionado_id = int(request.form['curso'])
            # Con el ID del curso seleccionado, se obtienen los grupos asociados
            grupos = Grupo.query.filter_by(id_curso=curso_seleccionado_id).all()
            series = Serie.query.all()
            return render_template('vistaDocente.html', supervisor_id=supervisor_id, cursos=cursos, grupos=grupos, id_curso_seleccionado=curso_seleccionado_id,series=series)
        if request.form['accion']=='asignarSeri189410.pts-0.pa3p2es':
            serie_seleccionada= request.form.get('series')
            grupo_seleccionado= request.form.get('grupos')
            try:
                if serie_seleccionada and grupo_seleccionado: 
                    db.session.execute(serie_asignada.insert().values(id_serie=serie_seleccionada, id_grupo=grupo_seleccionado))
                    db.session.commit()
                    flash('Serie asignada con éxito', 'success')
                    grupos = Grupo.query.filter_by(id_curso=curso_seleccionado_id).all()
                    series = Serie.query.all()
                    return redirect(url_for('dashDocente', supervisor_id=supervisor_id))
            except Exception as e:
                db.session.rollback()
                flash('Error al asignar la serie', 'danger')
                return redirect(url_for('dashDocente', supervisor_id=supervisor_id))

    # Luego, busca los grupos asociados al curso seleccionado, si hay uno.
    grupos = []
    if curso_seleccionado_id is not None:
        grupos = Grupo.query.filter_by(curso_id=curso_seleccionado_id).all()

    return render_template('vistaDocente.html', supervisor_id=supervisor_id, cursos=cursos, grupos=grupos, curso_seleccionado_id=curso_seleccionado_id,series=series)

@app.route('/dashDocente/<int:supervisor_id>/cuentaDocente', methods=['GET', 'POST'])
@login_required
def cuentaDocente(supervisor_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('login'))
    
    supervisor = Supervisor.query.get(supervisor_id)

    if request.method == 'POST':
        contraseña_actual = request.form.get('contraseña_actual')
        nueva_contraseña = request.form.get('nueva_contraseña')
        confirmar_nueva_contraseña = request.form.get('confirmar_nueva_contraseña')

        # Validaciones
        if not check_password_hash(supervisor.password, contraseña_actual):
            flash('Contraseña actual incorrecta', 'danger')
        elif len(nueva_contraseña) < 10:
            flash('La nueva contraseña debe tener al menos 6 caracteres', 'danger')
        elif nueva_contraseña != confirmar_nueva_contraseña:
            flash('Las nuevas contraseñas no coinciden', 'danger')
        else:
            # Cambiar la contraseña
            supervisor.password = generate_password_hash(nueva_contraseña)
            db.session.commit()
            flash('Contraseña actualizada correctamente', 'success')

    return render_template('cuentaDocente.html', supervisor=supervisor, supervisor_id=supervisor_id)


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
        try:
            nueva_serie = Serie(nombre=nombreSerie, activa=activa_value)
            db.session.add(nueva_serie)
            db.session.flush()
            try:
                crearCarpetaSerie(nueva_serie.id)
                current_app.logger.info(f'Se creó la carpeta de la serie {nueva_serie.nombre} con éxito.')
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'Ocurrió un error al crear la carpeta de la serie: {str(e)}')
                return render_template('agregarSerie.html', supervisor_id=supervisor_id)
        except Exception as e:
            db.session.rollback()
    return render_template('agregarSerie.html', supervisor_id=supervisor_id)
    
@app.route('/dashDocente/<int:supervisor_id>/agregarEjercicio', methods=['GET', 'POST'])
@login_required
def agregarEjercicio(supervisor_id):
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('login'))

    series = Serie.query.all()
    filepath_ejercicio = None
    rutaEnunciadoEjercicios = None
    if request.method == 'POST':
        try:
            nombreEjercicio = request.form.get('nombreEjercicio')
            id_serie = request.form.get('id_serie')
            enunciadoFile = request.files.get('enunciadoFile')
            imagenesFiles = request.files.getlist('imagenesFiles')
            unitTestFiles = request.files.getlist('archivosJava')
            serie_actual = db.session.get(Serie, int(id_serie))

            if not any(allowed_file(file.filename, '.java') for file in unitTestFiles):
                flash('Por favor, carga al menos un archivo .java.', 'danger')
                return render_template('agregarEjercicio.html', supervisor_id=supervisor_id, series=series)

            if not imagenesFiles:
                imagenesFiles = None

            nuevo_ejercicio = Ejercicio(nombre=nombreEjercicio, path_ejercicio="", enunciado="", id_serie=id_serie)
            db.session.add(nuevo_ejercicio)
            db.session.flush()

            rutaEjercicio, rutaEnunciadoEjercicios, mensaje = crearCarpetaEjercicio(nuevo_ejercicio.id, id_serie)

            if rutaEjercicio is None:
                raise Exception(mensaje)

            filepath_ejercicio = rutaEjercicio

            # Guardar enunciado
            nuevoNombre = str(nuevo_ejercicio.id) + "_" + str(nuevo_ejercicio.nombre) + ".md"
            enunciadoFile.save(os.path.join(rutaEnunciadoEjercicios, nuevoNombre))
            nuevo_ejercicio.path_ejercicio = rutaEjercicio
            nuevo_ejercicio.enunciado = os.path.join(rutaEnunciadoEjercicios, nuevoNombre)


            if imagenesFiles[0].filename:
                for imagenFile in imagenesFiles:
                    imagen_filename = secure_filename(imagenFile.filename)
                    imagenFile.save(os.path.join(rutaEnunciadoEjercicios, imagen_filename))
            else:
                current_app.logger.warning('No se encontraron imágenes en el enunciado.')

            ubicacionTest = os.path.join(rutaEjercicio, "src/test/java/org/example")
            os.makedirs(ubicacionTest, exist_ok=True)

            # Guardar archivos .java en la carpeta
            for unitTestFile in unitTestFiles:
                nombre_archivo = secure_filename(unitTestFile.filename)
                unitTestFile.save(os.path.join(ubicacionTest, nombre_archivo))

            db.session.commit()
            flash('Ejercicio agregado con éxito', 'success')
            return redirect(url_for('agregarEjercicio', supervisor_id=supervisor_id))

        except Exception as e:
            current_app.logger.error(f'Ocurrió un error al agregar el ejercicio: {str(e)}')
            # Si se produce un error, revertir y eliminar carpetas
            if filepath_ejercicio is not None and os.path.exists(filepath_ejercicio):
                shutil.rmtree(filepath_ejercicio)
            if rutaEnunciadoEjercicios is not None and os.path.exists(rutaEnunciadoEjercicios):
                shutil.rmtree(rutaEnunciadoEjercicios)
            db.session.rollback()
            return redirect(url_for('agregarEjercicio', supervisor_id=supervisor_id, series=series))

    return render_template('agregarEjercicio.html', supervisor_id=supervisor_id, series=series)


@app.route('/dashDocente/<int:supervisor_id>/serie/<int:serie_id>', methods=['GET', 'POST'])
@login_required
def detallesSeries(supervisor_id, serie_id):
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))

    serie = Serie.query.get(serie_id)
    ejercicios = Ejercicio.query.filter_by(id_serie=serie_id).all()
    grupos_asociados = None
    if serie is not None:
        grupos_asociados = Grupo.query.join(serie_asignada).filter(serie_asignada.c.id_serie == serie.id).all()
    if serie is None:
        grupos_asociados = None
        ejercicios= None

    if request.method == 'POST':
        current_app.logger.info(f'Formulario recibido: {request.form}')
        if 'activar_desactivar' in request.form:
            serie.activa = not serie.activa
            db.session.commit()
            return redirect(url_for('detallesSeries', supervisor_id=supervisor_id, serie_id=serie_id))
        elif 'eliminar' in request.form:
            try:
                current_app.logger.info(f'Eliminando la serie {serie.nombre}...')

                # Eliminar los ejercicios asociados a la serie
                Ejercicio.query.filter_by(id_serie=serie_id).delete()

                # Eliminar las asignaciones de serie a grupos
                db.session.execute(serie_asignada.delete().where(serie_asignada.c.id_serie == serie.id))

                # Eliminar la serie
                db.session.delete(serie)

                # Confirmar los cambios en la base de datos
                db.session.commit()

                # Eliminar los archivos asociados a la serie
                rutaSerie = 'ejerciciosPropuestos/Serie_' + str(serie.id)
                shutil.rmtree(rutaSerie)
                rutaEnunciadoSerie = 'enunciadosEjercicios/Serie_' + str(serie.id)
                shutil.rmtree(rutaEnunciadoSerie)
                # Redireccionar y mostrar un mensaje de éxito
                flash('Serie eliminada correctamente.', 'success')
                return redirect(url_for('dashDocente', supervisor_id=supervisor_id))
            except Exception as e:
                # Manejar errores y realizar rollback en caso de error
                current_app.logger.error(f'Ocurrió un error al eliminar la serie: {str(e)}')
                db.session.rollback()
                flash('Ocurrió un error al eliminar la serie.', 'danger')
                return redirect(url_for('detallesSeries', supervisor_id=supervisor_id, serie_id=serie_id))

        elif 'editar' in request.form:
            try:
                current_app.logger.info(f'Editando la serie {serie.nombre}...')
                serie = Serie.query.get(serie_id)
                serie.nombre = request.form.get('nuevo_nombre')
                db.session.commit()
                current_app.logger.info(f'Serie editada correctamente.')
                return redirect(url_for('detallesSeries', supervisor_id=supervisor_id, serie_id=serie_id))
            except Exception as e:
                current_app.logger.danger(f'Ocurrió un error al editar la serie: {str(e)}')
                db.session.rollback()
                return redirect(url_for('detallesSeries', supervisor_id=supervisor_id, serie_id=serie_id))
    if serie is None:
        return redirect(url_for('dashDocente', supervisor_id=supervisor_id))
    return render_template('detallesSerie.html', serie=serie, ejercicios=ejercicios, supervisor_id=supervisor_id, grupos_asociados=grupos_asociados)

@app.route('/dashDocente/<int:supervisor_id>/serie/<int:serie_id>/ejercicio/<int:ejercicio_id>', methods=['GET','POST'])
@login_required
def detallesEjercicio(supervisor_id, serie_id, ejercicio_id):
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))
    ejercicio = Ejercicio.query.get(ejercicio_id)
    serie= Serie.query.get(serie_id)
    if ejercicio and ejercicio.enunciado:
        with open(ejercicio.enunciado, 'r') as enunciado_file:
            enunciado_markdown = enunciado_file.read()
            enunciado_html = markdown.markdown(enunciado_markdown)
    else:
        enunciado_html = "<p>El enunciado no está disponible.</p>"

    if request.method == "POST":
        if 'editar' in request.form:

            current_app.logger.info(f'Editando el ejercicio...{ejercicio.nombre}')
            nombreEjercicio = request.form.get('nuevo_nombre')
            enunciadoFile = request.files.get('enunciadoFile')
            imagenesFiles = request.files.getlist('imagenesFiles')
            unitTestFiles = request.files.getlist('archivosJava')
            current_app.logger.info(f' ENUNCIADO: {enunciadoFile}')
            if nombreEjercicio:
                ejercicio.nombre=nombreEjercicio
                current_app.logger.info(f'nuevo nombre: {nombreEjercicio}')
                db.session.commit()
            if enunciadoFile :
                if os.path.exists(ejercicio.enunciado):
                    path_enunciado = os.path.join("enunciadosEjercicios/", f"Serie_{serie.id}"+"/"+f"Ejercicio_{ejercicio.id}"+"/"+ str(ejercicio.id) + "_" + ejercicio.nombre + ".md")
                    os.remove(ejercicio.enunciado)
                enunciadoFile.save(path_enunciado)
                ejercicio.enunciado = path_enunciado
                current_app.logger.info(f'nuevo enunciado: {ejercicio.enunciado}')  
                db.session.commit()

            # if imagenesFiles :
            #     for imagenFile in imagenesFiles:
            #         imagen_filename = secure_filename(imagenFile.filename)
            #         imagenFile.save(os.path.join(ejercicio.enunciado, imagen_filename))


            if unitTestFiles :
                try:
                    # Define la ruta de la carpeta org/example
                    ruta_carpeta = os.path.join(ejercicio.path_ejercicio , "src", "test", "java", "org")

                    # Verifica si la carpeta existe
                    if os.path.exists(ruta_carpeta):
                        # Elimina todos los archivos en la carpeta
                        for archivo in os.listdir(ruta_carpeta):
                            ruta_archivo = os.path.join(ruta_carpeta, archivo)
                            # Verifica si es un archivo y lo elimina
                            if os.path.isfile(ruta_archivo):
                                os.remove(ruta_archivo)

                    # Guarda los nuevos archivos .java en la carpeta org/example
                    for unitTestFile in unitTestFiles:
                        nombre_archivo = secure_filename(unitTestFile.filename)
                        # Construye la ruta completa para guardar el archivo en la carpeta org/example
                        ruta_archivo = os.path.join(ruta_carpeta, nombre_archivo)
                        # Guarda el archivo en la ruta construida
                        unitTestFile.save(ruta_archivo)
                    db.session.commit()
                except Exception as e:
                    current_app.logger.error(f'Ocurrió un error al guardar los archivos .java: {str(e)}')
        elif 'eliminar' in request.form:
            try:
                current_app.logger.info(f'Eliminando el ejercicio {ejercicio.nombre}...')
                Ejercicio_asignado.query.filter_by(id_ejercicio=ejercicio_id).delete()
                db.session.delete(ejercicio)
                try:
                    shutil.rmtree(ejercicio.path_ejercicio)
                    shutil.rmtree(ejercicio.enunciado)
                except Exception as e:
                    current_app.logger.error(f'Ocurrió un error al eliminar el ejercicio: {str(e)}')
                
            except Exception as e:
                current_app.logger.error(f'Ocurrió un error al eliminar el ejercicio: {str(e)}')
                db.session.rollback()
                flash('Error al eliminar el ejercicio', 'danger')
                return redirect(url_for('detallesSerie', supervisor_id=supervisor_id, serie_id=serie_id))
            db.session.commit()
            
            return redirect(url_for('detallesEjercicio', supervisor_id=supervisor_id,serie_id=serie_id, ejercicio_id=ejercicio_id))
    return render_template('detallesEjercicios.html', ejercicio=ejercicio, supervisor_id=supervisor_id, enunciado=enunciado_html, serie=serie)

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
        try:
            accion= request.form['accion']
            
            if accion == 'crearCurso':
                #Procesar el formulario y agregarlo a la base de datos
                nombre_curso = request.form['nombreCurso']
                activa_value = True if request.form.get('activa') == "true" else False
                if not (nombre_curso) :
                    flash('Por favor, complete todos los campos.', 'danger')
                nuevo_curso= Curso(
                    nombre=nombre_curso,
                    activa=activa_value
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
        except Exception as e:
            current_app.logger.error(f'Ocurrió un error al registrar los estudiantes: {str(e)}')
            db.session.rollback()
            flash('Error al registrar los estudiantes', 'danger')
            return redirect(url_for('registrarEstudiantes', supervisor_id=supervisor_id))
    return render_template('registrarEstudiantes.html', supervisor_id=supervisor_id)

@app.route('/dashDocente/<int:supervisor_id>/detalleCurso/<int:curso_id>', methods=['GET','POST'])
@login_required
def detallesCurso(supervisor_id, curso_id):
    curso_actual=Curso.query.get(curso_id)
    grupos=Grupo.query.filter_by(id_curso=curso_id).all()
    series=Serie.query.all()
    estudiantes_curso = Estudiante.query.filter(Estudiante.cursos.any(id=curso_id)).all()
    
    series_asignadas = Serie.query.join(serie_asignada).filter(serie_asignada.c.id_grupo.in_([grupo.id for grupo in grupos])).all()

    if request.method == 'POST':
        if 'activar_inactivar' in request.form:
            current_app.logger.info(f'Activando o desactivando el curso {curso_actual.nombre}...')
            accion = request.form['activar_inactivar']
            if accion == 'activar':
                curso_actual.activa = True
            elif accion == 'desactivar':
                curso_actual.activa = False
            db.session.commit()
            return redirect(url_for('detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))
        elif 'submit_action' in request.form and request.form['submit_action'] == 'asignarSerie':
            current_app.logger.info(f'Asignando serie a grupo...')
            serie_seleccionada= request.form.get('series')
            grupo_seleccionado = request.form.get('grupos')
            try:
                if serie_seleccionada and grupo_seleccionado: 
                    db.session.execute(serie_asignada.insert().values(id_serie=serie_seleccionada, id_grupo=grupo_seleccionado))
                    db.session.commit()
                    flash('Serie asignada con éxito', 'success')
                    grupos = Grupo.query.filter_by(id_curso=curso_actual.id).all()
                    series = Serie.query.all()
                    return redirect(url_for('detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))
            except Exception as e:
                current_app.logger.error(f'Ocurrió un error al agregar el ejercicio: {str(e)}')
                db.session.rollback()
                flash('Error al asignar la serie', 'danger')
                return redirect(url_for('detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))    
        elif 'eliminar' in request.form:
            try:
                current_app.logger.info(f'Eliminando el curso {curso_actual.nombre}...')

                # Obtener grupos, y series asignadas a el id_curso
                grupos=Grupo.query.filter_by(id_curso=curso_id).all()
                series_asignadas = Serie.query.join(serie_asignada).filter(serie_asignada.c.id_grupo.in_([grupo.id for grupo in grupos])).all()
                
                # Borrar los supervisores de los grupos                
                db.session.execute(supervisores_grupos.delete().where(supervisores_grupos.c.id_grupo.in_([grupo.id for grupo in grupos])))
                
                # Guardar el id de las series asignadas a los grupos.
                id_series_asignadas = [serie.id for serie in series_asignadas]

                # Borrar las series asignadas a los grupos
                db.session.execute(serie_asignada.delete().where(serie_asignada.c.id_grupo.in_([grupo.id for grupo in grupos])))
                
                # Obtener los id_estudiante de los grupos
                estudiantesEnGrupos = db.session.query(estudiantes_grupos).filter(estudiantes_grupos.c.id_grupo.in_([grupo.id for grupo in grupos])).all()
                
                id_estudiantes_grupos = [estudiante.id_estudiante for estudiante in estudiantesEnGrupos]
                
                # Borrar en Ejercicio_asignado todos los registros que tengan el id_estudiante en estudiantesEnGrupos
                ejercicios_a_eliminar=db.session.query(Ejercicio_asignado).filter(Ejercicio_asignado.id_estudiante.in_(id_estudiantes_grupos)).all()
                if ejercicios_a_eliminar:
                    for ejercicio in ejercicios_a_eliminar:
                        db.session.delete(ejercicio)
                        
                # Borrar en tabla estudiantes_grupos, todos los grupos.
                db.session.execute(estudiantes_grupos.delete().where(estudiantes_grupos.c.id_grupo.in_([grupo.id for grupo in grupos])))

                # Borrar los grupos del curso
                if grupos:
                    for grupo in grupos:
                        db.session.delete(grupo)

                # Borrar las inscripciones de los estudiantes en el curso
                db.session.execute(inscripciones.delete().where(inscripciones.c.id_curso == curso_id))

                for id_estudiante in id_estudiantes_grupos:
                    estudiante = Estudiante.query.get(id_estudiante)
                    if estudiante:
                        db.session.delete(estudiante)

                # Borrar el curso
                db.session.delete(curso_actual)

                db.session.commit()
                current_app.logger.info(f'Curso eliminado correctamente.')
                return redirect(url_for('dashDocente', supervisor_id=supervisor_id))
            except Exception as e:
                # Manejar errores y realizar rollback en caso de error
                current_app.logger.error(f'Ocurrió un error al eliminar el curso: {str(e)}')
                db.session.rollback()
                flash('Ocurrió un error al eliminar el curso.', 'danger')
                return redirect(url_for('detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))
        else:
            current_app.logger.error(f'Acción no reconocida: {request.form}')
            return redirect(url_for('detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))
    return render_template('detallesCurso.html', supervisor_id=supervisor_id, curso=curso_actual, grupos=grupos, series_asignadas=series_asignadas, estudiantes_curso=estudiantes_curso, series=series)


@app.route('/dashDocente/<int:supervisor_id>/asignarGrupos/<int:curso_id>', methods=['GET', 'POST'])
@login_required
def asignarGrupos(supervisor_id, curso_id):
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))

    cursos = Curso.query.all()

    if not cursos:
        flash('No existen cursos, por favor crear un curso', 'danger')
        return redirect(url_for('dashDocente', supervisor_id=supervisor_id))
    
    estudiantes_curso = Estudiante.query.filter(Estudiante.cursos.any(id=curso_id)).all()
    if request.method == 'POST':
        accion = request.form['accion']
        if accion == 'seleccionarCurso':
            id_curso_seleccionado = request.form['curso']
            flash('se cambio el curso a {curso_id}', 'success')
            return redirect(url_for('asignarGrupos', supervisor_id=supervisor_id, curso_id=id_curso_seleccionado))

        elif accion == 'seleccionarEstudiantes':
            # Recibir los estudiantes seleccionados
            estudiantes_seleccionados_ids= request.form.getlist('estudiantes[]')
            # Recibir el nombre del grupo
            nombre_grupo = request.form['nombreGrupo']
            # Recibir el id del curso
            id_curso_seleccionado = request.form['curso_seleccionado']
            if not nombre_grupo or not estudiantes_seleccionados_ids or not id_curso_seleccionado :
                flash('Por favor, complete todos los campos.', 'danger')
                return redirect(url_for('asignarGrupos', supervisor_id=supervisor_id, curso_id=id_curso_seleccionado))

            try:
                # Verificar si el grupo ya existe
                flash(f'estudiantes seleccionados: {estudiantes_seleccionados_ids}', 'danger')
                nuevo_grupo=Grupo(nombre=nombre_grupo, id_curso=id_curso_seleccionado)
                db.session.add(nuevo_grupo)
                db.session.commit()
                flash('Grupo creado con éxito', 'success')

            except Exception as e:
                current_app.logger.error(f'Ocurrió un error al agregar el grupo: {str(e)}')
                db.session.rollback()
            if nuevo_grupo:
                # Con los estudiantes que se seleccionaron, se asocian al grupo creado utilizando tabla asociacion estudiantes_grupos
                for estudiante_id in estudiantes_seleccionados_ids:
                    try:
                        nueva_relacion=estudiantes_grupos.insert().values(id_estudiante=estudiante_id, id_grupo=nuevo_grupo.id)
                        db.session.execute(nueva_relacion)
                        db.session.commit()
                        flash('Estudiantes asignados con éxito', 'success')
                    except Exception as e:
                        current_app.logger.error(f'Ocurrió un error al asignar estudiantes: {str(e)}')
                        db.session.rollback()
                try:
                    nuevo_registro= supervisores_grupos.insert().values(
                        id_supervisor=supervisor_id,
                        id_grupo=nuevo_grupo.id
                    )
                    db.session.execute(nuevo_registro)
                    db.session.commit()
                except Exception as e:
                    current_app.logger.error(f'Ocurrió un error al asignar el supervisor al grupo: {str(e)}')
                    db.session.rollback()

    return render_template('asignarGrupos.html', supervisor_id=supervisor_id, cursos=cursos, curso_seleccionado=curso_id,estudiantes_curso=estudiantes_curso)

@app.route('/dashDocente/<int:supervisor_id>/detalleCurso/<int:curso_id>/detalleGrupo/<int:grupo_id>', methods=['GET', 'POST'])
@login_required
def detallesGrupo(supervisor_id, curso_id, grupo_id):
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))
    grupo=Grupo.query.get(grupo_id)
    curso=Curso.query.get(curso_id)
    estudiantes = Estudiante.query.filter(Estudiante.cursos.any(id=curso_id)).all()
    # Obtener todos los estudiantes que pertenecen al grupo usando tabla asociacion estudiantes_grupos
    estudiantes_grupo = Estudiante.query.join(estudiantes_grupos).filter(estudiantes_grupos.c.id_grupo == grupo_id).all()
    curso=Curso.query.get(curso_id)

    if request.method == 'POST':
        if 'eliminar' in request.form:
            try:
                # Eliminar serie_asignada
                db.session.execute(serie_asignada.delete().where(serie_asignada.c.id_grupo.in_(grupo_id)))
                
                # Eliminar estudiantes_grupos
                db.session.execute(estudiantes_grupos.delete().where(estudiantes_grupos.c.id_grupo.in_(grupo_id)))

                # Eliminar en supervisores_grupos
                db.session.execute(supervisores_grupos.delete().where(supervisores_grupos.c.id_grupo.in_(grupo_id)))

                # Eliminar el grupo
                db.session.delete(grupo)
                db.session.commit()
                current_app.logger.info(f'Grupo eliminado correctamente.')
                return redirect(url_for('detallesCurso', supervisor_id=supervisor_id, curso_id=curso_id))
            except Exception as e:
                current_app.logger.error(f'Ocurrió un error al eliminar el grupo: {str(e)}')
                db.session.rollback()
                flash('Ocurrió un error al eliminar el grupo.', 'danger')
                return redirect(url_for('detallesGrupo', supervisor_id=supervisor_id, curso_id=curso_id, grupo_id=grupo_id))
        elif 'renombrar' in request.form:
            current_app.logger.info(f'Recibiendo formulario para renombrar el grupo...')
            try:
                current_app.logger.info(f'Renombrando el grupo {grupo.nombre}...')
                grupo.nombre = request.form.get('nuevo_nombre')
                db.session.commit()
                return redirect(url_for('detallesGrupo', supervisor_id=supervisor_id, curso_id=curso_id, grupo_id=grupo_id))
            except Exception as e:
                current_app.logger.error(f'Ocurrió un error al renombrar el grupo: {str(e)}')
                db.session.rollback()
                return redirect(url_for('detallesGrupo', supervisor_id=supervisor_id, curso_id=curso_id, grupo_id=grupo_id))
        else :
            current_app.logger.error(f'Acción no reconocida: {request.form}')
    grupo=Grupo.query.get(grupo_id)
    curso=Curso.query.get(curso_id)
    # Obtener todos los estudiantes que pertenecen al grupo usando tabla asociacion estudiantes_grupos
    estudiantes_grupo = Estudiante.query.join(estudiantes_grupos).filter(estudiantes_grupos.c.id_grupo == grupo_id).all()
    return render_template('detallesGrupo.html', supervisor_id=supervisor_id, grupo=grupo, estudiantes_grupo=estudiantes_grupo, curso=curso)

@app.route('/dashDocente/<int:supervisor_id>/detalleCurso/<int:curso_id>/detalleGrupo/<int:grupo_id>/eliminarEstudiante', methods=['GET', 'POST'])
@login_required
def eliminarEstudiante(supervisor_id, curso_id, grupo_id):
    curso= Curso.query.get(curso_id)
    grupo=Grupo.query.get(grupo_id)

    estudiantesEnGrupos = db.session.query(estudiantes_grupos).filter(estudiantes_grupos.c.id_grupo.in_([grupo.id])).all()
    
    id_estudiantes_grupos = [estudiante.id_estudiante for estudiante in estudiantesEnGrupos]
    estudiantes=[]
    for estudiante_id in id_estudiantes_grupos:
        estudiante = Estudiante.query.get(estudiante_id)
        if estudiante:
            estudiantes.append(estudiante)
            

    return render_template('eliminarEstudiante.html', supervisor_id=supervisor_id, curso=curso, grupo=grupo, estudiantes=estudiantes)
    
@app.route('/dashDocente/<int:supervisor_id>/detalleCurso/<int:curso_id>/detalleEstudiante/<int:estudiante_id>', methods=['GET', 'POST'])
@login_required
def detallesEstudiante(supervisor_id, curso_id, estudiante_id):
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))
    
    estudiante = Estudiante.query.get(estudiante_id)
    cursos = []
    grupos = []
    
    # Obtener cursos
    consulta_cursos = db.session.query(inscripciones).filter_by(id_estudiante=estudiante_id, id_curso=curso_id).all()
    if consulta_cursos:
        for consulta in consulta_cursos:
            curso = Curso.query.get(consulta.id_curso)
            cursos.append(curso)
    if not cursos:
        cursos = None
        grupos = None
    # Obtener grupos
    consulta_grupos = db.session.query(estudiantes_grupos).filter_by(id_estudiante=estudiante_id).all()
    if consulta_grupos:
        for consulta in consulta_grupos:
            grupo = Grupo.query.get(consulta.id_grupo)
            grupos.append(grupo)
    if not grupos:
        grupos = None

    # Obtener series asignadas
    series_asignadas = []
    ejercicios= []
    consulta_id_series = db.session.query(serie_asignada).filter(serie_asignada.c.id_grupo.in_([grupo.id for grupo in grupos])).all()
    if consulta_id_series:
        for consulta in consulta_id_series:
            serie = Serie.query.get(consulta.id_serie)
            ejercicios = Ejercicio.query.filter_by(id_serie=serie.id).all()
            series_asignadas.append(serie)
    if not series_asignadas:
        series_asignadas = None
    
    # Obtener ejercicios asignados al estudiante
    ejercicios_asignados = Ejercicio_asignado.query.filter_by(id_estudiante=estudiante_id).all()
    
    # Obtener los ejercicios de las series
    # Crear una lista para almacenar los datos de los ejercicios
    ejercicios = []
    if ejercicios_asignados:
        for ejercicio_asignado in ejercicios_asignados:
            ejercicio = Ejercicio.query.get(ejercicio_asignado.id_ejercicio)
            ejercicios.append(ejercicio)
    
    curso_actual = Curso.query.get(curso_id)
    current_app.logger.info(f'series_asignadas: {series_asignadas}')
    curso_actual = Curso.query.get(curso_id)
    current_app.logger.info(f'cursos: {cursos}, grupos: {grupos}')
    current_app.logger.info(f'ejercicio: {ejercicios}, ejercicios_asignados: {ejercicios_asignados}')
    return render_template('detallesEstudiantes.html', supervisor_id=supervisor_id, estudiante=estudiante, curso_actual=curso_actual, cursos=cursos, grupos=grupos,series_asignadas=series_asignadas, ejercicios_asignados=ejercicios_asignados)

@app.route('/dashDocente/<int:supervisor_id>/detalleCurso/<int:curso_id>/detalleEstudiante/<int:estudiante_id>/examinarEjercicio/<int:ejercicio_id>', methods=['GET', 'POST'])
@login_required
def examinarEjercicio(supervisor_id, curso_id, estudiante_id, ejercicio_id):
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))
    estudiante = Estudiante.query.get(estudiante_id)
    ejercicio = Ejercicio.query.get(ejercicio_id)
    ejercicio_asignado= Ejercicio_asignado.query.filter_by(id_estudiante=estudiante_id, id_ejercicio=ejercicio_id).first()
    serie = Serie.query.get(ejercicio.id_serie)
    grupo = Grupo.query.join(serie_asignada).filter(serie_asignada.c.id_serie == serie.id).first()
    curso= Curso.query.get(curso_id)
    estado = ejercicio_asignado.estado
    test_output= ejercicio_asignado.test_output
    fecha_ultimo_envio= ejercicio_asignado.fecha_ultimo_envio
    contador= ejercicio_asignado.contador
    test_output_dict = json.loads(test_output)
    if ejercicio and ejercicio.enunciado:
        with open(ejercicio.enunciado, 'r') as enunciado_file:
            enunciado_markdown = enunciado_file.read()
            enunciado_html = markdown.markdown(enunciado_markdown)
    else:
        enunciado_html = "<p>El enunciado no está disponible.</p>"

    rutaEnvio = ejercicio_asignado.ultimo_envio
    current_app.logger.info(f'rutaEnvio: {rutaEnvio}')
    archivos_java=[]
    # Obtener la lista de archivos .java en la carpeta
    for archivo in os.listdir(rutaEnvio):
        if archivo.endswith('.java'):
            with open(os.path.join(rutaEnvio, archivo), 'r') as f:
                contenido = f.read()
                archivos_java.append({'nombre': archivo, 'contenido': contenido})

    return render_template('examinarEjercicio.html', supervisor_id=supervisor_id, estudiante=estudiante, ejercicio=ejercicio, serie=serie, grupo=grupo, curso=curso, ejercicio_asignado=ejercicio_asignado, enunciado=enunciado_html, archivos_java=archivos_java, estado=estado, fecha_ultimo_envio=fecha_ultimo_envio, test_output=test_output_dict, contador=contador)

# Ruta para ver el progreso de los estudiantes de un curso
@app.route('/dashDocente/<int:supervisor_id>/progresoCurso/<int:curso_id>', methods=['GET', 'POST'])
@login_required
def progresoCurso(supervisor_id, curso_id):

    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))

    curso = Curso.query.get(curso_id)

    # Recuperar los estudiantes del curso
    estudiantes_curso = Estudiante.query.filter(Estudiante.cursos.any(id=curso_id)).all()

    # Recuperar los grupos del curso
    grupos_curso = Grupo.query.filter_by(id_curso=curso_id).all()

    # Recuperar todas las series asignadas de todos los grupos
    series_asignadas = Serie.query.join(serie_asignada).filter(serie_asignada.c.id_grupo.in_([grupo.id for grupo in grupos_curso])).all()

    if request.method == 'POST':
        # Obtener el ID de la serie seleccionada desde el formulario
        serie_seleccionada_id = request.form.get('serie')

        # Filtrar ejercicios por la serie seleccionada
        ejercicios = Ejercicio.query.filter_by(id_serie=serie_seleccionada_id).all()

        # Filtrar ejercicios asignados por estudiante y ejercicios de la serie
        ejercicios_asignados = Ejercicio_asignado.query.filter(
            Ejercicio_asignado.id_estudiante.in_([estudiante.id for estudiante in estudiantes_curso]),
            Ejercicio_asignado.id_ejercicio.in_([ejercicio.id for ejercicio in ejercicios])
        ).all()

        # Lógica para asignar colores a las celdas en la tabla
        colores_info = []

        for estudiante in estudiantes_curso:
            estudiante_info = {'nombre': f'{estudiante.nombres} {estudiante.apellidos}', 'ejercicios': [], 'calificacion': None}

            total_puntos = len(ejercicios)  # Total de puntos igual a la cantidad total de ejercicios
            puntos_obtenidos = 0

            for ejercicio in ejercicios:
                ejercicio_asignado = next(
                    (ea for ea in ejercicios_asignados if ea.id_estudiante == estudiante.id and ea.id_ejercicio == ejercicio.id), None
                )

                if ejercicio_asignado and ejercicio_asignado.estado:
                    puntos_obtenidos += 1  # Sumar 1 punto por cada ejercicio aprobado

                if ejercicio_asignado:
                    intentos = ejercicio_asignado.contador
                    if ejercicio_asignado.estado:
                        estudiante_info['ejercicios'].append({'id': ejercicio.id, 'color': 'success', 'intentos': intentos})
                    elif not ejercicio_asignado.estado and intentos > 0:
                        estudiante_info['ejercicios'].append({'id': ejercicio.id, 'color': 'danger', 'intentos': intentos})
                    else:
                        estudiante_info['ejercicios'].append({'id': ejercicio.id, 'color': 'info', 'intentos': intentos})
                else:
                    estudiante_info['ejercicios'].append({'id': ejercicio.id, 'color': 'info', 'intentos': 0})

            # Calcula la calificación usando la función calcular_calificacion
            if puntos_obtenidos is not None:
                estudiante_info['calificacion'] = calcular_calificacion(total_puntos, puntos_obtenidos)

            colores_info.append(estudiante_info)

        return render_template('progresoCurso.html', supervisor_id=supervisor_id, curso=curso, estudiantes_curso=estudiantes_curso, series_asignadas=series_asignadas, ejercicios=ejercicios, colores_info=colores_info)
    return render_template('progresoCurso.html', supervisor_id=supervisor_id, curso=curso, estudiantes_curso=estudiantes_curso, series_asignadas=series_asignadas)


###########################################################################################################################################
###########################################################################################################################################
###########################################################################################################################################


@app.route('/dashEstudiante/<int:estudiante_id>', methods=['GET', 'POST'])
@login_required
def dashEstudiante(estudiante_id):

    if not verify_estudiante(estudiante_id):
        return redirect(url_for('login'))

    estudiante = db.session.get(Estudiante, int(estudiante_id))

    curso = (
        Curso.query
        .join(inscripciones)
        .filter(inscripciones.c.id_estudiante == estudiante_id)
        .filter(Curso.activa == True)
        .first()
    )
    if not curso:
        return render_template('vistaEstudiante.html', estudiante_id=estudiante_id, estudiante=estudiante, curso=None, grupo=None, supervisor=None, seriesAsignadas=None, ejerciciosPorSerie=None)
    # Obtiene el grupo asociado al estudiante
    grupo = (
        Grupo.query
        .join(estudiantes_grupos)  # Join con la tabla estudiantes_grupos
        .filter(estudiantes_grupos.c.id_grupo == Grupo.id)
        .filter(estudiantes_grupos.c.id_estudiante == estudiante_id)
        .first()
    )
    # Si no se encuentra ningún grupo asignado, grupo será None
    if not grupo:
        grupo_nombre = "Ningún grupo asignado"
    else:
        grupo_nombre = grupo.nombre

    supervisor = None

    # Obtiene el supervisor asignado si grupo no es None
    if grupo:
        supervisor = (
            Supervisor.query
            .join(supervisores_grupos)
            .filter(supervisores_grupos.c.id_supervisor == Supervisor.id)
            .filter(supervisores_grupos.c.id_grupo == grupo.id)
            .first()
        )

    seriesAsignadas = []

    # Obtiene las series asignadas solo si grupo no es None
    if grupo:
        seriesAsignadas = (
        Serie.query
        .join(serie_asignada)
        .filter(serie_asignada.c.id_grupo == grupo.id)
        .filter(Serie.activa)  # Filtrar por series activas
        .all()
    )


    # A continuación, puedes obtener los ejercicios para cada serie en series_asignadas
    ejerciciosPorSerie = {}
    for serieAsignada in seriesAsignadas:
        ejercicios = Ejercicio.query.filter_by(id_serie=serieAsignada.id).all()
        ejerciciosPorSerie[serieAsignada] = ejercicios

    return render_template('vistaEstudiante.html', estudiante_id=estudiante_id, estudiante=estudiante,grupo=grupo, curso=curso, supervisor=supervisor,seriesAsignadas=seriesAsignadas,ejerciciosPorSerie=ejerciciosPorSerie)

@app.route('/dashEstudiante/<int:estudiante_id>/serie/<int:serie_id>', methods=['GET', 'POST'])
@login_required
def detallesSeriesEstudiantes(estudiante_id, serie_id):

    if not verify_estudiante(estudiante_id):
        return redirect(url_for('login'))
    serie = db.session.get(Serie, serie_id)
    ejercicios = Ejercicio.query.filter_by(id_serie=serie_id).all()
    ejercicios_asignados = (
        Ejercicio_asignado.query
        .filter(Ejercicio_asignado.id_estudiante == estudiante_id)
        .filter(Ejercicio_asignado.id_ejercicio.in_([ejercicio.id for ejercicio in ejercicios]))
        .all()
    )
    ejercicios_aprobados = sum(1 for ea in ejercicios_asignados if ea.estado)

    total_ejercicios = len(ejercicios)
    if total_ejercicios == 0:
        calificacion = 0
    else:
        calificacion = calcular_calificacion(total_ejercicios, ejercicios_aprobados)

    return render_template('detallesSerieEstudiante.html', serie=serie, ejercicios=ejercicios, estudiante_id=estudiante_id,calificacion=calificacion)

@app.route('/dashEstudiante/<int:estudiante_id>/serie/<int:serie_id>/ejercicio/<int:ejercicio_id>', methods=['GET', 'POST'])
@login_required
def detallesEjerciciosEstudiantes(estudiante_id, serie_id, ejercicio_id):
    if not verify_estudiante(estudiante_id):
        return redirect(url_for('login'))

    serie = Serie.query.get(serie_id)
    ejercicio = Ejercicio.query.get(ejercicio_id)
    matricula= Estudiante.query.get(estudiante_id).matricula
    ejercicios = Ejercicio.query.filter_by(id_serie=serie_id).all()
    ejercicios_asignados = (
        Ejercicio_asignado.query
        .filter(Ejercicio_asignado.id_estudiante == estudiante_id)
        .filter(Ejercicio_asignado.id_ejercicio.in_([ejercicio.id for ejercicio in ejercicios]))
        .all()
    )

    colors_info = []

    for ejercicio_disponible in ejercicios:
        ejercicio_info = {'nombre': ejercicio_disponible.nombre, 'id': ejercicio_disponible.id, 'color': 'bg-persian-indigo-opaco'}
            
        for ejercicio_asignado in ejercicios_asignados:
            if ejercicio_disponible.id == ejercicio_asignado.id_ejercicio:
                if ejercicio_asignado.estado:
                    ejercicio_info['color'] = 'bg-success-custom'
                elif not ejercicio_asignado.estado and ejercicio_asignado.contador > 0:
                    ejercicio_info['color'] = 'bg-danger-custom'
                    
        colors_info.append(ejercicio_info)

    ejercicios_aprobados = sum(1 for ea in ejercicios_asignados if ea.estado)

    total_ejercicios = len(ejercicios)
    if total_ejercicios == 0:
        calificacion=0
    else:
        calificacion = calcular_calificacion(total_ejercicios, ejercicios_aprobados)
    
    if ejercicio and ejercicio.enunciado:
        with open(ejercicio.enunciado, 'r') as enunciado_file:
            enunciado_markdown = enunciado_file.read()
            enunciado_html = markdown.markdown(enunciado_markdown)
    else:
        enunciado_html = "<p>El enunciado no está disponible.</p>"

    if request.method == 'POST':
        archivos_java = request.files.getlist('archivo_java')
        rutaArchivador=None
        try:
            rutaArchivador = crearArchivadorEstudiante(matricula)
            flash('Se creo exitosamente el archivador', 'success')
        except Exception as e:
            current_app.logger.error(f'Ocurrió un error al crear el archivador: {str(e)}')
            return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)

        if os.path.exists(rutaArchivador):
            ejercicioAsignado = Ejercicio_asignado.query.filter_by(id_estudiante=estudiante_id, id_ejercicio=ejercicio.id).first()
            if not ejercicioAsignado:
                try:
                    nuevoEjercicioAsignado = Ejercicio_asignado(
                    id_estudiante=estudiante_id,
                    id_ejercicio=ejercicio_id,
                    contador=0,
                    estado=False,
                    ultimo_envio=None,
                    fecha_ultimo_envio=datetime.now(),
                    test_output=None)
                    db.session.add(nuevoEjercicioAsignado)
                    db.session.flush()
                    try:
                        rutaSerieEstudiante = agregarCarpetaSerieEstudiante(rutaArchivador, serie.id)
                        current_app.logger.info(f'Ruta serie estudiante: {rutaSerieEstudiante}')
                        if os.path.exists(rutaSerieEstudiante):
                            try:
                                rutaEjercicioEstudiante = agregarCarpetaEjercicioEstudiante(rutaSerieEstudiante, ejercicio.id,  ejercicio.path_ejercicio)
                                current_app.logger.info(f'Ruta ejercicio estudiante: {rutaEjercicioEstudiante}')
                                if os.path.exists(rutaEjercicioEstudiante):
                                    for archivo_java in archivos_java:
                                        rutaFinal = os.path.join(rutaEjercicioEstudiante, 'src/main/java/org/example')
                                        if archivo_java and archivo_java.filename.endswith('.java'):
                                            archivo_java.save(os.path.join(rutaFinal, archivo_java.filename))
                                            current_app.logger.info(f'Archivo guardado en: {rutaFinal}')
                                    resultadoTest= ejecutarTestUnitario(rutaEjercicioEstudiante)
                                    current_app.logger.info(f'Resultado test: {resultadoTest}')
                                    if resultadoTest == 'BUILD SUCCESS':
                                        current_app.logger.info(f'El test fue exitoso')
                                        nuevoEjercicioAsignado.contador += 1
                                        nuevoEjercicioAsignado.ultimo_envio = rutaFinal
                                        nuevoEjercicioAsignado.fecha_ultimo_envio = datetime.now()
                                        nuevoEjercicioAsignado.test_output = json.dumps(resultadoTest)
                                        nuevoEjercicioAsignado.estado = True
                                        db.session.commit()
                                        errores = {"tipo": "success", "titulo": "Todos los test aprobados", "mensaje": resultadoTest}
                                        return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, errores=errores ,estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
                                    else:
                                        current_app.logger.info(f'El test no fue exitoso')
                                        nuevoEjercicioAsignado.contador += 1
                                        nuevoEjercicioAsignado.ultimo_envio = rutaFinal
                                        nuevoEjercicioAsignado.fecha_ultimo_envio = datetime.now()
                                        nuevoEjercicioAsignado.test_output = json.dumps(resultadoTest)
                                        nuevoEjercicioAsignado.estado = False
                                        db.session.commit()
                                        errores= {"tipo": "danger", "titulo": "Errores en la ejecución de pruebas unitarias", "mensaje": resultadoTest}
                                        return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, errores=errores ,estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
                            except Exception as e:
                                current_app.logger.error(f'Ocurrió un error al agregar la carpeta del ejercicio: {str(e)}')
                                db.session.rollback()
                                return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
                    except Exception as e:
                        current_app.logger.error(f'Ocurrió un error al agregar la carpeta de la serie: {str(e)}')
                        db.session.rollback()
                        # Agregar la eliminación de la carpeta??
                        return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
                except Exception as e:
                    current_app.logger.error(f'Ocurrió un error al agregar el ejercicio asignado: {str(e)}')
                    db.session.rollback()
                    # Agregar la eliminación de la carpeta??
                    return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
            else:
                try:
                    rutaSerieEstudiante = agregarCarpetaSerieEstudiante(rutaArchivador, serie.id)
                    if os.path.exists(rutaSerieEstudiante):
                        try:
                            rutaEjercicioEstudiante = agregarCarpetaEjercicioEstudiante(rutaSerieEstudiante, ejercicio.id,  ejercicio.path_ejercicio)
                            if os.path.exists(rutaEjercicioEstudiante):
                                for archivo_java in archivos_java:
                                    rutaFinal = os.path.join(rutaEjercicioEstudiante, 'src/main/java/org/example')
                                    if archivo_java and archivo_java.filename.endswith('.java'):
                                        archivo_java.save(os.path.join(rutaFinal, archivo_java.filename))
                                resultadoTest= ejecutarTestUnitario(rutaEjercicioEstudiante)
                                if resultadoTest == 'BUILD SUCCESS':
                                    ejercicioAsignado.contador += 1
                                    ejercicioAsignado.ultimo_envio = rutaFinal
                                    ejercicioAsignado.fecha_ultimo_envio = datetime.now()
                                    ejercicioAsignado.test_output = json.dumps(resultadoTest)
                                    ejercicioAsignado.estado = True
                                    db.session.commit()
                                    errores = {"tipo": "success", "titulo": "Todos los test aprobados", "mensaje": resultadoTest}
                                    return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, errores=errores ,estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
                                else:
                                    ejercicioAsignado.contador += 1
                                    ejercicioAsignado.ultimo_envio = rutaFinal
                                    ejercicioAsignado.fecha_ultimo_envio = datetime.now()
                                    ejercicioAsignado.test_output = json.dumps(resultadoTest)
                                    ejercicioAsignado.estado = False
                                    db.session.commit()
                                    errores= {"tipo": "danger", "titulo": "Errores en la ejecución de pruebas unitarias", "mensaje": resultadoTest}
                                    current_app.logger.info(f'resultadoTest: {resultadoTest}')
                                    return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, errores=errores ,estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
                        except Exception as e:
                            db.session.rollback()
                            current_app.logger.error(f'Ocurrió un error al agregar la carpeta del ejercicio: {str(e)}')
                            return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, errores=resultadoTest, estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
                except Exception as e:
                    current_app.logger.error(f'Ocurrió un error al agregar la carpeta de la serie: {str(e)}')
                    db.session.rollback()
    return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados, colors_info=colors_info, calificacion=calificacion)

@app.route('/dashEstudiante/<int:estudiante_id>/cuentaEstudiante', methods=['GET', 'POST'])
@login_required
def cuentaEstudiante(estudiante_id):
    if not verify_estudiante(estudiante_id):
        return redirect(url_for('login'))
    
    estudiante = Estudiante.query.get(estudiante_id)

    if request.method == 'POST':
        contraseña_actual = request.form.get('contraseña_actual')
        nueva_contraseña = request.form.get('nueva_contraseña')
        confirmar_nueva_contraseña = request.form.get('confirmar_nueva_contraseña')

        # Validaciones
        if not check_password_hash(estudiante.password, contraseña_actual):
            flash('Contraseña actual incorrecta', 'danger')
        elif len(nueva_contraseña) < 10:
            flash('La nueva contraseña debe tener al menos 6 caracteres', 'danger')
        elif nueva_contraseña != confirmar_nueva_contraseña:
            flash('Las nuevas contraseñas no coinciden', 'danger')
        else:
            # Cambiar la contraseña
            estudiante.password = generate_password_hash(nueva_contraseña)
            db.session.commit()
            flash('Contraseña actualizada correctamente', 'success')

    return render_template('cuentaEstudiante.html', estudiante=estudiante, estudiante_id=estudiante_id)




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
# source /home/ivonne/Documentos/GitHub/MemoriaTituloIvonne/venv/bin/activate
# serie activa por grupos, asignar la serie a un grupo de estudiantes
# Ruta donde debe quedar el archivo del alumno plantillaMaven/src/main/java/org/example/
# Ruta donde debe quedar el archivo de los test del profesor plantillaMaven/src/test/java/org/example/

# ssh ivonne@pa3p2.inf.udec.cl
# mail5@udec.cl
#gunicorn -w 2 -b 0.0.0.0:3000 main:app