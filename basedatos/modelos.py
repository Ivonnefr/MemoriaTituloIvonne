from flask_sqlalchemy import SQLAlchemy
from DBManager import db
# Las tablas son para many-to-many

# Tabla de asociación entre Cursos y Estudiantes
inscripciones = db.Table('inscripciones',
    db.Column('id_estudiante', db.Integer, db.ForeignKey('estudiante.id'), primary_key=True),
    db.Column('id_curso', db.Integer, db.ForeignKey('curso.id'), primary_key=True)
)
# Tabla de asociación entre Estudiantes y Grupos
estudiantes_grupos = db.Table('estudiantes_grupos',
    db.Column('id_estudiante', db.Integer, db.ForeignKey('estudiante.id'), primary_key=True),
    db.Column('id_grupo', db.Integer, db.ForeignKey('grupo.id'), primary_key=True)
)
# Tabla de asociación entre Supervisores y Grupos
supervisores_grupos = db.Table('supervisores_grupos',
    db.Column('id_supervisor', db.Integer, db.ForeignKey('supervisor.id'), primary_key=True),
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
    nombre = db.Column(db.String(50), nullable=False)
    curso = db.relationship('Curso', back_populates='grupos')
    estudiantes = db.relationship('Estudiante', secondary=estudiantes_grupos, back_populates='grupos')
    id_curso = db.Column(db.Integer, db.ForeignKey('curso.id'))
    def __init__(self, nombre):
        self.nombre = nombre

class Ejercicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
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
    nombre = db.Column(db.String(50), nullable=False)
    activa = db.Column(db.Boolean(), nullable=False)
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
    
class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path_test = db.Column(db.String(200), nullable=False)
    resultado = db.Column(db.Boolean(), nullable=False) 
    id_ejercicio_realizado = db.Column(db.Integer, db.ForeignKey('ejercicio_realizado.id'), nullable=False)
    ejercicio_realizado = db.relationship('Ejercicio_realizado', back_populates='test')

    def __init__(self, id_ejercicio_realizado, path_test):
        self.id_ejercicio_realizado = id_ejercicio_realizado
        self.path_test = path_test
        self.resultado = False

    
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
    id_grupo = db.Column()
    id_estudiante = db.Column(db.Integer, db.ForeignKey('estudiante.id'), nullable=False)
    calificacion = db.Column(db.Integer, nullable=True)
    
    def __init__(self, id_serie, id_estudiante):
        self.id_serie = id_serie
        self.id_estudiante = id_estudiante

class Ejercicio_realizado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_estudiante = db.Column(db.Integer, db.ForeignKey('estudiante.id'), nullable=False)
    path = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.Date(), nullable=False)
    id_ejercicio = db.Column(db.Integer, db.ForeignKey('ejercicio.id'), nullable=False)
    test = db.relationship('Test', uselist=False, back_populates='ejercicio_realizado')
    # uselist=False indica que la relación es one-to-one
    envios = db.relationship('Envio', back_populates='ejercicio_realizado')
    #Ejercicio_realizado tiene una relación one-to-one con Test y una relación one-to-many con Envio.
    def __init__(self, id_ejercicio, id_estudiante, path, fecha):
        self.id_ejercicio = id_ejercicio
        self.id_estudiante = id_estudiante
        self.path = path
        self.fecha = fecha
    
class Curso(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    estudiantes = db.relationship('Estudiante', secondary=inscripciones, back_populates='cursos')
    grupos = db.relationship('Grupo', order_by=Grupo.id, back_populates='curso')
    def __init__(self, nombre ):
        self.nombre = nombre

class Envio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_ejercicio_realizado = db.Column(db.Integer, db.ForeignKey('ejercicio_realizado.id'), nullable=False)
    ejercicio_realizado = db.relationship('Ejercicio_realizado', back_populates='envios')
    fecha = db.Column(db.Date(), nullable=False)
    
    def __init__(self, id_ejercicio_realizado, fecha):
        self.id_ejercicio_realizado = id_ejercicio_realizado
        self.fecha = fecha