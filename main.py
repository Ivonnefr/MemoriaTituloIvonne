from datetime import datetime
import os, shutil
from sqlite3 import IntegrityError
from click import DateTime
from flask import Flask, make_response, render_template, request, url_for, redirect, jsonify, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from wtforms import FileField, SubmitField, PasswordField, StringField, DateField, BooleanField, validators, FileField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired, Length, ValidationError
from funciones_archivo.manejoArchivosJava import eliminarPackages, agregarPackage
from funciones_archivo.manejoCarpetas import agregarCarpetaSerieEstudiante,crearCarpetaSerie, crearCarpetaEjercicio, crearArchivadorEstudiante, agregarCarpetaEjercicioEstudiante
from funciones_archivo.manejoMaven import ejecutarTestUnitario, compilarProyecto
from werkzeug.security import check_password_hash, generate_password_hash
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
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'ERROR',
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
    # ----->>>Falta borrar los flash de depuracion :)<<<<------
    # Procesa el archivo
    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Saltar la primera fila
        for row in reader:
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
    porcentaje = (puntos_obtenidos / total_puntos) * 100

    if porcentaje >= 60:
        # Calcular la calificación para el rango de 4 a 7
        calificacion = 4 + (3 / 40) * (porcentaje - 60)
    else:
        # Calcular la calificación para el rango de 1 a 4
        calificacion = 1 + (3 / 60) * porcentaje

    calificacion = max(1, min(calificacion, 7))

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
        return render_template('registersupervisor.html')
    
    # Verifica si ya existe un supervisor con ese correo
    supervisor = Supervisor.query.filter_by(correo=correo).first()
    if supervisor:
        flash('Ya existe un supervisor con ese correo.', 'warning')
        return render_template('registersupervisor.html')
    
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
        if request.form['accion']=='asignarSeries':
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
            crearCarpetaSerie(nueva_serie.id, nueva_serie.nombre)
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
    # --->Restringir la cantidad de caracteres del enunciado<---
    # se debe guardar en: ./id_serie_nombre_serie/id_ejercicio/src/test/java/org/example
    series = Serie.query.all()
    
    if request.method == 'POST':
        nombreEjercicio = request.form.get('nombreEjercicio')
        id_serie = request.form.get('id_serie')
        enunciadoFile = request.files.get('enunciadoFile')
        imagenesFiles = request.files.getlist('imagenesFiles')
        unitTestFile = request.files.getlist('archivosJava')
        serie_actual = db.session.get(Serie, int(id_serie))

        # Recuperamos el nombre del archivo de test unitario
        if not any(allowed_file(file.filename, '.java') for file in unitTestFile):
            flash('Por favor, carga al menos un archivo .java.', 'danger')
            return render_template('agregarEjercicio.html', supervisor_id=supervisor_id, series=series)

        nuevo_ejercicio = Ejercicio(nombre=nombreEjercicio, path_ejercicio="", enunciado="", id_serie=id_serie)
        nuevoNombre= str(nuevo_ejercicio.id) + "ejercicio.md"
        filepath_ejercicio = None

        try:
            db.session.add(nuevo_ejercicio)
            db.session.flush()
            rutaEjercicio,rutaEnunciadoEjercicios, mensaje = crearCarpetaEjercicio(nuevo_ejercicio.id, id_serie, serie_actual.nombre)

            if rutaEjercicio is None:
                raise Exception(mensaje)

            filepath_ejercicio = rutaEjercicio
            nuevoNombre = str(nuevo_ejercicio.id) + "_" + str(nuevo_ejercicio.nombre) + ".md"

            enunciadoFile.save(os.path.join(rutaEnunciadoEjercicios, nuevoNombre))

            nuevo_ejercicio.path_ejercicio = rutaEjercicio
            nuevo_ejercicio.enunciado = os.path.join(rutaEnunciadoEjercicios, nuevoNombre)

            # Itera a través de las imágenes y guárdalas en la misma carpeta
            for imagenFile in imagenesFiles:
                imagen_filename = secure_filename(imagenFile.filename)
                if os.path.exists(rutaEnunciadoEjercicios):
                    imagenFile.save(os.path.join(rutaEnunciadoEjercicios, imagen_filename))


            ubicacionTest = os.path.join(rutaEjercicio, "src/test/java/org/example")
            if os.path.exists(ubicacionTest):
                for unitTest in unitTestFile:
                    nombre_archivo = secure_filename(unitTest.filename)
                    unitTest.save(os.path.join(ubicacionTest, nombre_archivo))
            db.session.commit()
        except Exception as e:

            if os.path.exists(filepath_ejercicio) or os.path.exists(rutaEjercicio):
                os.remove(filepath_ejercicio)
            if os.path.exists(rutaEnunciadoEjercicios):
                shutil.rmtree(rutaEnunciadoEjercicios)

            # Si se produce un error con la base de datos después de crear la carpeta, puedes eliminarla aquí
            flash(f'Ocurrió un error al agregar el ejercicio: {str(e)}', 'danger')
            db.session.rollback()
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
            nombre_curso = request.form['nombreCurso']
            activa_value = True if request.form.get('activa') == "true" else False
            if not nombre_curso :
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
            
    return render_template('registrarEstudiantes.html', supervisor_id=supervisor_id)

@app.route('/dashDocente/<int:supervisor_id>/verCursos', methods=['GET','POST'])
@login_required
def verCursos(supervisor_id):
    # Usar la funcion de verificación
    if not verify_supervisor(supervisor_id):
        flash('No tienes permiso para acceder a este dashboard. Debes ser un Supervisor.', 'danger')
        return redirect(url_for('login'))
    cursos = Curso.query.all()
    grupos=Grupo.query.all()
    if not cursos:
        flash('No existen cursos, por favor crear un curso', 'danger')
        return redirect(url_for('dashDocente',supervisor_id=supervisor_id))
    
    return render_template('verCursos.html', supervisor_id=supervisor_id, cursos=cursos, grupos=grupos)

@app.route('/dashDocente/<int:supervisor_id>/detalleCurso/<int:curso_id>', methods=['GET','POST'])
@login_required
def detallesCurso(supervisor_id, curso_id):
    curso_actual=Curso.query.get(curso_id)
    grupos=Grupo.query.filter_by(id_curso=curso_id).all()
    estudiantes_curso = Estudiante.query.filter(Estudiante.cursos.any(id=curso_id)).all()
    return(render_template('detallesCurso.html', supervisor_id=supervisor_id, curso=curso_actual, grupos=grupos, estudiantes_curso=estudiantes_curso))

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
                db.session.rollback()
                flash('Error al crear el grupo', 'danger')

            if nuevo_grupo:
                # Con los estudiantes que se seleccionaron, se asocian al grupo creado utilizando tabla asociacion estudiantes_grupos
                for estudiante_id in estudiantes_seleccionados_ids:
                    try:
                        nueva_relacion=estudiantes_grupos.insert().values(id_estudiante=estudiante_id, id_grupo=nuevo_grupo.id)
                        db.session.execute(nueva_relacion)
                        db.session.commit()
                        flash('Estudiantes asignados con éxito', 'success')
                    except Exception as e:
                        db.session.rollback()
                        flash('Error al asignar estudiantes', 'danger')
                try:
                    nuevo_registro= supervisores_grupos.insert().values(
                        id_supervisor=supervisor_id,
                        id_grupo=nuevo_grupo.id
                    )
                    db.session.execute(nuevo_registro)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    flash('Error al asignar el supervisor al grupo','danger')

    return render_template('asignarGrupos.html', supervisor_id=supervisor_id, cursos=cursos, curso_seleccionado=curso_id,estudiantes_curso=estudiantes_curso)

# boton de seleccionar todo los estudiantes 
@app.route('/dashDocente/<int:supervisor_id>/editarGrupos/<int:grupo_id>', methods = ['GET', 'POST'])
@login_required
# Falta por implementar **
def editarGrupos(supervisor_id):
    return render_template('editarGrupos.html', supervisor_id=supervisor_id)

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

# Ruta para ver el progreso de los estudiantes
@app.route('/dashDocente/<int:supervisor_id>/progresoSesion', methods=['GET', 'POST'])
@login_required
def progresoSesion(supervisor_id):
    # Ruta muestra el progreso de los estudiantes en la sesión
    # Usa la función de verificación
    if not verify_supervisor(supervisor_id):
        return redirect(url_for('login'))
    
    # Listar todos los estudiantes de la sesion
    estudiantes = Estudiante.query.all()

    return render_template('progresoSesion.html', supervisor_id=supervisor_id, estudiantes=estudiantes)



# DashBoard del estudiante. Aquí se muestran las series activas y las que ya han sido completadas
@app.route('/dashEstudiante/<int:estudiante_id>', methods=['GET', 'POST'])
@login_required
def dashEstudiante(estudiante_id):
    # Uso la funcion de verificacion
    if not verify_estudiante(estudiante_id):
        return redirect(url_for('login'))
    # Si el método es get muestra el dashBoard del Estudiante
    # estudiante= Estudiante.query.get(estudiante_id)
    estudiante = db.session.get(Estudiante, int(estudiante_id))

    # Obtiene el curso asignado al estudiante
    curso = (
        Curso.query
        .join(inscripciones)  # Join con la tabla inscripciones
        .filter(inscripciones.c.id_curso == Curso.id)
        .filter(inscripciones.c.id_estudiante == estudiante_id)
        .first()
    )
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
    return render_template('detallesSerieEstudiante.html', serie=serie, ejercicios=ejercicios, estudiante_id=estudiante_id)

@app.route('/dashEstudiante/<int:estudiante_id>/serie/<int:serie_id>/ejercicio/<int:ejercicio_id>', methods=['GET', 'POST'])
@login_required
def detallesEjerciciosEstudiantes(estudiante_id, serie_id, ejercicio_id):
    if not verify_estudiante(estudiante_id):
        return redirect(url_for('login'))

    serie = Serie.query.get(serie_id)
    ejercicio = Ejercicio.query.get(ejercicio_id)
    matricula= Estudiante.query.get(estudiante_id).matricula
    estudiante = db.session.get(Estudiante, int(estudiante_id))
    ejercicios = Ejercicio.query.filter_by(id_serie=serie_id).all()
    ejercicios_asignados = (
        Ejercicio_asignado.query
        .filter(Ejercicio_asignado.id_estudiante == estudiante_id)
        .filter(Ejercicio_asignado.id_ejercicio.in_([ejercicio.id for ejercicio in ejercicios]))
        .all()
    )

    colors_info = []

    for ejercicio_disponible in ejercicios:
        ejercicio_info = {'nombre': ejercicio_disponible.nombre, 'id': ejercicio_disponible.id, 'color': 'info'}
        
        for ejercicio_asignado in ejercicios_asignados:
            if ejercicio_disponible.id == ejercicio_asignado.id_ejercicio:
                if ejercicio_asignado.estado:
                    ejercicio_info['color'] = 'success'
                elif not ejercicio_asignado.estado and ejercicio_asignado.contador > 0:
                    ejercicio_info['color'] = 'danger'
                
        colors_info.append(ejercicio_info)

    ejercicios_aprobados = sum(1 for ea in ejercicios_asignados if ea.estado)

    total_ejercicios = len(ejercicios)
    calificacion = calcular_calificacion(total_ejercicios, ejercicios_aprobados)

    if ejercicio and ejercicio.enunciado:
        with open(ejercicio.enunciado, 'r') as enunciado_file:
            enunciado_markdown = enunciado_file.read()
            enunciado_html = markdown.markdown(enunciado_markdown)
    else:
        enunciado_html = "<p>El enunciado no está disponible.</p>"

    if request.method == 'POST':
        archivos_java = request.files.getlist('archivo_java')
        # La carpeta del ejercicio está guardada en ejerciciosPropuestos/numeroserie_nombredeserie/id_ejercicio
        rutaArchivador=None
        if not archivos_java:
            flash('Por favor, carga al menos un archivo .java.', 'danger')
            return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)        
        
        try:
            rutaArchivador = crearArchivadorEstudiante(matricula)
            #flash('Se creo exitosamente el archivador', 'success')
        except Exception as e:
            return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
        # Luego de crear la carpeta con la matricula del estudiante, se asigna el ejercicio a al estudiante en la bd
        
        if rutaArchivador:
            try:
                # Revisar si ya existe un ejercicio asignado con el estudiante_id y ejercicio_id, si no existe crearlo en la bd
                ejercicioAsignado = Ejercicio_asignado.query.filter_by(id_estudiante=estudiante_id, id_ejercicio=ejercicio.id).first()
                # flash(f'Ejercicio asignado: {ejercicioAsignado}', 'danger')
                if not ejercicioAsignado:
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
                    rutaSerieEstudiante = agregarCarpetaSerieEstudiante(rutaArchivador, serie.id, serie.nombre)
                    if rutaSerieEstudiante:
                        # Si la ruta de la serie se creo exitosamente en la carpeta del estudiante
                        # Se crea la carpeta del ejercicio dentro de la carpeta de la serie
                        rutaEjercicioEstudiante = agregarCarpetaEjercicioEstudiante(rutaSerieEstudiante, ejercicio.id,  ejercicio.path_ejercicio)
                        if os.path.exists(rutaEjercicioEstudiante):
                            # Se creó exitosamente la carpeta con el ejercicio
                            # Ahora se añaden los archivos del estudiante a la carpeta
                            for archivo_java in archivos_java:
                                rutaFinal = os.path.join(rutaEjercicioEstudiante, 'src/main/java/org/example')
                                if archivo_java and archivo_java.filename.endswith('.java'):
                                    archivo_java.save(os.path.join(rutaFinal, archivo_java.filename))
                            resultadoCompilacion = compilarProyecto(rutaEjercicioEstudiante)
                            if resultadoCompilacion:
                                # Se compiló mal el archivo
                                nuevoEjercicioAsignado.contador += 1
                                nuevoEjercicioAsignado.ultimo_envio = rutaFinal
                                nuevoEjercicioAsignado.fecha_ultimo_envio = datetime.now()
                                nuevoEjercicioAsignado.test_output = json.dumps(resultadoCompilacion) # Se debe obtener el resultado de los test unitarios o compilacion
                                nuevoEjercicioAsignado.estado = False
                                db.session.commit()
                                return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html,errores_compilacion=resultadoCompilacion, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info,calificacion=calificacion)
                            else:
                                resultadoTest = ejecutarTestUnitario(rutaEjercicioEstudiante)
                                if resultadoTest:
                                    (f'Resultados: {resultadoTest}', 'info')
                                    nuevoEjercicioAsignado.contador += 1
                                    nuevoEjercicioAsignado.ultimo_envio = rutaFinal
                                    nuevoEjercicioAsignado.fecha_ultimo_envio = datetime.now()
                                    nuevoEjercicioAsignado.test_output =  json.dumps(resultadoTest) # Se debe obtener el resultado de los test unitarios o compilacion
                                    nuevoEjercicioAsignado.estado=False
                                    db.session.commit()
                                    return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html,errores_test=resultadoTest,ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados, colors_info=colors_info, calificacion=calificacion)
                                elif resultadoTest is None:
                                    nuevoEjercicioAsignado.contador += 1
                                    nuevoEjercicioAsignado.ultimo_envio = rutaFinal
                                    nuevoEjercicioAsignado.fecha_ultimo_envio = datetime.now()
                                    nuevoEjercicioAsignado.test_output = "Todos los Test aprobados" # Se debe obtener el resultado de los test unitarios o compilacion
                                    nuevoEjercicioAsignado.estado=True
                                    flash(f'Felicitaciones, aprobaste', 'success')
                                    db.session.commit()
                                    return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html,errores_test=nuevoEjercicioAsignado.test_output, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,calificacion=calificacion, colors_info=colors_info)
                    db.session.commit()
                else:
                    # Se ocupan los datos asignados para encontrar la carpeta de la serie y ejercicio
                    rutaSerieEstudiante= agregarCarpetaSerieEstudiante(matricula, serie.id, serie.nombre)
                    if rutaSerieEstudiante:
                        # Si encuentro la ruta de la serie, creo la carpeta del ejercicio otra vez
                        rutaEjercicioEstudiante = agregarCarpetaEjercicioEstudiante(rutaSerieEstudiante, ejercicio.id, ejercicio.path_ejercicio)
                        if os.path.exists(rutaEjercicioEstudiante):
                            # Ahora se añaden los archivos del estudiante a la carpeta
                            for archivo_java in archivos_java:
                                rutaFinal = os.path.join(rutaEjercicioEstudiante, 'src/main/java/org/example')
                                if archivo_java and archivo_java.filename.endswith('.java'):
                                    archivo_java.save(os.path.join(rutaFinal, archivo_java.filename))

                            resultadoCompilacion = compilarProyecto(rutaEjercicioEstudiante)
                            if resultadoCompilacion:
                                ejercicioAsignado.contador += 1
                                ejercicioAsignado.ultimo_envio = rutaFinal
                                ejercicioAsignado.fecha_ultimo_envio = datetime.now()
                                ejercicioAsignado.test_output = json.dumps(resultadoCompilacion) # Se debe obtener el resultado de los test unitarios o compilacion
                                ejercicioAsignado.estado = False
                                db.session.commit()
                                return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html,errores_compilacion=resultadoCompilacion, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
                            else:
                                resultadoTest = ejecutarTestUnitario(rutaEjercicioEstudiante)
                                if resultadoTest:
                                    ejercicioAsignado.contador += 1
                                    ejercicioAsignado.ultimo_envio = rutaFinal
                                    ejercicioAsignado.fecha_ultimo_envio = datetime.now()
                                    ejercicioAsignado.test_output = json.dumps(resultadoTest) # Se debe obtener el resultado de los test unitarios o compilacion
                                    ejercicioAsignado.estado=False
                                    db.session.commit()
                                    return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html,errores_test=resultadoTest, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados,colors_info=colors_info, calificacion=calificacion)
                                elif resultadoTest is None:
                                    ejercicioAsignado.contador += 1
                                    ejercicioAsignado.ultimo_envio = rutaFinal
                                    ejercicioAsignado.fecha_ultimo_envio = datetime.now()
                                    ejercicioAsignado.test_output = "Todos los test aprobados" # Se debe obtener el resultado de los test unitarios o compilacion
                                    ejercicioAsignado.estado=True
                                    db.session.commit()
                                    return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html,errores_test=ejercicioAsignado.test_output, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados, colors_info=colors_info, calificacion=calificacion)
                db.session.commit() 
            except Exception as e:
                db.session.rollback()
                return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html)
            # Se crea la carpeta de el ejercicio siguiendo el mismo formato que del enunciado

    return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html, ejercicios=ejercicios, ejercicios_asignados=ejercicios_asignados, colors_info=colors_info,calificacion=calificacion)



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
# Guardar el mismo nombre para todo en ejercicio_numero_serie_numero
# Sistema de notas feedback IMPORTANTEEE
# formula para escala de notas al 50% exigencia