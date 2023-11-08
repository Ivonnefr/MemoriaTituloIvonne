import re
# Recibe un archivo java y quita los packages utilizando RegEx
def eliminarPackages(archivo_java):
    with open(archivo_java, 'r') as archivo:
        txt = archivo.read()
        x = re.sub("^package .*$", "", txt, flags=re.MULTILINE)
    with open(archivo_java, 'w') as archivo:
        archivo.write(x)
    #Luego de quitar los packages se agrega la linea package org.example llamando a la funcion agregar_package
    agregarPackage(archivo_java)

# Funcion para agregar al inicio del archivo .java la siguiente linea: package org.example;
# Esto es para luego poder ejecutar test unitarios con maven
# Recibe la ruta del archivo .java
def agregarPackage(archivo_java):
    # Leer el contenido del archivo existente
    with open(archivo_java, 'r') as archivo:
        lineas = archivo.readlines()
    #Si el archivo ya incluye la linea "package org.example" no se hace nada
    if lineas[0] == "package org.example;\n":
        return
    else:
        lineas.insert(0, "package org.example;\n")
        # Escribir el contenido actualizado en el archivo
        with open(archivo_java, 'w') as archivo:
            archivo.writelines(lineas)