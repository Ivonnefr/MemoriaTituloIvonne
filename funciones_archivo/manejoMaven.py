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


def ejecutarTestUnitario(matricula,ejercicio):
    ruta_base = "ejerciciosEstudiantes"
    ruta_alumno = os.path.join(ruta_base, str(matricula))
    print('compilando...')
    # Comando para ejecutar pruebas unitarias con maven
    print(ruta_alumno)
    comando = ['mvn','clean' ,'test']
    # Ejecutar el comando utilizando subprocess y especificar el directorio de trabajo actual
    subprocess.run(comando, cwd=ruta_alumno)
    print('El archivo se ejecuto los test unitarios exitosamente')
