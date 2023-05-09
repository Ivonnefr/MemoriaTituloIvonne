
import subprocess

# funcion para compilar archivo java
def compilar_java(archivo):
    print('compilando...')
    # Comando para compilar el archivo
    comando = f"javac {archivo}"

    try:
        print('antes de compilar')
        # Ejecutamos el comando y redirigimos la salida y errores estándar
        subprocess.run(comando, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        print('despues de compilar')
        # Imprimimos la salida y errores del compilador
        #print(resultado.stdout.decode())
        #print(resultado.stderr.decode())

        # Si el proceso se completó correctamente, imprimimos un mensaje de éxito
        return("El archivo se compiló exitosamente")

    except subprocess.CalledProcessError as error:
        # Si se produce un error durante la ejecución del proceso, lo manejamos aquí
        return(f"Ocurrió un error durante la compilación: {error}")
