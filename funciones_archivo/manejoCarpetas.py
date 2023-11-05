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



def crearArchivadorEstudiante(matricula):
# Funcion crea la carpeta del estudiante con la matricula para guardar sus archivos
    rutaPrincipal= 'ejerciciosPropuestos/'
    rutaEstudiante = os.path.join(rutaPrincipal, str(matricula))
    if not os.path.exists(rutaEstudiante):
        os.makedirs(rutaEstudiante)
    else:
        print("La carpeta ya existe")
    return rutaEstudiante

# Funcion para crear la carpeta del ejercicio en la carpeta de su respectiva serie.
def crear_carpeta_ejercicio(id_ejercicio, id_serie, serie_nombre):
    rutaBase = "ejerciciosPropuestos/"
    rutaSerie = os.path.join(rutaBase, f"{id_serie}_{serie_nombre}")
    # ejerciciosPropuestos/1_nombredelaserie
    nombreCarpetaEjercicio = os.path.join(rutaSerie, "Ejercicio_" + str(id_ejercicio))
    rutaEnunciados= "enunciadosEjercicios/"
    rutaFinalEnunciado = os.path.join(rutaEnunciados, "Ejercicio_" + str(id_ejercicio) )
    # Ruta donde quedará la carpeta es ejerciciosPropuestos/id_serie"_"serie_nombre/nombreCarpetaEjercicio
    
    if os.path.exists(os.path.join(rutaEnunciados, f"{id_serie}_{serie_nombre}")) | os.path.exists(nombreCarpetaEjercicio):
        return None, "La carpetas ya existen"
    
    try:
        shutil.copytree("plantillaMaven/", nombreCarpetaEjercicio)
        os.makedirs(rutaFinalEnunciado)
        return nombreCarpetaEjercicio, "Carpetas creadas con éxito"
    except Exception as e:
        return None, f"Error al crear las carpetas: {str(e)}"


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


    if not os.path.exists(rutaFinalEnunciado) |os.path.exists(rutaSerie):
        os.makedirs(rutaFinalEnunciado)
        os.makedirs(rutaSerie)
    else:
        return "La carpeta ya existe"
    
    return rutaSerie