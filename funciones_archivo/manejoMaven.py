import xml.etree.ElementTree as ET
import subprocess,os, re

def extraerInformacionError(linea):
    # Expresión regular para extraer información específica de la línea de error
    patron = re.compile(r'/src/main/java/org/example/([^:]+):(\[\d+,\d+\]) (.+)')
    coincidencia = patron.search(linea)
    
    if coincidencia:
        nombre_archivo = coincidencia.group(1)
        fila_columna = coincidencia.group(2)
        tipo_error = coincidencia.group(3)
        return nombre_archivo, fila_columna, tipo_error
    else:
        return None

def compilarProyecto(rutaEjercicioEstudiante):
    comando = ['mvn', 'clean', 'compile']
    resultado = subprocess.run(comando, cwd=rutaEjercicioEstudiante, capture_output=True, text=True)
    
    patron = re.compile(r'COMPILATION ERROR(.+?)BUILD FAILURE', re.DOTALL)
    coincidencias = patron.finditer(resultado.stdout)
    
    if not any(coincidencias):
        print("Compilación exitosa. No se encontraron errores.")
        return
    
    for match in coincidencias:
        lineas = match.group(0).split('\n')
        
        for linea in lineas:
            if 'ERROR' in linea:
                informacion_error = extraerInformacionError(linea)
                if informacion_error:
                    nombre_archivo, fila_columna, tipo_error = informacion_error
                    print(f"Nombre del archivo: {nombre_archivo}")
                    print(f"Fila y columna: {fila_columna}")
                    print(f"Tipo de error: {tipo_error}")
                    print("------")


def ejecutarTestUnitario(rutaEjercicioEstudiante):
    





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

