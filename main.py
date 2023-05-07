import subprocess
from flask import Flask, render_template, request, url_for, redirect
from flask_wtf import FlaskForm
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from wtforms import FileField, SubmitField, PasswordField,StringField

from werkzeug.utils import secure_filename
import os
from wtforms.validators import InputRequired, Length, ValidationError

#inicializar la aplicacion
app = Flask(__name__)

app.config['SECRET_KEY']= 'mysecretkey'

# class RegisterForm(FlaskForm):
#     username = StringField(validators=[InputRequired(), Length(min=4, max=15)], render_kw={"placeholder": "Username"})
#     password = PasswordField(validators=[InputRequired(), Length(min=8, max=80)], render_kw={"placeholder": "Password"})
#     submit = SubmitField("Register")
#     def validate_username(self, username):
#         existing_user_username = User.query.filter_by(username=username.data).first()
#         if existing_user_username:
#             raise ValidationError("That username already exists. Please choose a different one.")
    

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


@app.route("/<usr>")
def user(usr):
    return "<h1>{usr}</h1>"

def pagina_no_encontrada(error):
    return render_template('404.html'), 404
    #return redirect(url_for('index')) te devuelve a esa página

if __name__ == '__main__':
    app.register_error_handler(404, pagina_no_encontrada)
    app.run(debug=True, port=5000)


# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'supersecretkey'
# app.config['UPLOAD_FOLDER'] = 'static/files'

# class UploadFileForm(FlaskForm):
#     file = FileField("File", validators=[InputRequired()])
#     submit = SubmitField("Upload File")

# @app.route('/', methods=['GET',"POST"])
# @app.route('/home', methods=['GET',"POST"])
# def home():
#     form = UploadFileForm()
#     if form.validate_on_submit():
#         file = form.file.data # First grab the file
#         file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))) # Then save the file
#         return "File has been uploaded."
#     return render_template('home.html', form=form)

# if __name__ == '__main__':
#     app.run(debug=True)

# @app.route('/upload_file', methods=['GET',"POST"])
# def upload_file():
#     if request.method == 'POST':
#         file = request.files['file']
#         file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename)))
#         return "File has been uploaded."
#     return render_template('website/templates/upload_file.html')



# #lsof -i:PUERTO //para revisar todos los procesos que estan usando el puerto
# #kill -9 PID //para matar el proceso que esta usando el puerto
