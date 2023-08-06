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


# Funcion para agregar la carpeta maven al ejercicio propuesto
def agregarCarpetaMavenPropuesta(numeroSerie, numeroEjercicio):
    # Usamos la carpeta plantilla como base para crear la carpeta maven del ejercicio
    rutaMaven = "plantillaMaven/"

    # La ruta base es el path relativo de ejerciciosPropuestos
    rutaBase = "ejerciciosPropuestos/"

    # Buscamos la serie a la que pertenece el numeroEjercicio, para ubicar la carpeta del ejercicio
    rutaSerie = os.path.join(rutaBase, str(numeroSerie))

    # Creamos la carpeta con el numero del ejercicio dentro de la ruta de la serie
    rutaEjercicio = os.path.join(rutaSerie, str(numeroEjercicio))

    # Verificamos si la carpeta del ejercicio ya existe, si no existe, la creamos
    if not os.path.exists(rutaEjercicio):
        os.makedirs(rutaEjercicio)

    # Copiamos el contenido de la carpeta maven en la carpeta del ejercicio
    contenido_ruta_maven = os.listdir(rutaMaven)
    for archivo in contenido_ruta_maven:
        ruta_archivo_origen = os.path.join(rutaMaven, archivo)
        ruta_archivo_destino = os.path.join(rutaEjercicio, archivo)
        shutil.copy(ruta_archivo_origen, ruta_archivo_destino)

    return rutaEjercicio
