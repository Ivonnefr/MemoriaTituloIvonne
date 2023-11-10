import xml.etree.ElementTree as ET
import subprocess,os

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
    # Comando para ejecutar pruebas unitarias con Maven
    comando = ['mvn','-l', './mvn.log','clean', 'compile']
    
    try:
        # Ejecutar el comando utilizando subprocess y capturar la salida estándar y de error
        resultado = subprocess.run(comando, cwd=rutaEjercicioEstudiante, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        salida_estandar = resultado.stdout 
        salida_error = resultado.stderr # Ocupar esto para procesar los erroress

        if resultado.returncode == 0:
            # La compilación tuvo éxito
            return f'La compilación se realizó exitosamente.\nSalida estándar:\n{salida_estandar}'
        else:
            # La compilación falló, devuelve la salida de error
            return f'Error de compilación:\n{salida_error}'
    except Exception as e:
        # Manejar excepciones si ocurren problemas al ejecutar el comando
        return f'Error al compilar: {str(e)}'
    
# Funcion para procesar los resultados de la compilacion
#def procesarCompilacion():