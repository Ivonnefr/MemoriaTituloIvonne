import re,os,subprocess
from ansi2html import Ansi2HTMLConverter

def ejecutarTestUnitario(rutaEjercicioEstudiante):
    comando = ['mvn', 'clean', 'test']
    resultado = subprocess.run(comando, cwd=rutaEjercicioEstudiante, capture_output=True, text=True)
    
    patron = re.compile(r'T E S T S(.+?)BUILD FAILURE', re.DOTALL)
    coincidencias = patron.search(resultado.stdout)
    
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
    
    return None  # No hubo coincidencias


def extraerInformacionError(linea):
    # Expresión regular para extraer información específica de la línea de error
    patron = re.compile(r'/src/main/java/org/example/([^:]+):(\[\d+,\d+\]) (.+)')
    coincidencia = patron.search(linea)
    
    if coincidencia:
        nombre_archivo = coincidencia.group(1)
        fila_columna = coincidencia.group(2)
        tipo_error = coincidencia.group(3)
        return {'Error en el archivo': nombre_archivo, 'en la fila y columna': fila_columna, 'El tipo de error es': tipo_error}
    else:
        return None

def compilarProyecto(rutaEjercicioEstudiante):
    comando = ['mvn', 'clean', 'compile']
    resultado = subprocess.run(comando, cwd=rutaEjercicioEstudiante, capture_output=True, text=True)
    
    patron = re.compile(r'COMPILATION ERROR(.+?)BUILD FAILURE', re.DOTALL)
    coincidencias = patron.finditer(resultado.stdout)
    
    errores = []
    
    for match in coincidencias:
        lineas = match.group(0).split('\n')
        
        for linea in lineas:
            if 'ERROR' in linea:
                informacion_error = extraerInformacionError(linea)
                if informacion_error:
                    errores.append(informacion_error)
    
    return errores