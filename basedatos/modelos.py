from flask_sqlalchemy import SQLAlchemy
from DBManager import db
import json

# Las tablas son para many-to-many

# Tabla de asociación entre Cursos y Estudiantes
inscripciones = db.Table('inscripciones',
    db.Column('id_estudiante', db.Integer, db.ForeignKey('estudiante.id'), primary_key=True),
    db.Column('id_curso', db.Integer, db.ForeignKey('curso.id'), primary_key=True)
)
# Tabla de asociación entre E studiantes y Grupos
estudiantes_grupos = db.Table('estudiantes_grupos',
    db.Column('id_estudiante', db.Integer, db.ForeignKey('estudiante.id'), primary_key=True),
    db.Column('id_grupo', db.Integer, db.ForeignKey('grupo.id'), primary_key=True)
)
# Tabla de asociación entre Supervisores y Grupos
supervisores_grupos = db.Table('supervisores_grupos',
    db.Column('id_supervisor', db.Integer, db.ForeignKey('supervisor.id'), primary_key=True),
    db.Column('id_grupo', db.Integer, db.ForeignKey('grupo.id'), primary_key=True)
)
# Tabla de asignación many-to-many para relacionar series y grupos
serie_asignada = db.Table('serie_asignada',
    db.Column('id_serie', db.Integer, db.ForeignKey('serie.id'), primary_key=True),
    db.Column('id_grupo', db.Integer, db.ForeignKey('grupo.id'), primary_key=True)
)

class Supervisor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombres= db.Column(db.String(200), nullable=False)
    apellidos= db.Column(db.String(200), nullable=False)
    correo = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    
    def __init__(self, nombres, apellidos, correo, password):
        self.nombres = nombres
        self.apellidos = apellidos
        self.correo = correo
        self.password = password
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return f"s{self.id}"

    
class Grupo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    curso = db.relationship('Curso', back_populates='grupos')
    estudiantes = db.relationship('Estudiante', secondary=estudiantes_grupos, back_populates='grupos')
    id_curso = db.Column(db.Integer, db.ForeignKey('curso.id'))
    def __init__(self, nombre, id_curso):
        self.nombre = nombre
        self.id_curso = id_curso

class Ejercicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    path_ejercicio = db.Column(db.String(200), nullable=False)
    enunciado = db.Column(db.String(), nullable=False)
    id_serie = db.Column(db.Integer, db.ForeignKey('serie.id'), nullable=False)
    serie = db.relationship('Serie', back_populates='ejercicios')

    def __init__(self, nombre, path_ejercicio, enunciado, id_serie):
        self.nombre = nombre
        self.path_ejercicio = path_ejercicio
        self.enunciado = enunciado
        self.id_serie = id_serie

    
class Serie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    activa = db.Column(db.Boolean(), nullable=False, default=True)
    ejercicios = db.relationship('Ejercicio', order_by=Ejercicio.id, back_populates='serie')
    
    def __init__(self, nombre, activa):
        self.nombre = nombre
        self.activa = activa


class Estudiante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    matricula = db.Column(db.String(50), nullable=False)
    nombres = db.Column(db.String(200), nullable=False)
    apellidos = db.Column(db.String(200), nullable=False)
    correo = db.Column(db.String(50), nullable=True, unique=True)
    password = db.Column(db.String(150), nullable=False)
    carrera = db.Column(db.String(100), nullable=False)
    cursos = db.relationship('Curso', secondary=inscripciones, back_populates='estudiantes')
    grupos = db.relationship('Grupo', secondary=estudiantes_grupos, back_populates='estudiantes')
    ejercicios_asignados = db.relationship('Ejercicio_asignado', back_populates='estudiante', viewonly=True)
    
    def __init__(self, matricula, nombres, apellidos, correo, password, carrera):
        self.matricula = matricula
        self.nombres = nombres
        self.apellidos = apellidos
        self.correo = correo
        self.password = password
        self.carrera = carrera
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return f"e{self.id}"
    
class Curso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    activa = db.Column(db.Boolean(), nullable=False, default=True)
    estudiantes = db.relationship('Estudiante', secondary=inscripciones, back_populates='cursos')
    grupos = db.relationship('Grupo', order_by=Grupo.id, back_populates='curso')
    
    def __init__(self, nombre, activa=activa):
        self.nombre = nombre
        self.activa = activa

class Ejercicio_asignado(db.Model):
    __table_args__ = (
        db.PrimaryKeyConstraint('id_estudiante', 'id_ejercicio'),
    )
    id_estudiante = db.Column(db.Integer, db.ForeignKey('estudiante.id'), primary_key=True)
    id_ejercicio = db.Column(db.Integer, db.ForeignKey('ejercicio.id'), primary_key=True)
    
    contador = db.Column(db.Integer, nullable=False, default=0)
    estado = db.Column(db.Boolean(), nullable=False, default=False)
    ultimo_envio = db.Column(db.String(), nullable=True)
    fecha_ultimo_envio = db.Column(db.DateTime(), nullable=True)
    test_output = db.Column(db.String(), nullable=True)

    ejercicio = db.relationship('Ejercicio', foreign_keys=[id_ejercicio], backref='ejercicios_asignados')
    estudiante = db.relationship('Estudiante', viewonly=True, lazy='joined')

    def __init__(self, id_estudiante, id_ejercicio, contador=contador, estado=estado, ultimo_envio=ultimo_envio, fecha_ultimo_envio=fecha_ultimo_envio, test_output=test_output):
        self.id_estudiante = id_estudiante
        self.id_ejercicio = id_ejercicio
        self.contador = contador
        self.estado = estado
        self.ultimo_envio = ultimo_envio
        self.fecha_ultimo_envio = fecha_ultimo_envio
        self.test_output = json.dumps(test_output)