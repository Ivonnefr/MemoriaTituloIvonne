import subprocess
from flask import Flask, render_template, request, url_for, redirect
from flask_wtf import FlaskForm
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from wtforms import FileField, SubmitField, PasswordField,StringField

from werkzeug.utils import secure_filename
import os, re
from wtforms.validators import InputRequired, Length, ValidationError
from funciones_archivo.compilar import compilar_java

#inicializar la aplicacion
app = Flask(__name__)
app.config['SECRET_KEY']= 'mysecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads'


class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Upload File")

# recibe un archivo java y quita los packages utilizando RegEx
def quitar_packages(archivo_java):
    with open(archivo_java, 'r') as archivo:
        txt = archivo.read()
        x = re.sub("^package .*$", "", txt, flags=re.MULTILINE)
    with open(archivo_java, 'w') as archivo:
        archivo.write(x)
    # with open(nuevo_archivo, 'w') as nuevo:
    #     nuevo.write(x)

#Ruta inicio
@app.route('/'  , methods=['GET',"POST"])
def index():    
    #solo se indica el nombre porque flask sabe donde están los html
    return render_template('index.html')


#Ruta login
@app.route('/login', methods=['GET',"POST"])
def login():
    return render_template('login.html')

#Ruta registro
@app.route('/register', methods=['GET',"POST"])
def register():
        return render_template('register.html')

#Ruta para subir archivo java
@app.route('/upload_file', methods=['GET',"POST"])
def upload_file():  
    form = UploadFileForm()
    if form.validate_on_submit():
        file = form.file.data # Obtengo los datos del archivo
        if file and file.filename.endswith('.java'): # Revisa si el archivo tiene la extesion .java
            file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename)))
            #Cuando se sube un archivo se compila y luego se quitan los packages
            #Revisar que el archivo compile exitosamente
            compilar_java('uploads/'+file.filename)
            quitar_packages('uploads/'+file.filename)
            #luego de esto debería redireccionarme a la siguiente página que sería algo como : /upload_file/<nombre_alumno>/<pregunta>
        else:
            #Hacer esto en la misma página y no como return
            return "Tipo de archivo invalido, enviar solo archivos .java ."

        # file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))) # Then save the file
        # return "File has been uploaded."
    
    return render_template('upload_file.html', form=form)

#Ruta siguiente despues de subir el archivo, donde se muestran los resultados de aplicar los test unitarios
@app.route('/upload_file/pregunta', methods=["POST"])

#Funcion para ejecutar el script 404
def pagina_no_encontrada(error):
    return render_template('404.html'), 404
    #return redirect(url_for('index')) #te devuelve a esa página

#Ruta para ejecutar el script
if __name__ == '__main__':
    app.register_error_handler(404, pagina_no_encontrada)
    app.run(debug=True, port=5000)


# @app.route('/', methods=['GET',"POST"])
# @app.route('/home', methods=['GET',"POST"])
# def home():
#     form = UploadFileForm()
#     if form.validate_on_submit():
#         file = form.file.data # First grab the file
#         file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))) # Then save the file
#         return "File has been uploaded."
#     return render_template('home.html', form=form)

# #Ruta login
# @app.route("/<usr>")
# def user(usr):
#     return "<h1>{usr}</h1>"


# #lsof -i:PUERTO //para revisar todos los procesos que estan usando el puerto
# #kill -9 PID //para matar el proceso que esta usando el puerto
