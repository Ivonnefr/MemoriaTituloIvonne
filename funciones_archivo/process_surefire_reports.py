import xml.etree.ElementTree as ET
def procesar_surefire_reports():
    # Ruta del archivo XML
    ruta_archivo = '/home/ivonne/Documentos/GitHub/MemoriaTituloIvonne/ejercicios_alumnos/121234/102/target/surefire-reports/TEST-org.example.ExpendedorSimpleTest.xml'

    # Parsear el archivo XML
    tree = ET.parse(ruta_archivo)
    root = tree.getroot()

    # Obtener todas las etiquetas 'testcase'
    tests = root.findall(".//testcase")

    # Recorrer cada prueba y determinar si falló o no
    for test in tests:
        nombre_prueba = test.get('name')
        resultado_prueba = 'Aprobado' if test.find('failure') is None else 'Falló'
        print(f'La prueba "{nombre_prueba}" {resultado_prueba}.')