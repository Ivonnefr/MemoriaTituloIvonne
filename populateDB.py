from main import db
from basedatos.modelos import Supervisor, Grupo, Serie, Estudiante, Ejercicio, Test, Supervision, Serie_asignada, Ejercicio_realizado, Comprobacion_ejercicio


def populate_database(app, db):
    with app.app_context():
    # Crea objetos y agrega registros a la base de datos
    # Crea un supervisor
        supervisor = Supervisor(nombre='John', apellido_paterno='Doe', apellido_materno='Smith', correo='john.doe@example.com', password='password123')
        db.session.add(supervisor)
        db.session.commit()

        # Crea un grupo
        grupo = Grupo(nombre='Grupo 1')
        db.session.add(grupo)
        db.session.commit()

        # Crea una serie
        serie = Serie(nombre='Serie 1', fecha='2023-06-21')
        db.session.add(serie)
        db.session.commit()

        # Crea un estudiante
        estudiante = Estudiante(matricula='123456', nombre='Jane', apellido_paterno='Doe', apellido_materno='Smith', correo='jane.doe@example.com', password='password456')
        db.session.add(estudiante)
        db.session.commit()

        # Crea un ejercicio
        ejercicio = Ejercicio(nombre='Ejercicio 1', path_ejercicio='path/ejercicio1.py', enunciado='Enunciado del ejercicio 1', id_serie=serie.id)
        db.session.add(ejercicio)
        db.session.commit()

        # Crea un test
        test = Test(id_ejercicio=ejercicio.id, path_test='path/test1.py')
        db.session.add(test)
        db.session.commit()

        # Crea una supervisión
        supervision = Supervision(id_supervisor=supervisor.id, id_grupo=grupo.id)
        db.session.add(supervision)
        db.session.commit()

        # Crea una serie asignada
        serie_asignada = Serie_asignada(id_serie=serie.id, id_estudiante=estudiante.id)
        db.session.add(serie_asignada)
        db.session.commit()

        # Crea un ejercicio realizado
        ejercicio_realizado = Ejercicio_realizado(id_ejercicio=ejercicio.id, id_estudiante=estudiante.id, path='path/ejercicio_realizado1.py', fecha='2023-06-21')
        db.session.add(ejercicio_realizado)
        db.session.commit()

        # Crea una comprobación de ejercicio
        comprobacion_ejercicio = Comprobacion_ejercicio(ejercicio_realizado=ejercicio_realizado.id, test=test.id, fecha='2023-06-21', resultado='Aprobado')
        db.session.add(comprobacion_ejercicio)
        db.session.commit()
