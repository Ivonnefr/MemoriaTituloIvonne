import datetime
import subprocess
from click import DateTime
from flask import Flask, render_template, request, url_for, redirect, jsonify, session, flash
from flask_wtf import FlaskForm 
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy 
from wtforms import FileField, SubmitField, PasswordField,StringField
from werkzeug.utils import secure_filename
import os, re
from wtforms.validators import InputRequired, Length, ValidationError
from funciones_archivo.compile_java import compilar_archivo_java
from funciones_archivo.run_unit_test import ejecutar_test_unitario
from funciones_archivo.delete_packages import eliminar_packages
from funciones_archivo.copy_maven_folder import *
from funciones_archivo.add_java_file import agregar_archivo_java
from funciones_archivo.add_packages import agregar_package
from funciones_archivo.process_surefire_reports import procesar_surefire_reports
from flask_jwt_extended import JWTManager, create_access_token
from werkzeug.security import check_password_hash, generate_password_hash
from DBManager import db, init_app
from basedatos.modelos import Supervisor, Grupo, Serie, Estudiante, Ejercicio, Test, Supervision, Serie_asignada, Ejercicio_realizado, Comprobacion_ejercicio

#inicializar la aplicacion
app = Flask(__name__)
init_app(app)
jwt=JWTManager(app)
class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Upload File")

#Ruta inicio
@app.route('/'  , methods=['GET',"POST"])
def index():    
    #solo se indica el nombre porque flask sabe donde están los html
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('username')
        password = request.form.get('password')

        if not correo or not password:
            flash('El correo electrónico y la contraseña son requeridos.')
            return redirect(url_for('login'))

        user = Estudiante.query.filter_by(correo=correo).first()

        if not user or not check_password_hash(user.password, password):
            flash('Por favor revise sus datos de acceso e intente de nuevo.')
            return redirect(url_for('login'))
        
        # Crea el token de acceso
        access_token = create_access_token(identity=user.id)
        # Guarda el usuario en la sesión
        session['logged_in'] = True
        # Enviar el token en la respuesta
        return jsonify(access_token=access_token), 200

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        correo = request.form.get('username')
        password = request.form.get('password')
        
        if not correo or not password:
            flash('El correo electrónico y la contraseña son requeridos.')
            return redirect(url_for('register'))

        # Crea un nuevo usuario con la contraseña encriptada
        new_user = Estudiante(correo=correo, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        flash('Registro exitoso, ahora puede iniciar sesión.')
        return redirect(url_for('login'))

    return render_template('register.html')


#Ruta para el docente:
@app.route('/vistaDocente', methods=['GET', 'POST'])
def rutaDocente():
    #Muestra el listado de todos los ejercicios y series, botones para agregar ejercicio y serie.
    # Obtiene todas las series
    series = Serie.query.all()
    
    # Crea un diccionario donde las llaves son los id de las series y los valores son listas de ejercicios
    ejercicios_por_serie = {serie.id: [] for serie in series}
    
    # Obtiene todos los ejercicios
    ejercicios = Ejercicio.query.all()
    
    # Agrega los ejercicios a las listas correspondientes en el diccionario
    for ejercicio in ejercicios:
        ejercicios_por_serie[ejercicio.id_serie].append(ejercicio)
    
    #Si se presiona el boton de agregar serie, se muestra un formulario para agregar una serie.
    #Si se presiona el boton de agregar ejercicio, se muestra un formulario para agregar un ejercicio.
    
    #Si se presiona el boton de editar serie, se muestra un formulario para editar una serie.
    #Si se presiona el boton de editar ejercicio, se muestra un formulario para editar un ejercicio.
    #Si se presiona el boton de eliminar serie, se muestra un formulario para eliminar una serie.
    #Si se presiona el boton de eliminar ejercicio, se muestra un formulario para eliminar un ejercicio.
    return render_template('vistaDocente.html',series=series, ejercicios_por_serie=ejercicios_por_serie)

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
            return redirect(url_for('vistaDocente.agregar_serie'))  # Cambiar esto

        # Crear una nueva instancia de la Serie
        nueva_serie = Serie(nombre=nombreSerie, fecha=fecha)

        # Guardar la nueva serie en la base de datos
        db.session.add(nueva_serie)
        db.session.commit()

        # Redireccionar a '/vistaDocente' después de agregar la serie exitosamente
        return redirect(url_for('rutaDocente'))
    return render_template('agregarSerie.html')



#Ruta para agregar un ejercicio a una serie que ya existe
@app.route('/vistaDocente/agregarEjercicio', methods=['GET', 'POST'])
def agregar_ejercicio():
    #Recibe un formulario con los datos del ejercicio.

    return render_template('agregarEjercicio.html')

# Ruta para editar una serie
@app.route('/vistaDocente/editarSerie', methods=['GET', 'POST'])
def editar_serie():
    return render_template('editarSerie.html')

@app.route('/ejercicios', methods=['GET', 'POST'])
def listar_ejercicios():
    # Obtiene todas las series
    series = Serie.query.all()
    
    # Crea un diccionario donde las llaves son los id de las series y los valores son listas de ejercicios
    ejercicios_por_serie = {serie.id: [] for serie in series}
    
    # Obtiene todos los ejercicios
    ejercicios = Ejercicio.query.all()
    
    # Agrega los ejercicios a las listas correspondientes en el diccionario
    for ejercicio in ejercicios:
        ejercicios_por_serie[ejercicio.id_serie].append(ejercicio)
    
    # Devuelve la plantilla con el diccionario de ejercicios por serie
    return render_template('ejercicios.html', series=series, ejercicios_por_serie=ejercicios_por_serie)



#Ruta para subir archivo java
@app.route('/upload_file', methods=['GET',"POST"])
def upload_file():  
    form = UploadFileForm()
    if form.validate_on_submit():
        file = form.file.data # Obtengo los datos del archivo
        
        if file and file.filename.endswith('.java'): # Revisa si el archivo tiene la extesion .java
            filepath= os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))
            file.save(filepath)
            print(filepath)
            #Cuando se sube un archivo se compila y luego se quitan los packages
            #Revisar que el archivo compile exitosamente
            eliminar_packages(filepath)
            
            compilar_archivo_java(filepath)
            #luego de esto debería redireccionarme a la siguiente página que sería algo como : /upload_file/<nombre_alumno>/<pregunta>
        else:
            #Hacer esto en la misma página y no como return
            return "Tipo de archivo invalido, enviar solo archivos .java ."

        # file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))) # Then save the file
        # return "File has been uploaded."
    
    return render_template('upload_file.html', form=form)




#Ruta siguiente despues de subir el archivo, donde se muestran los resultados de aplicar los test unitarios
@app.route('/upload_file/pregunta', methods=["POST"])
def pregunta():

    return render_template('pregunta.html')




#Funcion para ejecutar el script 404
def pagina_no_encontrada(error):
    return render_template('404.html'), 404
    #return redirect(url_for('index')) #te devuelve a esa página




#Ruta para ejecutar el script
if __name__ == '__main__':
    app.register_error_handler(404, pagina_no_encontrada)
    app.run(host='0.0.0.0',debug=True, port=5000)

# #lsof -i:PUERTO //para revisar todos los procesos que estan usando el puerto
# #kill -9 PID //para matar el proceso que esta usando el puerto
#source /home/ivonne/Documentos/GitHub/MemoriaTituloIvonne/venv/bin/activate


#serie activa por grupos, asignar la serie a un grupo de estudiantes