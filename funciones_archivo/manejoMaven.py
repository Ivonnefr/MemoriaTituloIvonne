import re, os, subprocess
from ansi2html import Ansi2HTMLConverter

def ejecutarTestUnitario(rutaEjercicioEstudiante):
    comando = ['mvn', 'clean', 'test']
    resultado = subprocess.run(comando, cwd=rutaEjercicioEstudiante, capture_output=True, text=True)

    patron_success = re.compile(r'BUILD SUCCESS', re.DOTALL)
    patron_failures = re.compile(r'Failures:(.+?)BUILD FAILURE', re.DOTALL)
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
            return errores
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
                    return errores
            # Si no se cumplen ninguno de los patrones anteriores, retorna el mensaje de error
            return "Error al ejecutar pruebas unitarias"
