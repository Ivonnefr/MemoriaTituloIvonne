import os, shutil

def agregarCarpetaEjercicioEstudiante(rutaSerie, ejercicio_id, ejercicio_path):

    # Validar parámetros
    if not os.path.exists(rutaSerie) or not os.path.exists(ejercicio_path):
        raise ValueError("Ruta de archivador o ejercicio no válida.")

    # Crear la ruta de la carpeta del ejercicio para el estudiante
    rutaEjercicioEstudiante = os.path.join(rutaSerie, f"Ejercicio_{ejercicio_id}")

    # Verificar si la carpeta existe y eliminarla
    if os.path.exists(rutaEjercicioEstudiante):
        shutil.rmtree(rutaEjercicioEstudiante)
    # Copiar la carpeta del ejercicio al estudiante
    shutil.copytree(ejercicio_path, rutaEjercicioEstudiante)

    return rutaEjercicioEstudiante

def agregarCarpetaSerieEstudiante(matricula, serie_id, serie_nombre):
    try:
        rutaArchivador = crearArchivadorEstudiante(matricula)
        rutaSerieEstudiante = os.path.join(rutaArchivador, f"{serie_id}_{serie_nombre}")
        if os.path.exists(rutaSerieEstudiante):
            return rutaSerieEstudiante
        else:
            os.makedirs(rutaSerieEstudiante)
            return rutaSerieEstudiante
    except Exception as e:
        return f"Hubo un error al agregar la carpeta de la serie: {str(e)}"

    # Si la carpeta ya existe, simplemente devolver la ruta existente
def crearArchivadorEstudiante(matricula):
    # Función para crear la carpeta del estudiante con la matrícula para guardar sus archivos
    rutaPrincipal = 'ejerciciosEstudiantes/'
    rutaEstudiante = os.path.join(rutaPrincipal, str(matricula))

    # Verificar si la carpeta del estudiante ya existe
    if not os.path.exists(rutaEstudiante):
        os.makedirs(rutaEstudiante)

    return rutaEstudiante


# Funcion para crear la carpeta del ejercicio en la carpeta de su respectiva serie.
def crearCarpetaEjercicio(id_ejercicio, id_serie, serie_nombre):
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
def crearCarpetaSerie(id_serie, serie_nombre):
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