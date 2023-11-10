import xml.etree.ElementTree as ET
import subprocess,os, re

# Recibe los datos para encontrar la ruta del reporte de pruebas unitarias
# Lee el archivo y procesa el xml, luego retorna esto en un formato entendible
def procesarSurefireReports(rutaEstudiane, nombreTest):
    # Ruta del archivo XML
    rutaArchivo = 'ejerciciosEstudiantes/'

    # Parsear el archivo XML
    tree = ET.parse(rutaArchivo)
    root = tree.getroot()

    # Obtener todas las etiquetas 'testcase'
    tests = root.findall(".//testcase")

    # Recorrer cada prueba y determinar si falló o no
    for test in tests:
        nombre_prueba = test.get('name')
        resultado_prueba = 'Aprobado' if test.find('failure') is None else 'Falló'
        print(f'La prueba "{nombre_prueba}" {resultado_prueba}.')


def ejecutarTestUnitario(matricula,rutaEjercicioEstudiante):
    comando = ['mvn','clean' ,'test']
    rutaReports= os.path.join(rutaEjercicioEstudiante, 'target/surefire-reports')
    # Ejecutar el comando utilizando subprocess y especificar el directorio de trabajo actual
    proceso = subprocess.Popen(comando, cwd=rutaEjercicioEstudiante, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proceso.wait()  # Esperar a que el proceso termine
    return 'El archivo se ejecuto los test unitarios exitosamente'

def compilarProyecto(rutaEjercicioEstudiante):
    comando = ['mvn', '-l', './mvn.log', 'clean', 'compile']

    try:
        resultado = subprocess.run(comando, cwd=rutaEjercicioEstudiante, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        salida_estandar = resultado.stdout
        salida_error = resultado.stderr

        if resultado.returncode == 0:
            log_hasta_success = leer_hasta_build_success(salida_estandar)
            return f'La compilación se realizó exitosamente.\nDetalles:\n{log_hasta_success}'
        else:
            log_hasta_failure = leer_hasta_build_failure(salida_error)
            errores_compilacion, info_errores = obtener_errores_compilacion(log_hasta_failure)
            
            return f'Error de compilación:\n{log_hasta_failure}\nDetalles:\n{errores_compilacion}\n{info_errores}'
    except Exception as e:
        return f'Error al compilar: {str(e)}'

def leer_hasta_build_success(log):
    patron = re.compile(r'([\s\S]*?)(?=\[INFO\] BUILD SUCCESS)')
    coincidencia = patron.search(log)

    if coincidencia:
        return coincidencia.group(0)
    else:
        return "No se encontró 'BUILD SUCCESS' en el log."

def leer_hasta_build_failure(log):
    patron = re.compile(r'([\s\S]*?)(?=\[ERROR\] BUILD FAILURE)')
    coincidencia = patron.search(log)

    if coincidencia:
        return coincidencia.group(0)
    else:
        return "No se encontró 'BUILD FAILURE' en el log."

def obtener_errores_compilacion(log_hasta_failure):
    # Patrón para extraer líneas entre COMPILATION ERROR y BUILD FAILURE
    patron_errores = re.compile(r'\[ERROR\] COMPILATION ERROR(.+?)\[ERROR\] BUILD FAILURE', re.DOTALL)
    coincidencia_errores = patron_errores.search(log_hasta_failure)

    if coincidencia_errores:
        errores_formateados = coincidencia_errores.group(1).strip()
        
        # Patrón para extraer la línea que contiene la cantidad de errores
        patron_info_errores = re.compile(r'\[INFO\] (\d+) error')
        coincidencia_info_errores = patron_info_errores.search(log_hasta_failure)
        cantidad_errores = coincidencia_info_errores.group(1) if coincidencia_info_errores else "0"

        return errores_formateados, f"Cantidad de errores: {cantidad_errores}"
    else:
        return "No se encontraron errores de compilación entre COMPILATION ERROR y BUILD FAILURE.", ""
 