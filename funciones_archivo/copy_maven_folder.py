import os, shutil
def agregarCarpetaMavenEstudiante(matricula, numero_ejercicio):
    # Buscar la carpeta del ejercicio con el numero_ejercicio
    ruta_base = "/home/ivonne/Documentos/GitHub/MemoriaTituloIvonne/ejercicios_alumnos"
    ruta_alumno = os.path.join(ruta_base, str(matricula), str(numero_ejercicio))
    print(ruta_alumno)
    ruta_carpeta_maven = f"/home/ivonne/Documentos/GitHub/MemoriaTituloIvonne/ejercicios_propuestos/{numero_ejercicio}"
    try:
        #Si la carpeta ya existe, se elimina y se crea nuevamente
        if os.path.exists(ruta_alumno):
            shutil.rmtree(ruta_alumno)
        #si la carpeta no existe la crea
        
        shutil.copytree(ruta_carpeta_maven, ruta_alumno)
        print(f"La carpeta {ruta_carpeta_maven} se ha copiado correctamente en {ruta_alumno}")
    except FileExistsError:
        print(f"La carpeta {ruta_alumno} ya existe. No se puede copiar.")
    except Exception as e: print(e)
#funcion para crear una copia de la carpeta maven en la carpeta del alumno.
#debe recibir la matrícula del alumno y el número del ejercicio
#Se crea por primera vez la copia de la carpeta


def crear_carpeta_ejercicio(id_serie, id_ejercicio):
    # Crea una carpeta para un ejercicio dentro de su serie correspondiente
    rutaBase = "ejerciciosPropuestos/"
    rutaSerie = os.path.join(rutaBase, str(id_serie))
    rutaEjercicio = os.path.join(rutaSerie, str(id_ejercicio))

    if not os.path.exists(rutaEjercicio):
        os.makedirs(rutaEjercicio)
    return rutaEjercicio


def crear_carpeta_serie(id_serie, serie_nombre):
    # Crea una carpeta para una serie específica
    rutaBase = "ejerciciosPropuestos/"
    
    # Crear la carpeta con el formato id_nombreSerie
    nombre_carpeta = f"{id_serie}_{serie_nombre}"
    rutaSerie = os.path.join(rutaBase, nombre_carpeta)

    if not os.path.exists(rutaSerie):
        os.makedirs(rutaSerie)
    
    return rutaSerie