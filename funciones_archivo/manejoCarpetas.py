import os, shutil

# Funcion para crear una copia de la carpeta maven en la carpeta del alumno.
def agregarCarpetaEjercicioEstudiante(rutaArchivador, ejercicio_id, ejercicio_nombre, ejercicio_path):
    # Si la carpeta ya existe, se elimina y se crea nuevamente
    rutaEjercicioEstudiante = os.path.join(rutaArchivador, f"Ejercicio_{ejercicio_id}_{ejercicio_nombre}")
    # Si la carpeta ya existe, seelimina el contenido y se crea nuevamente
    if os.path.exists(rutaEjercicioEstudiante):
        shutil.rmtree(rutaEjercicioEstudiante)
        os.makedirs(rutaEjercicioEstudiante)
    # Si la carpeta no existe, se crea
    else:
        os.makedirs(rutaEjercicioEstudiante)
    # Se copia la carpeta del ejercicio
    try:
        shutil.copytree(ejercicio_path, rutaEjercicioEstudiante)
        return rutaEjercicioEstudiante
    except Exception as e:
        return "Hubo un error en agregar la carpeta del ejercicio"

def agregarCarpetaSerieEstudiante(matricula, serie_id, serie_nombre):
    rutaSerieEstudiante= os.path.join("ejerciciosEstudiantes/", f"{matricula}/{serie_id}_{serie_nombre}")
    if os.path.exists(rutaSerieEstudiante):
        return rutaSerieEstudiante
    else:
        os.makedirs(rutaSerieEstudiante)
        return rutaSerieEstudiante

def crearArchivadorEstudiante(matricula):
# Funcion crea la carpeta del estudiante con la matricula para guardar sus archivos
    rutaPrincipal= 'ejerciciosEstudiantes/'
    rutaEstudiante = os.path.join(rutaPrincipal, str(matricula))
    if not os.path.exists(rutaEstudiante):
        os.makedirs(rutaEstudiante)
    else:
        return "Estudiante ya tiene su archivador"
    return rutaEstudiante

# Funcion para crear la carpeta del ejercicio en la carpeta de su respectiva serie.
def crear_carpeta_ejercicio(id_ejercicio, id_serie, serie_nombre):
    rutaBase = "ejerciciosPropuestos/"
    rutaSerie = os.path.join(rutaBase, f"{id_serie}_{serie_nombre}")
    nombreCarpetaEjercicio = os.path.join(rutaSerie, "Ejercicio_" + str(id_ejercicio))
    rutaEnunciados = os.path.join("enunciadosEjercicios/", f"{id_serie}_{serie_nombre}")
    rutaFinalEnunciado = os.path.join(rutaEnunciados, "Ejercicio_" + str(id_ejercicio))
    
    if os.path.exists(rutaFinalEnunciado) or os.path.exists(nombreCarpetaEjercicio):
        return rutaFinalEnunciado, nombreCarpetaEjercicio, "Las carpetas ya existen"
    
    try:
        shutil.copytree("plantillaMaven/", nombreCarpetaEjercicio)
        os.makedirs(rutaFinalEnunciado)
        return nombreCarpetaEjercicio, rutaFinalEnunciado, "Carpetas creadas con éxito"
    except Exception as e:
        return None, None, f"Error al crear las carpetas: {str(e)}"


# Funcion para crear la carpeta de la serie en la carpeta de ejercicios propuestos.
def crear_carpeta_serie(id_serie, serie_nombre):
    # Crea una carpeta para una serie específica
    rutaBase = "ejerciciosPropuestos/"
    rutaEnunciados= "enunciadosEjercicios/"
    nombreCarpetaEnunciados= f"{id_serie}_{serie_nombre}"

    # Crear la carpeta con el formato id_nombreSerie
    nombre_carpeta = f"{id_serie}_{serie_nombre}"
    rutaSerie = os.path.join(rutaBase, nombre_carpeta)
    rutaFinalEnunciado= os.path.join(rutaEnunciados, nombreCarpetaEnunciados)


    if not os.path.exists(rutaFinalEnunciado) or os.path.exists(rutaSerie):
        os.makedirs(rutaFinalEnunciado)
        os.makedirs(rutaSerie)
    else:
        return "La carpeta ya existe"
    
    return rutaSerie