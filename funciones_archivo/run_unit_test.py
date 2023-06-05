import subprocess

def ejecutar_test_unitario(ruta):
    print('compilando...')
    # Comando para ejecutar pruebas unitarias con maven
    
    comando = f"mvn clean test -f"

    try:
        print('antes...')
        # Ejecutamos el comando y redirigimos la salida y errores estándar
        sp=subprocess.run(comando, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        print(sp.stderr.decode)
        print('El archivo se ejecutó exitosamente')

        # Si el proceso se completó correctamente, imprimimos un mensaje de éxito
        

    except subprocess.CalledProcessError as error:
        print(error.stderr)
        # Si se produce un error durante la ejecución del proceso, lo manejamos aquí
        return(f"Ocurrió un error durante la compilación: {error}")
    
