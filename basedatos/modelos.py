
from flask_sqlalchemy import SQLAlchemy
from main import db

class Supervisor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellido_paterno = db.Column(db.String(50), nullable=False)
    apellido_materno = db.Column(db.String(50), nullable=False)
    correo = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    
    def __init__(self, nombre, apellido_paterno, apellido_materno, correo, password):
        self.nombre = nombre
        self.apellido_paterno = apellido_paterno
        self.apellido_materno = apellido_materno
        self.correo = correo
        self.password = password
    
    
class Grupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    
    def __init__(self, nombre):
        self.nombre = nombre

class Serie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    fecha = db.Column(db.Date(), nullable=False)
    
    def __init__(self, nombre, fecha):
        self.nombre = nombre
        self.fecha = fecha

class Estudiante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    matricula = db.Column(db.String(50), nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    apellido_paterno = db.Column(db.String(50), nullable=False)
    apellido_materno = db.Column(db.String(50), nullable=False)
    correo = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    
    def __init__(self, matricula, nombre, apellido_paterno, apellido_materno, correo, password):
        self.matricula = matricula
        self.nombre = nombre
        self.apellido_paterno = apellido_paterno
        self.apellido_materno = apellido_materno
        self.correo = correo
        self.password = password

class Ejercicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    path_ejercicio = db.Column(db.String(200), nullable=False)
    enunciado = db.Column(db.String(200), nullable=False)
    id_serie = db.Column(db.Integer, db.ForeignKey('serie.id'), nullable=False)
    
    def __init__(self, nombre, path_ejercicio, enunciado, id_serie):
        self.nombre = nombre
        self.path_ejercicio = path_ejercicio
        self.enunciado = enunciado
        self.id_serie = id_serie
    
class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_ejercicio = db.Column(db.Integer, db.ForeignKey('ejercicio.id'), nullable=False)
    path_test = db.Column(db.String(200), nullable=False)
    
    def __init__(self, id_ejercicio, path_test):
        self.id_ejercicio = id_ejercicio
        self.path_test = path_test
    
    
class Supervision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_supervisor = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)
    id_grupo = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=False)
    
    def __init__(self, id_supervisor, id_grupo):
        self.id_supervisor = id_supervisor
        self.id_grupo = id_grupo

class Serie_asignada(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_serie = db.Column(db.Integer, db.ForeignKey('serie.id'), nullable=False)
    id_estudiante = db.Column(db.Integer, db.ForeignKey('estudiante.id'), nullable=False)
    
    def __init__(self, id_serie, id_estudiante):
        self.id_serie = id_serie
        self.id_estudiante = id_estudiante

class Ejercicio_realizado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_ejercicio = db.Column(db.Integer, db.ForeignKey('ejercicio.id'), nullable=False)
    id_estudiante = db.Column(db.Integer, db.ForeignKey('estudiante.id'), nullable=False)
    path = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.Date(), nullable=False)
    
    def __init__(self, id_ejercicio, id_estudiante, path, fecha):
        self.id_ejercicio = id_ejercicio
        self.id_estudiante = id_estudiante
        self.path = path
        self.fecha = fecha

class Comprobacion_ejercicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ejercicio_realizado = db.Column(db.Integer, db.ForeignKey('ejercicio_realizado.id'), nullable=False)
    test = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    fecha = db.Column(db.Date(), nullable=False)
    resultado = db.Column(db.String(50), nullable=False)
    
    def __init__(self, ejercicio_realizado, test, fecha, resultado):
        self.ejercicio_realizado = ejercicio_realizado
        self.test = test
        self.fecha = fecha
        self.resultado = resultado



