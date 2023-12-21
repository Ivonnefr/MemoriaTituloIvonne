import re, os, subprocess
from ansi2html import Ansi2HTMLConverter
from bs4 import BeautifulSoup

def ejecutarTestUnitario(rutaEjercicioEstudiante):
    comando = ['mvn', 'clean', 'test']
    resultado = subprocess.run(comando, cwd=rutaEjercicioEstudiante, capture_output=True, text=True)

    patron_success = re.compile(r'BUILD SUCCESS', re.DOTALL)
    patron_failures = re.compile(r'Results:(.+?)BUILD FAILURE', re.DOTALL)
    patron_comp = re.compile(r'COMPILATION ERROR(.+?)BUILD FAILURE', re.DOTALL)
    patron_compile = re.compile(r'BUILD FAILURE(.+?)Help 1', re.DOTALL)
    
    coincidencias = patron_success.search(resultado.stdout)
    if coincidencias:
        return 'BUILD SUCCESS'
    else:
        coincidencias = patron_failures.search(resultado.stdout)
        if coincidencias:
            lineas_test = coincidencias.group(1).split('\n')
            converter = Ansi2HTMLConverter()
            errores = []
            for linea in lineas_test:
                if 'ERROR' in linea:
                    # Filtra los códigos ANSI y agrega la línea limpia
                    linea_limpia = converter.convert(linea, full=False)
                    errores.append(linea_limpia)
            errores_sin_error_tag = eliminar_error(errores)
            errores_negrita= agregar_negrita(errores_sin_error_tag)
            return errores_negrita
        else:
            if patron_comp.search(resultado.stdout):
                coincidencias = patron_compile.search(resultado.stdout)
                if coincidencias:
                    lineas_test = coincidencias.group(1).split('\n')
                    converter = Ansi2HTMLConverter()
                    errores = []
                    for linea in lineas_test:
                        if 'ERROR' in linea:
                            # Filtra los códigos ANSI y agrega la línea limpia
                            linea_limpia = converter.convert(linea, full=False)
                            errores.append(linea_limpia)
                    errores_sin_error_tag = eliminar_error(errores)
                    return errores_sin_error_tag
            
            # Si no se cumplen ninguno de los patrones anteriores, retorna el mensaje de error
            return "Error al ejecutar pruebas unitarias"
        

def eliminar_error(html_lines):
    # Crear una lista para almacenar las líneas después de eliminar [ERROR]
    lines_sin_error = []

    # Iterar sobre cada línea HTML
    for linea_html in html_lines:
        # Crear un objeto BeautifulSoup para analizar la línea HTML
        soup = BeautifulSoup(linea_html, 'html.parser')

        # Encontrar y eliminar todas las instancias de la etiqueta <span> que contiene "ERROR"
        for span_error in soup.find_all('span', string='ERROR'):
            span_error.decompose()

        # Eliminar corchetes restantes
        linea_modificada = str(soup).replace('[', '').replace(']', '')

        # Agregar la línea modificada a la lista
        lines_sin_error.append(linea_modificada)

    return lines_sin_error

def agregar_negrita(html_lines):
    # Crear una lista para almacenar las líneas después de agregar negrita
    lines_con_negrita = []

    # Iterar sobre cada línea HTML
    for linea_html in html_lines:
        # Buscar las posiciones de las flechas en la línea
        indice_flechas = linea_html.find('»')

        # Si hay flechas, agregar negrita después de ellas
        if indice_flechas != -1:
            # Insertar <strong> después de las flechas
            nueva_linea = f"{linea_html[:indice_flechas + 1]}<strong>{linea_html[indice_flechas + 1:]}</strong>"

            # Agregar la línea modificada a la lista
            lines_con_negrita.append(nueva_linea)
        else:
            # Si no hay flechas, mantener la línea sin cambios
            lines_con_negrita.append(linea_html)
    final=agregar_negrita_despues_flechas(lines_con_negrita)
    return final

def agregar_negrita_despues_flechas(html_lines):
    # Crear una lista para almacenar las líneas después de agregar negrita
    lines_con_negrita = []

    # Iterar sobre cada línea HTML
    for linea_html in html_lines:
        # Crear un objeto BeautifulSoup para analizar la línea HTML
        soup = BeautifulSoup(linea_html, 'html.parser')

        # Encontrar la flecha "==> " en la línea
        flecha = soup.find(string=lambda s: '==>' in s)

        # Si se encuentra la flecha, agregar negrita solo al texto antes de la flecha
        if flecha:
            # Obtener el texto antes y después de la flecha
            texto_antes_flecha = flecha.split('==>')[0]
            texto_despues_flecha = flecha.split('==>')[1]

            # Crear una nueva etiqueta <b> y agregar el texto antes de la flecha
            nueva_etiqueta = soup.new_tag('b')
            nueva_etiqueta.string = texto_antes_flecha

            # Insertar la nueva etiqueta antes de la flecha
            flecha.insert_before(nueva_etiqueta)

            # Reemplazar la flecha con el texto después de la flecha
            flecha.replace_with(texto_despues_flecha)
        
        # Agregar la línea modificada a la lista
        lines_con_negrita.append(str(soup))

    return lines_con_negrita
