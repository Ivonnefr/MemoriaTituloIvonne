from website import create_app
from flask import render_template, request
import subprocess
from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
import os
from wtforms.validators import InputRequired

#inicializar la aplicacion
app = Flask(__name__)

@app.route('/')
def index():    
    #solo se indica el nombre porque flask sabe donde están los html
    return render_template('index.html')




if __name__ == '__main__':
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
