import subprocess
import threading
import sys
import os
import datetime
from colorama import Fore, Style, init

# Inicializar colorama para visualización en terminales Windows/Linux
init(autoreset=True)

# ==========================================================
# ⚡ CONFIGURACIÓN DE ENTORNO ALPHA v3.5
# ==========================================================
# Cambia a False si necesitas volver al laboratorio con archivos CSV
MODO_LIVE = True  

# Definición de los Lóbulos del Cerebro
scripts_percepcion = [
    "lobulo_percepcion/n_talamo.py",      # Tálamo H5: Clasificador de 7 Regímenes
    "lobulo_percepcion/n_vestibular.py",  # Filtro de Ruido BTC (Equilibrio)
    "lobulo_percepcion/n_momentum.py",    # Sensor de Energía y Aceleración
    "lobulo_percepcion/n_visual.py"       # IA Visual Alpha (Cerebro H5)
]

scripts_riesgo = [
    "lobulo_riesgo/n_homeostasis.py",         # Gestión de PnL y Supervivencia
    "lobulo_riesgo/n_guardian_vestibular.py", # Veto de Ruido Inteligente
    "lobulo_riesgo/n_log_hipocampo.py"        # Grabación de Memoria Histórica
]

scripts_ejecucion = ["lobulo_ejecucion/n_ejecutor.py"]

# Selección de Sensor (Ojos) y Brazo Ejecutor (Músculos)
if MODO_LIVE:
    SENSOR = "lobulo_percepcion/mt5_feeder.py"    # Sensor de 19 Dimensiones
    BRAZO = "lobulo_ejecucion/mt5_gateway.py"     # Ejecutor Real BTCUSD
else:
    SENSOR = "lobulo_percepcion/sensor_feeder.py" # Ingesta Histórica (CSV)
    BRAZO = None                                  # Sin ejecución en simulación

# Consolidar lista de lanzamiento total
SCRIPTS_A_LANZAR = [SENSOR] + scripts_percepcion + scripts_riesgo + scripts_ejecucion
if BRAZO:
    SCRIPTS_A_LANZAR.append(BRAZO)

# ==========================================================
# 📂 GESTIÓN DE CAJA NEGRA (LOGS)
# ==========================================================
LOG_DIR = "logs_sistema"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Generamos un ID de sesión único basado en la fecha y hora de arranque
session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
MASTER_LOG_FILE = os.path.join(LOG_DIR, f"log_maestro_{'LIVE' if MODO_LIVE else 'SIM'}_{session_id}.txt")

# Mapa de colores para identificar cada lóbulo en la terminal de un vistazo
COLORES = {
    "mt5_feeder": Fore.GREEN + Style.BRIGHT,      # SENSOR
    "mt5_gateway": Fore.RED + Style.BRIGHT,        # EJECUCIÓN MT5
    "n_talamo": Fore.CYAN + Style.BRIGHT,         # CONTEXTO
    "n_visual": Fore.BLUE + Style.BRIGHT,         # INTELIGENCIA IA
    "n_homeostasis": Fore.YELLOW + Style.BRIGHT,  # RIESGO
    "n_ejecutor": Fore.MAGENTA + Style.BRIGHT,    # DECISIÓN FINAL
    "n_vestibular": Fore.WHITE + Style.DIM,       # RUIDO
}

def guardar_en_log(mensaje):
    """Escribe cada pensamiento del organismo en la Caja Negra."""
    with open(MASTER_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(mensaje + "\n")

def capturar_flujo(proceso, nombre):
    """Lee la salida estándar de cada lóbulo y la muestra con su color asignado."""
    for linea in iter(proceso.stdout.readline, b''):
        try:
            # Decodificamos la señal ignorando errores de caracteres extraños
            texto = linea.decode('utf-8', errors='replace').strip()
            if not texto: continue
            
            color = COLORES.get(nombre, Fore.WHITE)
            ts_real = datetime.datetime.now().strftime("%H:%M:%S")
            mensaje_formateado = f"[{ts_real}] [{nombre.upper()}] {texto}"
            
            # Imprimir en consola y guardar en el log maestro
            print(f"{color}{mensaje_formateado}")
            guardar_en_log(mensaje_formateado)
            
        except Exception:
            pass

def lanzar_organismo():
    """Inicializa todos los procesos del cerebro de forma independiente y paralela."""
    print(f"\n{Fore.CYAN}{'='*65}")
    print(f"{Fore.CYAN}🧠 CEREBRO TRADING ALPHA v3.5 - MODO: {'[LIVE MT5]' if MODO_LIVE else '[SIMULACIÓN CSV]'}")
    print(f"{Fore.CYAN}ESTADO: Sincronizado con 7 Regímenes y Tálamo H5")
    print(f"{Fore.CYAN}{'='*65}\n")
    print(f"{Fore.YELLOW}📂 Caja Negra activa en: {MASTER_LOG_FILE}\n")
    
    # Configuración de entorno para asegurar codificación UTF-8 en Windows Server
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = os.getcwd()

    procesos = []
    
    # Despertar cada lóbulo uno por uno
    for s in SCRIPTS_A_LANZAR:
        script_path = os.path.normcase(s)
        nombre = os.path.basename(s).replace('.py', '')
        
        try:
            # Lanzamos con '-u' para salida sin buffer (real-time logs)
            proc = subprocess.Popen(
                [sys.executable, "-u", script_path], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                env=env,
                text=False 
            )
            
            # Hilo dedicado para no bloquear el orquestador mientras leemos el lóbulo
            t = threading.Thread(target=capturar_flujo, args=(proc, nombre), daemon=True)
            t.start()
            procesos.append(proc)
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error al despertar lóbulo {nombre}: {e}")

    try:
        # El orquestador mantiene el organismo vivo esperando a que los procesos terminen
        for p in procesos:
            p.wait()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}🛑 Apagando organismo digital por orden del usuario...")
        # Protocolo de terminación segura para todos los procesos
        for p in procesos:
            p.terminate()

if __name__ == "__main__":
    lanzar_organismo()