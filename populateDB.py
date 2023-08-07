from DBManager import db
from main import app
from datetime import date
from basedatos.modelos import Supervisor, Grupo, Serie, Estudiante, Ejercicio, Test, Supervision, Serie_asignada, Ejercicio_realizado, Comprobacion_ejercicio
with app.app_context():
    # Crea objetos y agrega registros a la base de datos
    # Crea un supervisor
    supervisor = Supervisor(nombre='ivonne', apellido_paterno='flores', apellido_materno='Roa', correo='ivonne@mail.com', password='123')
    db.session.add(supervisor)
    db.session.commit()

    # Crea un grupo
    grupo = Grupo(nombre='Grupo 1')
    db.session.add(grupo)
    db.session.commit()

    # Crea una serie
    fecha = date.fromisoformat('2023-06-21')
    serie = Serie(nombre='Serie 1', fecha=fecha)
    activa = False
    db.session.add(serie)
    db.session.commit()

    # Crea un estudiante
    estudiante = Estudiante(matricula='123456', nombre='sad', apellido_paterno='pepe', apellido_materno='sad', correo='burro@example.com', password='burrito123')
    db.session.add(estudiante)
    db.session.commit()

    # Crea un ejercicio
    ejercicio = Ejercicio(nombre='Ejercicio 2', path_ejercicio='path/ejercicio1.py', enunciado='Enunciado del ejercicio 1', id_serie=serie.id)
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
    fecha = date.fromisoformat('2023-07-21')
    ejercicio_realizado = Ejercicio_realizado(id_ejercicio=ejercicio.id, id_estudiante=estudiante.id, path='path/ejercicio_realizado1.py', fecha=fecha)
    db.session.add(ejercicio_realizado)
    db.session.commit()

    # Crea una comprobación de ejercicio
    fecha = date.fromisoformat('2023-08-21')
    comprobacion_ejercicio = Comprobacion_ejercicio(ejercicio_realizado=ejercicio_realizado.id, test=test.id, fecha=fecha, resultado='Aprobado')
    db.session.add(comprobacion_ejercicio)
    db.session.commit()
