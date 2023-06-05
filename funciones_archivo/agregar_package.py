import re
#funcion para agregar al inicio del archivo .java la siguiente linea: package org.example;
#esto es para luego poder ejecutar test unitarios con maven
#recibe la ruta del archivo .java
def agregar_package(archivo_java):
    # Leer el contenido del archivo existente
    with open(archivo_java, 'r') as archivo:
        lineas = archivo.readlines()

    # Insertar la nueva línea en la posición correcta
    lineas.insert(0, "package org.example\n")

    # Escribir el contenido actualizado en el archivo
    with open(archivo_java, 'w') as archivo:
        archivo.writelines(lineas)
