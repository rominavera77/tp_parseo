# Trabajo Final. Materia Parseo y Generación de Código
Compilador para un Sistema de mitigación y alerta temprana en un depósito de almacenamiento de fertilizantes. 

# Objetivo

Diseñar e implementar un compilador específico de dominio (DSL - Domain Specific Language) orientado a la automatización y seguridad industrial, específicamente para el monitoreo y control de variables críticas (Temperatura, Presión y Confinamiento) en reactores o depósitos de almacenamiento de Nitrato de Amonio como fertilizante. 

# Alcance 

El lenguaje permitirá:
  * Evaluar escenarios posibles y emitir alertas.
  * Llevar un registro de la trazabilidad Industrial con la integración del módulo logging de Python estructurado por niveles de severidad (INFO      para asignaciones cotidianas, WARNING para desvíos de parámetros e interlocks y CRITICAL para emergencias graves).
  * Persistencia Física de Datos: Generación automatizada de archivos de auditoría locales en formato JSON (telemetria_reactor.json) y registros      de auditoría de alertas en formato .log (alertas_criticas_planta.log).

# Especificaciones Léxicas 

Los programas estaran delimitados por el iniciador "BEGIN" y un finalizador "END".
Contendran las palabras reservadas: 'IF': 'IF', 'THEN': 'THEN', 'TEMP': 'TEMP', 'PRESION': 'PRESION', 'CONFINADO': 'CONFINADO',
    'TRUE': 'BOOL', 'FALSE': 'BOOL'
Las constantes serán números enteros.
Los identificadores deberan contener letras de la a a la z en minúscula, mayúscula y/o '_'.
Los operadores son infijos: >, <, =. 

# Especificaciones Sintácticas
```
 <programa> ::= BEGIN <lista_sentencias> END
 <lista_sentencias> ::= <sentencia> <lista_sentencias>
                     | <sentencia>
 <sentencia> ::= TEMP '=' NUMBER
              | PRESION '=' NUMBER
              | CONFINADO '=' BOOL
              | ID '=' NUMBER
              | ID '=' BOOL
              | IF <condicion> THEN <sentencia>
 <condicion> ::= <variable_critica> '>' NUMBER
              | <variable_critica> '<' NUMBER
              | <variable_critica> '=' BOOL
 <variable_critica> ::= TEMP
                     | PRESION
                     | CONFINADO
```
                   
# Especificaciones Semánticas

El análisis semántico se realiza de forma directa sobre la tabla de símbolos (variables_entorno). El sistema evalúa tres variables críticas (TEMP, PRESION, CONFINADO) y aplica de manera estricta las siguientes reglas operativas basadas en el comportamiento químico real del Nitrato de Amonio.
