import os, shutil
from funciones_archivo.manejoCarpetas import agregarCarpetaMavenEstudiante
def agregar_archivo_java(matricula, numero_ejercicio, archivo_java):
    #Funcion que agrega el archivo_java subido por el alumno a la carpeta con los ejercicios del alumno.
    #Recibe la matricula del alumno, el numero del ejercicio y la ruta del archivo .java
    ruta_base = "/home/ivonne/Documentos/GitHub/MemoriaTituloIvonne/ejercicios_alumnos"
    #El archivo_java debe quedar en ruta_base/src/main/java/org/example
    # El archivo_java debe quedar en ruta_base/src/main/java/org/example
    ruta_carpeta_maven = os.path.join("src", "main", "java", "org", "example")
    #La ruta especifica del alumno sería el join de la ruta_base, la matricula y el numero del ejercicio
    ruta_alumno = os.path.join(ruta_base, str(matricula), str(numero_ejercicio), ruta_carpeta_maven)
    #Se copia el archivo_java en la ruta del alumno

    try:
        shutil.copy2(archivo_java, ruta_alumno)
        print(f"El archivo {archivo_java} se ha copiado correctamente en {ruta_alumno}")
    except FileExistsError:
        print("El archivo ya existe, se va a volver a copiar")
        #Si el archivo existe, se elimina la carpeta, llamando a la funcion agregarCarpetaMavenEstudiante y se agrega el archivo_java
        agregarCarpetaMavenEstudiante(matricula, numero_ejercicio)
        shutil.copy(archivo_java, ruta_alumno)
    except Exception as e: print(e)


    
