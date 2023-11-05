import datetime
import os
from sqlite3 import IntegrityError
from click import DateTime
from flask import Flask, make_response, render_template, request, url_for, redirect, jsonify, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from wtforms import FileField, SubmitField, PasswordField, StringField, DateField, BooleanField, validators, FileField
from werkzeug.utils import secure_filename
from wtforms.validators import InputRequired, Length, ValidationError
from funciones_archivo.compile_java import compilar_archivo_java
from funciones_archivo.run_unit_test import ejecutar_test_unitario
from funciones_archivo.delete_packages import eliminar_packages
from funciones_archivo.manejoCarpetas import agregarCarpetaMavenEstudiante, crear_carpeta_serie, crear_carpeta_ejercicio, crearArchivadorEstudiante
from funciones_archivo.add_java_file import agregar_archivo_java
from funciones_archivo.add_packages import agregar_package
from funciones_archivo.process_surefire_reports import procesar_surefire_reports
from werkzeug.security import check_password_hash, generate_password_hash
from DBManager import db, init_app
from basedatos.modelos import Supervisor, Grupo, Serie, Estudiante, Ejercicio, Ejercicio_asignado, Curso, serie_asignada, inscripciones, estudiantes_grupos, supervisores_grupos
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
    ejercicios_por_serie = {}  # Usaremos un diccionario vacío para llenarlo con los ejericios y pasarlo al template

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
    # --->Restringir la cantidad de caracteres del enunciado<---
    # Falta agregar la opcion de recibir el archivo con el .java de los test unitarios
    # se debe guardar en: ./id_serie_nombre_serie/id_ejercicio/src/test/java/org/example
    series = Serie.query.all()
    
    if request.method == 'POST':
        nombreEjercicio = request.form.get('nombreEjercicio')
        id_serie = request.form.get('id_serie')
        enunciadoFile = request.files.get('enunciadoFile')
        serie_actual = db.session.get(Serie, int(id_serie))
        if not enunciadoFile:
            flash('Por favor, carga un archivo .md.', 'danger')
            return render_template('agregarEjercicio.html', supervisor_id=supervisor_id, series=series)

        filename = secure_filename(enunciadoFile.filename)
        nuevo_ejercicio = Ejercicio(nombre=nombreEjercicio, path_ejercicio="", enunciado="", id_serie=id_serie)
        rutaEnunciadoEjercicios = './enunciadosEjercicios'
        nuevoNombre= str(nuevo_ejercicio.id) + "ejercicio.md"
        
        filepath_ejercicio = None

        try:
            db.session.add(nuevo_ejercicio)
            db.session.flush()
            ruta_ejercicio, mensaje = crear_carpeta_ejercicio(nuevo_ejercicio.id, id_serie, serie_actual.nombre)

            if ruta_ejercicio is None:
                raise Exception(mensaje)

            filepath_ejercicio = ruta_ejercicio
            nuevoNombre = "ejercicio" + str(nuevo_ejercicio.id) + "_serie_" + str(serie_actual.id) + ".md"

            enunciadoFile.save(os.path.join(rutaEnunciadoEjercicios, nuevoNombre))

            nuevo_ejercicio.path_ejercicio = ruta_ejercicio
            nuevo_ejercicio.enunciado = os.path.join(rutaEnunciadoEjercicios, nuevoNombre)
            db.session.commit()
        except Exception as e:
            db.session.rollback()

            if filepath_ejercicio and os.path.exists(filepath_ejercicio):
                os.remove(filepath_ejercicio)

            # Si se produce un error con la base de datos después de crear la carpeta, puedes eliminarla aquí
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
    # Obtiene el supervisor asignado
    supervisor = (
        Supervisor.query
        .join(supervisores_grupos)  # Join con la tabla supervisores_grupos
        .filter(supervisores_grupos.c.id_supervisor == Supervisor.id)
        .filter(supervisores_grupos.c.id_grupo == grupo.id)  # Suponiendo que el estudiante está en un solo grupo
        .first()
    )
    # Si no se encuentra ningún grupo asignado, grupo será None
    if not grupo:
        grupo_nombre = "Ningún grupo asignado"
    else:
        grupo_nombre = grupo.nombre

    # Obtiene la serie asignada al estudiante
    # Obtiene todas las series asignadas al grupo del estudiante
    seriesAsignadas = (
        Serie.query
        .join(serie_asignada)  # Unirse a la tabla de asignación de series
        .filter(serie_asignada.c.id_grupo == grupo.id)  # Filtrar por el ID del grupo
        .all()  # Obtener todas las series asignadas al grupo
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

    # Obtén el ejercicio y su ruta de enunciado desde la base de datos
    serie = Serie.query.get(serie_id)
    ejercicio = Ejercicio.query.get(ejercicio_id)
    matricula= Estudiante.query.get(estudiante_id).matricula
    # Asegúrate de que la ruta de enunciado del ejercicio no esté vacía
    if ejercicio and ejercicio.enunciado:
        # Lee el contenido del archivo de enunciado con Python-Markdown
        with open(ejercicio.enunciado, 'r') as enunciado_file:
            enunciado_markdown = enunciado_file.read()
            # Convierte el Markdown en HTML
            enunciado_html = markdown.markdown(enunciado_markdown)
    else:
        enunciado_html = "<p>El enunciado no está disponible.</p>"

    if request.method == 'POST':
        archivos_java = request.files.getlist('archivo_java')
        # Crear la carpeta del estudiante con la serie y el ejercicio.
        # LLamar a copy_maven_folder para copiar la carpeta maven en la carpeta del estudiante
        # La carpeta del ejercicio está guardada en ejerciciosPropuestos/numeroserie_nombredeserie/id_ejercicio
        try:
            rutaArchivador = crearArchivadorEstudiante(matricula)
        except Exception as e:
            flash(f'Ocurrió un error al crear el archivador: {str(e)}', 'danger')
            return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html)

        # Luego de crear la carpeta con la matricula del estudiante, se crea la carpeta de el ejercicio siguiendo el mismo formato que del enunciado
        


        for archivo_java in archivos_java:
            if archivo_java and archivo_java.filename.endswith('.java'):
                # Guarda el archivo en una ubicación deseada
                ruta_destino = os.path.join('ruta_de_guardado', f'estudiante_{estudiante_id}', f'ejercicio_{ejercicio_id}')
                os.makedirs(ruta_destino, exist_ok=True)
                archivo_java.save(os.path.join(ruta_destino, archivo_java.filename))

    return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html)



# @app.route('/dashEstudiante/<int:estudiante_id>/serie/<int:serie_id>/ejercicio/<int:ejercicio_id>', methods=['GET', 'POST'])
# @login_required
# def detallesEjerciciosEstudiantes(estudiante_id, serie_id, ejercicio_id):
#     if not verify_estudiante(estudiante_id):
#         return redirect(url_for('login'))

#     # Obtén el ejercicio y su ruta de enunciado desde la base de datos
#     serie = Serie.query.get(serie_id)
#     ejercicio = Ejercicio.query.get(ejercicio_id)

#     # Asegúrate de que la ruta de enunciado del ejercicio no esté vacía
#     if ejercicio and ejercicio.enunciado:
#         # Lee el contenido del archivo de enunciado con Python-Markdown
#         with open(ejercicio.enunciado, 'r') as enunciado_file:
#             enunciado_markdown = enunciado_file.read()
#             # Convierte el Markdown en HTML
#             enunciado_html = markdown.markdown(enunciado_markdown)
#     else:
#         enunciado_html = "<p>El enunciado no está disponible.</p>"
#     # ---> EN QUE PARTE DEBO CREAR LA CARPETA DEL ESTUDIANTE ??????????????
#     # ---> Crearlas todas juntas de una serie cuando son asignadas por estudiante o cuando sube el archivo??

#     if request.method == 'POST':
#         # Recibo mas de un archivo...
#         archivo_java = request.files['archivo_java']
#         if archivo_java and archivo_java.filename.endswith('.java'):
#             # Guarda el archivo en una ubicación deseada
#             ruta_destino = os.path.join('ruta_de_guardado', f'estudiante_{estudiante_id}', f'ejercicio_{ejercicio_id}')
#             os.makedirs(ruta_destino, exist_ok=True)
#             archivo_java.save(os.path.join(ruta_destino, archivo_java.filename))
#             # Compilar el archivo usando funcion de compilar_archivo_java
#             compilar_archivo_java(os.path.join(ruta_destino, archivo_java.filename))
#             # Eliminar packages usando funcion de eliminar_packages
#             eliminar_packages(os.path.join(ruta_destino, archivo_java.filename))
#             # Eliminar .java

#             # Ejecutar test unitarios
#     return render_template('detallesEjerciciosEstudiante.html', serie=serie, ejercicio=ejercicio, estudiante_id=estudiante_id, enunciado=enunciado_html)

# # Ruta para subir archivo java
# @app.route('/upload_file', methods=['GET',"POST"])
# def upload_file():  
#     form = UploadFileForm()
#     if form.validate_on_submit():
#         file = form.file.data # Obtengo los datos del archivo
        
#         if file and file.filename.endswith('.java'): # Revisa si el archivo tiene la extesion .java
#             filepath= os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))
#             file.save(filepath)
#             print(filepath)
#             # Cuando se sube un archivo se compila y luego se quitan los packages
#             # Revisar que el archivo compile exitosamente
#             eliminar_packages(filepath)
            
#             compilar_archivo_java(filepath)
#             # luego de esto debería redireccionarme a la siguiente página que sería algo como : /upload_file/<nombre_alumno>/<pregunta>
#         else:
#             # Hacer esto en la misma página y no como return
#             return "Tipo de archivo invalido, enviar solo archivos .java ."

#         file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))) # Then save the file
#         return "File has been uploaded."
    
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
# ssh ivonne@pa3p2.inf.udec.cl
# mail5@udec.cl     

# Guardar el mismo nombre para todo en ejercicio_numero_serie_numero
# Viusalizacion de salida? con errores o no ?
# Sistema de notas feedback