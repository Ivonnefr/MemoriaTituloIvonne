from website import create_app
from flask import render_template, request
import subprocess
app = create_app()

# funcion para compilar archivo java
def compilar_java(archivo):
    # comando para compilar archivo java
    comando = 'javac ' + archivo
    # ejecutar comando
    subprocess.call(comando, shell=True)
    print('Archivo compilado')

@app.route('/',methods = ['GET','POST'])
def home():
    #if request.method == 'POST':
        #archivo = request.form['archivo_java']
        
    #return render_template('home.html')

    #llamar a funcion compilar_java

    archivo = '/home/ivonne/Documentos/GitHub/MemoriaTituloIvonne/uploads/Test.java'
    
    compilar_java(archivo)


if __name__ ==  '__main__':
    app.run(debug=True)

archivo = '/home/ivonne/Documentos/GitHub/MemoriaTituloIvonne/uploads/Test.java'
#lsof -i:PUERTO //para revisar todos los procesos que estan usando el puerto
#kill -9 PID //para matar el proceso que esta usando el puerto

