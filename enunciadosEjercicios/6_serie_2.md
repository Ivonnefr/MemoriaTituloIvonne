# Listado 1. Data Definition Language (DDL)

Este listado de ejercicios te ayudará a practicar la sintaxis del DDL de SQL. Te recomendamos almacenar tus scripts en la plataforma de Oracle APEX a la que tienes acceso. Debes poner atención a los tipos de datos utilizados y al espacio que utilizarás para almacenar cada dato. Es ideal no asignar más espacio del estrictamente necesario a cada campo. 

## Ejercicio 1

**Sistema de Gestión de Biblioteca**

En una biblioteca universitaria, se te ha encomendado diseñar una base de datos para gestionar los libros, los préstamos y los usuarios. Debes crear las tablas necesarias con sus campos y tipos de datos correspondientes. A continuación, se presenta una descripción del sistema:

1. **Libros:**
   - Cada libro tiene un número único de identificación.
   - Se almacena el título del libro.
   - Se almacena el autor del libro.
   - Se guarda la categoría a la que pertenece el libro (por ejemplo, Ciencia Ficción, Historia, Informática, etc.).
   - Se registra la cantidad de copias disponibles en la biblioteca.

2. **Usuarios:**
   - Cada usuario tiene un número único de identificación.
   - Se almacena el nombre completo del usuario.
   - Se guarda la dirección del usuario.
   - Se guarda el correo electrónico del usuario.

3. **Préstamos:**
   - Cada préstamo tiene un número único de identificación.
   - Se almacena la fecha de inicio del préstamo.
   - Se almacena la fecha de vencimiento del préstamo.
   - Cada préstamo está relacionado con un usuario y un libro.
   - Se registra si el préstamo está activo o ha sido devuelto.

Basándote en esta descripción, diseña las tablas con sus campos y tipos de datos. Luego, escribe las sentencias SQL para crear estas tablas.

## Ejercicio 2

**Sistema de Gestión de Empleados**

En una empresa de recursos humanos, se te ha encargado diseñar una base de datos para gestionar la información de los empleados, sus departamentos y sus proyectos. Debes crear las tablas necesarias con sus campos y tipos de datos correspondientes. A continuación, se presenta una descripción del sistema:

1. **Empleados:**
   - Cada empleado tiene un número único de identificación.
   - Se almacena el nombre completo del empleado.
   - Se guarda la fecha de nacimiento del empleado.
   - Se registra el cargo o puesto del empleado en la empresa.
   - Se almacena el salario del empleado.
   - Cada empleado está asignado a un departamento.
   - Se registra si el empleado está actualmente activo en la empresa.

2. **Departamentos:**
   - Cada departamento tiene un número único de identificación.
   - Se almacena el nombre del departamento.
   - Se registra la descripción del departamento.
   - Se almacena el nombre del jefe del departamento (un empleado de la misma tabla).

3. **Proyectos:**
   - Cada proyecto tiene un número único de identificación.
   - Se almacena el nombre del proyecto.
   - Se registra la descripción del proyecto.
   - Cada proyecto está asociado a uno o varios empleados.

Basándote en esta descripción, diseña las tablas con sus campos y tipos de datos. Luego, escribe las sentencias SQL para crear estas tablas.

## Ejercicio 3

**Sistema de Gestión de Tienda de Productos**

Imagina que estás diseñando una base de datos para una pequeña tienda de productos. A continuación, se presenta una descripción del sistema:

1. **Productos:**
   - Cada producto tiene un número único de identificación.
   - Se almacena el nombre del producto.
   - Se guarda la descripción del producto.
   - Se registra el precio unitario del producto.
   - Se almacena la cantidad disponible en inventario.

2. **Clientes:**
   - Cada cliente tiene un número único de identificación.
   - Se almacena el nombre completo del cliente.
   - Se guarda la dirección del cliente.
   - Se almacena el número de teléfono del cliente.

3. **Ventas:**
   - Cada venta tiene un número único de identificación.
   - Se almacena la fecha de la venta.
   - Cada venta está asociada a un cliente.
   - Cada venta puede contener uno o varios productos vendidos.
   - Para cada producto vendido, se registra la cantidad vendida.

Basándote en esta descripción, diseña las tablas con sus campos y tipos de datos. Luego, escribe las sentencias SQL para crear estas tablas.

## Ejercicio 4

**Sistema de Gestión Judicial**

Imagina que estás diseñando una base de datos para un sistema de gestión judicial. A continuación, se presenta una descripción del sistema:

1. **Casos:**
   - Cada caso tiene un número único de identificación.
   - Se almacena el número del expediente judicial.
   - Se guarda la fecha de inicio del caso.
   - Se registra la descripción del caso.
   - Se almacena el estado actual del caso (por ejemplo, en proceso, cerrado, en apelación, etc.).

2. **Jueces:**
   - Cada juez tiene un número único de identificación.
   - Se almacena el nombre completo del juez.
   - Se guarda la especialidad judicial del juez (por ejemplo, penal, civil, laboral, etc.).

3. **Partes:**
   - Cada parte involucrada en un caso tiene un número único de identificación.
   - Se almacena el nombre completo de la parte.
   - Se guarda la dirección de la parte.
   - Se almacena el tipo de parte (demandante, demandado, tercero involucrado, etc.).

4. **Audiencias:**
   - Cada audiencia tiene un número único de identificación.
   - Se almacena la fecha y hora de la audiencia.
   - Cada audiencia está relacionada con un caso y un juez.

Basándote en esta descripción, diseña las tablas con sus campos y tipos de datos. Luego, escribe las sentencias SQL para crear estas tablas.

## Ejercicio 5

**Sistema de Gestión Pokémon**

Imagina que estás diseñando una base de datos para un sistema de gestión Pokémon. A continuación, se presenta una descripción del sistema:

1. **Pokémon:**
   - Cada Pokémon tiene un número único de identificación.
   - Se almacena el nombre del Pokémon.
   - Se registra el tipo del Pokémon (por ejemplo, Agua, Fuego, Planta, etc.).
   - Se almacena la descripción del Pokémon.
   - Se guarda la evolución previa y posterior del Pokémon (si aplica).

2. **Entrenadores:**
   - Cada entrenador tiene un número único de identificación.
   - Se almacena el nombre completo del entrenador.
   - Se guarda la edad del entrenador.
   - Se almacena la ciudad de origen del entrenador.

3. **Pokéballs:**
   - Cada Pokéball tiene un número único de identificación.
   - Se almacena el tipo de Pokéball (por ejemplo, Normal, Super, Ultra, etc.).
   - Se guarda la cantidad disponible en el inventario.

4. **Capturas:**
   - Cada captura tiene un número único de identificación.
   - Se almacena la fecha y hora de la captura.
   - Cada captura está asociada a un entrenador y un Pokémon.
   - Se registra si la captura fue exitosa o no.

Basándote en esta descripción, diseña las tablas con sus campos y tipos de datos. Luego, escribe las sentencias SQL para crear estas tablas.

## Ejercicio 6

**Sistema de Gestión Hospitalaria**

Imagina que estás diseñando una base de datos para un sistema de gestión hospitalaria. A continuación, se presenta una descripción del sistema:

1. **Pacientes:**
   - Cada paciente tiene un número único de identificación.
   - Se almacena el nombre completo del paciente.
   - Se registra la fecha de nacimiento del paciente.
   - Se guarda el género del paciente (por ejemplo, masculino, femenino, otro).
   - Se almacena la dirección del paciente.

2. **Doctores:**
   - Cada doctor tiene un número único de identificación.
   - Se almacena el nombre completo del doctor.
   - Se guarda la especialidad médica del doctor (por ejemplo, pediatra, cardiólogo, cirujano, etc.).
   - Se registra la fecha de inicio de empleo del doctor en el hospital.

3. **Habitaciones:**
   - Cada habitación tiene un número único de identificación.
   - Se almacena el tipo de habitación (por ejemplo, individual, compartida).
   - Se guarda el estado de la habitación (disponible, ocupada, en limpieza, etc.).
   - Se almacena la capacidad máxima de la habitación.

4. **Historias Clínicas:**
   - Cada historia clínica tiene un número único de identificación.
   - Se almacena la fecha de inicio de la historia clínica.
   - Cada historia clínica está asociada a un paciente y un doctor.
   - Se guarda el diagnóstico y tratamiento.

Basándote en esta descripción, diseña las tablas con sus campos y tipos de datos. Luego, escribe las sentencias SQL para crear estas tablas.

## Ejercicio 7

**Sistema de Información Astronómica**

Imagina que estás diseñando una base de datos para un sistema de información astronómica. A continuación, se presenta una descripción del sistema:

1. **Objetos Celestes:**
   - Cada objeto celeste tiene un número único de identificación.
   - Se almacena el nombre del objeto celeste (por ejemplo, estrella, planeta, galaxia, etc.).
   - Se registra la fecha de descubrimiento del objeto.
   - Se almacena la distancia desde la Tierra en años luz.
   - Se guarda una descripción del objeto celeste.

2. **Astrónomos:**
   - Cada astrónomo tiene un número único de identificación.
   - Se almacena el nombre completo del astrónomo.
   - Se guarda la especialidad de investigación del astrónomo (por ejemplo, astrofísica, cosmología, planetología, etc.).
   - Se registra la fecha de nacimiento del astrónomo.

3. **Observatorios:**
   - Cada observatorio tiene un número único de identificación.
   - Se almacena el nombre del observatorio.
   - Se guarda la ubicación geográfica del observatorio.
   - Se almacena la capacidad de observación del observatorio (por ejemplo, telescopios, radiotelescopios, etc.).

4. **Descubrimientos Astronómicos:**
   - Cada descubrimiento astronómico tiene un número único de identificación.
   - Se almacena la fecha del descubrimiento.
   - Cada descubrimiento está relacionado con un objeto celeste y un astrónomo.
   - Se guarda la descripción del descubrimiento y su relevancia científica.

Basándote en esta descripción, diseña las tablas con sus campos y tipos de datos. Luego, escribe las sentencias SQL para crear estas tablas.

## Ejercicio 8

**Sistema de Gestión Química**

Imagina que estás diseñando una base de datos para un sistema de gestión química. A continuación, se presenta una descripción del sistema:

1. **Elementos Químicos:**
   - Cada elemento químico tiene un número único de identificación (número atómico).
   - Se almacena el símbolo del elemento (por ejemplo, H para hidrógeno, O para oxígeno, etc.).
   - Se guarda el nombre completo del elemento químico.
   - Se registra la masa atómica del elemento.
   - Se almacena la clasificación del elemento (metales, no metales, metaloides, etc.).

2. **Compuestos:**
   - Cada compuesto tiene un número único de identificación.
   - Se almacena el nombre del compuesto químico.
   - Se guarda la fórmula química del compuesto.
   - Se almacena la descripción del compuesto y su uso (si aplica).
   - Se registra la fecha de descubrimiento o síntesis del compuesto.

3. **Laboratorios:**
   - Cada laboratorio tiene un número único de identificación.
   - Se almacena el nombre del laboratorio.
   - Se guarda la dirección del laboratorio.
   - Se almacena la especialización del laboratorio (por ejemplo, química orgánica, análisis de materiales, etc.).

4. **Experimentos:**
   - Cada experimento tiene un número único de identificación.
   - Se almacena la fecha del experimento.
   - Cada experimento está relacionado con un laboratorio y un compuesto químico.
   - Se guarda la descripción del experimento y los resultados obtenidos.

Basándote en esta descripción, diseña las tablas con sus campos y tipos de datos. Luego, escribe las sentencias SQL para crear estas tablas.

## Ejercicio 9

**Sistema de Gestión en Química Industrial**

Imagina que estás diseñando una base de datos para un sistema de gestión en el campo de la química industrial. A continuación, se presenta una descripción del sistema:

1. **Productos Químicos:**
   - Cada producto químico tiene un número único de identificación.
   - Se almacena el nombre del producto químico.
   - Se registra la fórmula química del producto.
   - Se guarda la descripción del producto y su aplicación industrial.
   - Se almacena la clasificación de peligrosidad del producto (por ejemplo, inflamable, tóxico, corrosivo, etc.).

2. **Procesos de Producción:**
   - Cada proceso de producción tiene un número único de identificación.
   - Se almacena el nombre del proceso químico.
   - Se guarda la descripción detallada del proceso.
   - Se almacenan los productos químicos involucrados en el proceso.
   - Se registra la fecha de inicio y finalización del proceso.

3. **Plantas Industriales:**
   - Cada planta industrial tiene un número único de identificación.
   - Se almacena el nombre de la planta.
   - Se guarda la ubicación geográfica de la planta.
   - Se almacena la capacidad de producción y los recursos disponibles en la planta.

4. **Regulaciones y Normativas:**
   - Cada regulación o normativa tiene un número único de identificación.
   - Se almacena el título de la regulación.
   - Se guarda la descripción de la regulación y su ámbito de aplicación.
   - Se registra la fecha de emisión y la autoridad emisora.

Basándote en esta descripción, diseña las tablas con sus campos y tipos de datos. Luego, escribe las sentencias SQL para crear estas tablas.

## Ejercicio 10

**Sistema de Gestión de Robots Industriales**

Imagina que estás diseñando una base de datos para un sistema de gestión de robots industriales. A continuación, se presenta una descripción del sistema:

1. **Robots Industriales:**
   - Cada robot industrial tiene un número único de identificación.
   - Se almacena el nombre del robot.
   - Se registra el fabricante del robot.
   - Se guarda la descripción de las capacidades y funciones del robot.
   - Se almacena la fecha de adquisición del robot.

2. **Tareas de Producción:**
   - Cada tarea de producción tiene un número único de identificación.
   - Se almacena la descripción detallada de la tarea.
   - Se guarda la fecha de inicio y finalización de la tarea.
   - Se registra el robot encargado de realizar la tarea.
   - Se almacena el estado de la tarea (en progreso, completada, pendiente, etc.).

3. **Operadores de Robots:**
   - Cada operador de robot tiene un número único de identificación.
   - Se almacena el nombre completo del operador.
   - Se guarda la especialización del operador en tipos de robots o tareas.
   - Se registra la fecha de contratación del operador.

4. **Mantenimiento de Robots:**
   - Cada registro de mantenimiento tiene un número único de identificación.
   - Se almacena la fecha del mantenimiento.
   - Cada mantenimiento está asociado a un robot y un operador.
   - Se guarda una descripción del mantenimiento realizado y los componentes reparados o reemplazados.

Basándote en esta descripción, diseña las tablas con sus campos y tipos de datos. Luego, escribe las sentencias SQL para crear estas tablas.

## Ejercicio 11

**Sistema de Gestión en Automotora**

Imagina que estás diseñando una base de datos para un sistema de gestión de una automotora. A continuación, se presenta una descripción del sistema:

1. **Vehículos:**
   - Cada vehículo tiene un número único de identificación.
   - Se almacena la marca del vehículo.
   - Se guarda el modelo del vehículo.
   - Se registra el año de fabricación del vehículo.
   - Se almacena el tipo de vehículo (automóvil, camioneta, motocicleta, etc.).
   - Se guarda el precio de venta del vehículo.

2. **Clientes:**
   - Cada cliente tiene un número único de identificación.
   - Se almacena el nombre completo del cliente.
   - Se guarda la dirección del cliente.
   - Se almacena el número de teléfono del cliente.
   - Se registra la fecha de registro como cliente.

3. **Vendedores:**
   - Cada vendedor tiene un número único de identificación.
   - Se almacena el nombre completo del vendedor.
   - Se guarda la dirección del vendedor.
   - Se registra la comisión por ventas del vendedor.

4. **Ventas de Vehículos:**
   - Cada venta de vehículo tiene un número único de identificación.
   - Se almacena la fecha de la venta.
   - Cada venta está asociada a un cliente y un vendedor.
   - Se guarda el vehículo vendido y su precio de venta.
   - Se registra el monto total de la venta.

Basándote en esta descripción, diseña las tablas con sus campos y tipos de datos. Luego, escribe las sentencias SQL para crear estas tablas.
