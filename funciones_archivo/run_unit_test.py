import subprocess,os
def ejecutar_test_unitario(matricula,ejercicio):
    ruta_base = "/home/ivonne/Documentos/GitHub/MemoriaTituloIvonne/ejercicios_alumnos"
    ruta_alumno = os.path.join(ruta_base, str(matricula), str(ejercicio))
    print('compilando...')
    # Comando para ejecutar pruebas unitarias con maven
    print(ruta_alumno)
    comando = ['mvn','clean' ,'test']
    # Ejecutar el comando utilizando subprocess y especificar el directorio de trabajo actual
    subprocess.run(comando, cwd=ruta_alumno)
    print('El archivo se ejecuto los test unitarios exitosamente')
