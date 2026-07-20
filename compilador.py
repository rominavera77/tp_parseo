# =====================================================================
# SUITE DE AUTODIAGNÓSTICO INTEGRADO (TESTS LÉXICOS Y SINTÁCTICOS)
# =====================================================================
import io
import os
import json
import logging
import ply.lex as lex
import ply.yacc as yacc
import tkinter as tk
from tkinter import messagebox
import sys

# # Configuración de logs en consola para el operador
# logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
# logger = logging.getLogger("IndustrialLogger")
# =====================================================================
# CONFIGURACIÓN DEL SISTEMA DE REGISTRO EN DISCO (AUDITORÍA INDUSTRIAL)
# =====================================================================

# 1. Definir el formato estándar para el reporte de incidentes de la planta
formato_industrial = logging.Formatter(
    fmt='%(asctime)s [%(levelname)s] (MODULO_REACTOR): %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 2. Configurar el logger principal
logger = logging.getLogger("PlantaNitratoAmonio")
logger.setLevel(logging.INFO)  # Captura todo el flujo para distribuir

# 3. Manejador de Consola: Muestra toda la telemetría en tiempo real para los operadores
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formato_industrial)
logger.addHandler(console_handler)

# 4. Manejador de Archivo Físico: Guarda EXCLUSIVAMENTE alertas y fallas críticas en disco
# El modo 'a' (append) asegura que los logs no se borren al reiniciar el compilador
ruta_log_fisico = "alertas_criticas_planta.log"
file_handler = logging.FileHandler(ruta_log_fisico, mode='a', encoding='utf-8')
file_handler.setLevel(logging.WARNING)  # Filtro: Solo WARNING, ERROR y CRITICAL pasan al disco
file_handler.setFormatter(formato_industrial)
logger.addHandler(file_handler)


# =====================================================================
# ANALIZADOR LÉXICO (SCANNER)
# =====================================================================
tokens = ('ID', 'NUMBER', 'BOOL', 'EQUALS', 'LT', 'GT', 'IF', 'THEN', 'TEMP', 'PRESION', 'CONFINADO')
t_EQUALS, t_LT, t_GT = r'=', r'<', r'>'

reserved = {
    'IF': 'IF', 'THEN': 'THEN', 'TEMP': 'TEMP', 
    'PRESION': 'PRESION', 'CONFINADO': 'CONFINADO',
    'TRUE': 'BOOL', 'FALSE': 'BOOL'
}

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

t_ignore = ' \t'
def t_newline(t): r'\n+'; t.lexer.lineno += len(t.value)
def t_error(t): logger.error(f"LÉXICO: Carácter ilegal '{t.value[0]}'"); t.lexer.skip(1)

lexer = lex.lex()

# =====================================================================
# TABLA DE SÍMBOLOS Y CONTENEDOR DE ALERTAS PARA EL JSON
# =====================================================================
variables_entorno = {'TEMP': 25, 'PRESION': 1, 'CONFINADO': False}
alertas_detectadas = []  # Acá guardamos los incidentes del ciclo analizado

# =====================================================================
# ANALIZADOR SINTÁCTICO Y EVALUACIÓN SEMÁNTICA
# =====================================================================
def p_programa(p):
    '''programa : lista_sentencias'''
    pass

def p_lista_sentencias(p):
    '''lista_sentencias : sentencia lista_sentencias
                        | sentencia'''
    pass

def p_sentencia_if(p):
    '''sentencia : IF condicion THEN sentencia'''
    if p[2]:
        logger.warning("ESTRUCTURA CONDICIONAL: Interlock lógico activado.")

def p_condicion(p):
    '''condicion : variable_critica GT NUMBER
                 | variable_critica LT NUMBER
                 | variable_critica EQUALS BOOL'''
    var, op, val = p[1], p[2], p[3]
    actual = variables_entorno.get(var)
    if op == '>': p[0] = actual > val
    elif op == '<': p[0] = actual < val
    elif op == '=': p[0] = actual == (True if val == 'TRUE' else False)

def p_variable_critica(p):
    '''variable_critica : TEMP
                        | PRESION
                        | CONFINADO'''
    p[0] = p[1]

def p_sentencia_temp(p):
    '''sentencia : TEMP EQUALS NUMBER'''
    val = p[3]
    variables_entorno['TEMP'] = val
    logger.info(f"SINTÁCTICO: TEMP asignada en {val}°C.")

    # Evaluación semántica de límites críticos
    if 210 <= val < 300:
        msg = f"Temperatura crítica ({val}°C). Inicio de descomposición térmica."
        logger.warning(msg)
        alertas_detectadas.append({"nivel": "WARNING", "mensaje": msg})
        
        if variables_entorno['CONFINADO']:
            msg_critico = "Material CONFINADO a alta temperatura. Peligro de sobrepresión."
            logger.critical(msg_critico)
            alertas_detectadas.append({"nivel": "CRITICAL", "mensaje": msg_critico})
            
    elif val >= 300:
        msg_detonacion = f"Temperatura extrema ({val}°C). Superado umbral seguro en masa."
        logger.critical(msg_detonacion)
        alertas_detectadas.append({"nivel": "CRITICAL", "mensaje": msg_detonacion})

def p_sentencia_presion(p):
    '''sentencia : PRESION EQUALS NUMBER'''
    val = p[3]
    variables_entorno['PRESION'] = val
    logger.info(f"SINTÁCTICO: PRESION asignada en {val} atm.")

    if val > 5 and variables_entorno['TEMP'] > 150:
        msg = f"Alta presión ({val} atm) combinada con calor incrementa el índice de riesgo."
        logger.warning(msg)
        alertas_detectadas.append({"nivel": "WARNING", "mensaje": msg})

def p_sentencia_confinado(p):
    '''sentencia : CONFINADO EQUALS BOOL'''
    estado = (p[3] == 'TRUE')
    variables_entorno['CONFINADO'] = estado
    logger.info(f"SINTÁCTICO: Estado CONFINADO modificado a {estado}.")

def p_error(p): logger.error("SINTÁCTICO: Error de sintaxis en la entrada.")

parser = yacc.yacc(write_tables=False, debug=False)

# =====================================================================
# FUNCIÓN DE TRADUCCIÓN EXPORTADORA A JSON
# =====================================================================
def generar_archivo_telemetria(ruta_destino="telemetria_reactor.json"):
    """Compila el estado actual y las alertas en un formato JSON estandarizado."""
    payload = {
        "origen": "Compilador_Industrial_Nitrato_Amonio",
        "estado_variables": variables_entorno,
        "alertas": alertas_detectadas,
        "requiere_accion_inmediata": any(a["nivel"] == "CRITICAL" for a in alertas_detectadas)
    }
    
    # Escritura del archivo físico en disco
    with open(ruta_destino, 'w', encoding='utf-8') as archivo:
        json.dump(payload, archivo, indent=4, ensure_ascii=False)
    
    print(f"\n[ÉXITO] Archivo JSON generado correctamente en: '{ruta_destino}'")

def mostrar_pantalla_control(estado_variables, alertas):
    """Genera una interfaz visual representativa del estado del reactor."""
    # Crear la ventana principal
    ventana = tk.Tk()
    ventana.title("HMI - Panel de Monitoreo de Nitrato de Amonio")
    ventana.geometry("450x300")
    ventana.configure(bg="#2c3e50")

    # Determinar el color del panel según la gravedad del riesgo
    tiene_critico = any(a["nivel"] == "CRITICAL" for a in alertas)
    tiene_warning = any(a["nivel"] == "WARNING" for a in alertas)
    
    if tiene_critico:
        color_estado = "#e74c3c"  # Rojo
        texto_estado = "🚨 ESTADO: PELIGRO CRÍTICO 🚨"
    elif tiene_warning:
        color_estado = "#f1c40f"  # Amarillo
        texto_estado = "⚠️ ESTADO: ADVERTENCIA OPERATIVA ⚠️"
    else:
        color_estado = "#2ecc71"  # Verde
        texto_estado = "✅ ESTADO: OPERACIÓN SEGURA ✅"

    # Encabezado del Reactor
    lbl_titulo = tk.Label(ventana, text="REACTOR DE FERTILIZANTES - PABELLÓN B", 
                          fg="white", bg="#34495e", font=("Arial", 12, "bold"), pady=10)
    lbl_titulo.pack(fill=tk.X)

    # Indicador Visual de Alerta (Cambia de color dinámicamente)
    lbl_status = tk.Label(ventana, text=texto_estado, fg="black", bg=color_estado, 
                          font=("Arial", 11, "bold"), pady=8)
    lbl_status.pack(fill=tk.X, pady=10)

    # Marco de Datos de Telemetría
    marco_datos = tk.Frame(ventana, bg="#2c3e50")
    marco_datos.pack(pady=10)

    font_datos = ("Arial", 11)
    tk.Label(marco_datos, text=f"Temperatura Actual: {estado_variables['TEMP']} °C", fg="white", bg="#2c3e50", font=font_datos).pack(anchor="w")
    tk.Label(marco_datos, text=f"Presión del Sistema: {estado_variables['PRESION']} atm", fg="white", bg="#2c3e50", font=font_datos).pack(anchor="w")
    
    estado_confinamiento = "CERRADO (CONFINADO)" if estado_variables['CONFINADO'] else "ABIERTO (VENTILADO)"
    tk.Label(marco_datos, text=f"Estado de Válvulas: {estado_confinamiento}", fg="white", bg="#2c3e50", font=font_datos).pack(anchor="w")

    # Botón de Reconocimiento del Operador
    btn_cerrar = tk.Button(ventana, text="Reconocer Alerta / Cerrar Panel", command=ventana.destroy, 
                           bg="#34495e", fg="white", font=("Arial", 10, "bold"), padx=10, pady=5)
    btn_cerrar.pack(side=tk.BOTTOM, pady=15)

    # Ejecutar el bucle de la interfaz gráfica
    ventana.mainloop()

# --- EJECUCIÓN DEL FLUJO ---
if __name__ == '__main__':
    data_telemetria = '''
    TEMP = 120
    CONFINADO = TRUE
    IF TEMP > 200 THEN PRESION = 8
    '''
    
def ejecutar_autodiagnostico():
    print("\n" + "="*60)
    logger.info("⚙️  INICIANDO AUTODIAGNÓSTICO INTERNO DEL COMPILADOR...")
    print("="*60)
    
    pruebas_pasadas = 0
    total_pruebas = 5

    # Función auxiliar para aislar y capturar logs en memoria
    def simular_analisis(codigo):
        log_capture = io.StringIO()
        handler_test = logging.StreamHandler(log_capture)
        logger.addHandler(handler_test)
        
        # Reset de estados previos
        lexer.lineno = 1
        variables_entorno.clear()
        variables_entorno.update({'TEMP': 25, 'PRESION': 1, 'CONFINADO': False})
        alertas_detectadas.clear()
        
        # Ejecución
        parser.parse(codigo)
        
        logger.removeHandler(handler_test)
        return log_capture.getvalue()

    # --- TEST 1: Reconocimiento Léxico de Tokens ---
    print("--- TEST 1: Reconocimiento Léxico de Tokens ---")
    try:
        lexer.lineno = 1
        lexer.input("TEMP PRESION CONFINADO TRUE IF THEN 300 = < >")
        tokens_obtenidos = []
        while True:
            tok = lexer.token()
            if not tok: break
            tokens_obtenidos.append(tok.type)
        
        esperados = ['TEMP', 'PRESION', 'CONFINADO', 'BOOL', 'IF', 'THEN', 'NUMBER', 'EQUALS', 'LT', 'GT']
        assert tokens_obtenidos == esperados, f"Tokens erróneos: {tokens_obtenidos}"
        logger.info("  [OK] Test Léxico: Secuencia de tokens e identificadores válida.")
        pruebas_pasadas += 1
    except Exception as e:
        logger.error(f"  [FALLO] Test Léxico: {e}")

    # --- TEST 2: Filtrado de Caracteres Ilegales ---
    print("--- TEST 2: Filtrado de Caracteres Ilegales ---")
    logs = simular_analisis("TEMP = 100 $")
    if "LÉXICO: Carácter ilegal" in logs:
        logger.info("  [OK] Test Léxico: Detección correcta de caracteres prohibidos ($).")
        pruebas_pasadas += 1
    else:
        logger.error("  [FALLO] Test Léxico: El scanner no reportó el carácter ilegal '$'.")

    # --- TEST 3: Sintaxis de Asignaciones y Estructura Gramatical ---
    print("--- TEST 3: Sintaxis de Asignaciones y Estructura Gramatical ---")
    logs = simular_analisis("TEMP = 220\nPRESION = 4\nCONFINADO = TRUE")
    if "SINTÁCTICO: Error de sintaxis" not in logs:
        logger.info("  [OK] Test Sintáctico: Estructura de sentencias secuenciales aprobada.")
        pruebas_pasadas += 1
    else:
        logger.error("  [FALLO] Test Sintáctico: Error al procesar asignaciones válidas.")

    # --- TEST 4: Sintaxis del Bloque Condicional Complejo ---
    print("--- TEST 4: Sintaxis del Bloque Condicional Complejo ---")   
    logs = simular_analisis("IF TEMP > 200 THEN PRESION = 6")
    if "SINTÁCTICO: Error de sintaxis" not in logs:
        logger.info("  [OK] Test Sintáctico: Gramática de control IF-THEN aprobada.")
        pruebas_pasadas += 1
    else:
        logger.error("  [FALLO] Test Sintáctico: La estructura IF-THEN generó un falso error.")

    # --- TEST 5: Rechazo de Sintaxis Truncada o Incompleta ---
    print("--- TEST 5: Rechazo de Sintaxis Truncada o Incompleta ---")
    logs = simular_analisis("IF TEMP > 200 THEN")
    if "SINTÁCTICO: Error de sintaxis" in logs:
        logger.info("  [OK] Test Sintáctico: Rechazo correcto de bloque condicional trunco.")
        pruebas_pasadas += 1
    else:
        logger.error("  [FALLO] Test Sintáctico: El parser aceptó una sentencia incompleta.")

    # --- DIAGNÓSTICO FINAL ---
    print("-" * 60)
    if pruebas_pasadas == total_pruebas:
        logger.info(f"✅ CONTROL DE CALIDAD EXITOSO: {pruebas_pasadas}/{total_pruebas} pruebas sintácticas/léxicas pasadas.")
        print("="*60 + "\n")
        return True
    else:
        logger.error(f"❌ COMPILADOR CORRUPTO: Solo pasaron {pruebas_pasadas}/{total_pruebas} pruebas. Abortando inicio.")
        print("="*60 + "\n")
        return False


# =====================================================================
# ORQUESTACIÓN PRINCIPAL DEL ENTORNO INDUSTRIAL
# =====================================================================
if __name__ == '__main__':
    
    # 1. Ejecutar las pruebas internas automáticas antes de interactuar con la planta
    if ejecutar_autodiagnostico():
        
        # Función auxiliar para limpiar el reactor entre simulaciones
        def reiniciar_reactor():
            variables_entorno.clear()
            variables_entorno.update({'TEMP': 25, 'PRESION': 1, 'CONFINADO': False})
            alertas_detectadas.clear()
            lexer.lineno = 1

        # ESCENARIO 1: OPERACIÓN ESTABLE EN PLANTA
        reiniciar_reactor()
        escenario_1 = '''
        TEMP = 150
        PRESION = 3
        CONFINADO = FALSE
        IF TEMP > 200 THEN PRESION = 9
        '''
        logger.info("====== INICIANDO ESCENARIO 1: OPERACIÓN NORMAL ======")
        parser.parse(escenario_1)
        generar_archivo_telemetria()
        mostrar_pantalla_control(variables_entorno, alertas_detectadas)
        
        input("\n[PAUSA] Presioná Enter para pasar al Escenario 2 (Alerta Amarilla)...")

        # ESCENARIO 2: DESCOMPOSICIÓN TÉRMICA SIN CONFINAMIENTO
        reiniciar_reactor()
        escenario_2 = '''
        CONFINADO = FALSE
        TEMP = 230
        PRESION = 2
        '''
        logger.info("====== INICIANDO ESCENARIO 2: ALERTA DE DESCOMPOSICIÓN ======")
        parser.parse(escenario_2)
        generar_archivo_telemetria()
        mostrar_pantalla_control(variables_entorno, alertas_detectadas)
        
        input("\n[PAUSA] Presioná Enter para pasar al Escenario 3 (Interlock Crítico)...")

        # ESCENARIO 3: INTERLOCK SEVERO POR SOFTWARE
        reiniciar_reactor()
        escenario_3 = '''
        CONFINADO = TRUE
        TEMP = 245
        IF TEMP > 200 THEN PRESION = 8
        '''
        logger.info("====== INICIANDO ESCENARIO 3: INTERLOCK AUTOMÁTICO ACTIVO ======")
        parser.parse(escenario_3)
        generar_archivo_telemetria()
        mostrar_pantalla_control(variables_entorno, alertas_detectadas)
        
        input("\n[PAUSA] Presioná Enter para pasar al Escenario 4 (Peligro Máximo)...")

        # ESCENARIO 4: SITUACIÓN DE RIESGO CRÍTICO EN MASA
        reiniciar_reactor()
        escenario_4 = '''
        TEMP = 315
        PRESION = 4
        '''
        logger.info("====== INICIANDO ESCENARIO 4: UMBRAL CRÍTICO ABSOLUTO ======")
        parser.parse(escenario_4)
        generar_archivo_telemetria()
        mostrar_pantalla_control(variables_entorno, alertas_detectadas)

        logger.info("====== TODOS LOS ESCENARIOS DE TELEMETRÍA FUERON PROBADOS CON ÉXITO ======")
