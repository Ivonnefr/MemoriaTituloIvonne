from website import create_app
from flask import render_template, request
import subprocess

app = create_app()


@app.route('/',methods = ['GET','POST'])
def home():

    archivo =('/home/ivonne/Documentos/GitHub/MemoriaTituloIvonne/uploads/Test.java')
    compilar_java(archivo)
    


if __name__ ==  '__main__':
    app.run(debug=True)

#lsof -i:PUERTO //para revisar todos los procesos que estan usando el puerto
#kill -9 PID //para matar el proceso que esta usando el puerto

archivo =('/home/ivonne/Documentos/GitHub/MemoriaTituloIvonne/uploads/Test.java')
compilar_java(archivo)