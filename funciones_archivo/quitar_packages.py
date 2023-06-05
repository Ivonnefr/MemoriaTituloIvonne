import re
from funciones_archivo import agregar_package
# recibe un archivo java y quita los packages utilizando RegEx
def eliminar_packages(archivo_java):
    with open(archivo_java, 'r') as archivo:
        txt = archivo.read()
        x = re.sub("^package .*$", "", txt, flags=re.MULTILINE)
    with open(archivo_java, 'w') as archivo:
        archivo.write(x)
    #Luego de quitar los packages se agrega la linea package org.example llamando a la funcion agregar_package
    agregar_package(archivo_java)