import subprocess

# funcion para compilar archivo java
def compilar_archivo_java(archivo):
    print('compilando...')
    # Comando para compilar el archivo

    comando = f"javac {archivo}"

    try:
        print('antes de compilar')
        # Ejecutamos el comando y redirigimos la salida y errores estándar
        sp=subprocess.run(comando, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        print(sp.stderr.decode)
        print('El archivo se compiló exitosamente')

        # Si el proceso se completó correctamente, imprimimos un mensaje de éxito
        

    except subprocess.CalledProcessError as error:
        print(error.stderr)
        # Si se produce un error durante la ejecución del proceso, lo manejamos aquí
        return(f"Ocurrió un error durante la compilación: {error}")
    
