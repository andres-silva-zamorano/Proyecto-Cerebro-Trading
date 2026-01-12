import subprocess
import threading
import sys
import os
import datetime
from colorama import Fore, Style, init

init(autoreset=True)

# ==========================================================
# ⚡ CONFIGURACIÓN DE ENTORNO ALPHA
# ==========================================================
MODO_LIVE = True  # Cambia a False para volver a simulación por CSV

# Diccionario de scripts según el modo
scripts_percepcion = [
    "lobulo_percepcion/n_talamo.py",
    "lobulo_percepcion/n_vestibular.py",
    "lobulo_percepcion/n_momentum.py",
    "lobulo_percepcion/n_visual.py"
]

scripts_riesgo = [
    "lobulo_riesgo/n_homeostasis.py",
    "lobulo_riesgo/n_guardian_vestibular.py",
    "lobulo_riesgo/n_log_hipocampo.py"
]

scripts_ejecucion = ["lobulo_ejecucion/n_ejecutor.py"]

# Selección de Sensor y Brazo Ejecutor
if MODO_LIVE:
    SENSOR = "lobulo_percepcion/mt5_feeder.py"    # Sensor Polars/Wilder MT5
    BRAZO = "lobulo_ejecucion/mt5_gateway.py"     # Ejecutor Real MT5
else:
    SENSOR = "lobulo_percepcion/sensor_feeder.py" # Sensor de Laboratorio CSV
    BRAZO = None                                  # En simulación no hay Gateway real

# Consolidar lista de lanzamiento
SCRIPTS_A_LANZAR = [SENSOR] + scripts_percepcion + scripts_riesgo + scripts_ejecucion
if BRAZO:
    SCRIPTS_A_LANZAR.append(BRAZO)

# ==========================================================
# 📂 GESTIÓN DE CAJA NEGRA (LOGS)
# ==========================================================
LOG_DIR = "logs_sistema"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
MASTER_LOG_FILE = os.path.join(LOG_DIR, f"log_maestro_{'LIVE' if MODO_LIVE else 'SIM'}_{session_id}.txt")

COLORES = {
    "mt5_feeder": Fore.GREEN + Style.BRIGHT,
    "mt5_gateway": Fore.RED + Style.BRIGHT,
    "sensor_feeder": Fore.WHITE,
    "n_talamo": Fore.CYAN,
    "n_visual": Fore.BLUE,
    "n_homeostasis": Fore.YELLOW,
    "n_ejecutor": Fore.MAGENTA,
}

def guardar_en_log(mensaje):
    with open(MASTER_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(mensaje + "\n")

def capturar_flujo(proceso, nombre):
    """Lee, colorea y guarda la salida de cada lóbulo."""
    for linea in iter(proceso.stdout.readline, b''):
        try:
            texto = linea.decode('utf-8', errors='replace').strip()
            if not texto: continue
            
            color = COLORES.get(nombre, Fore.WHITE)
            ts_real = datetime.datetime.now().strftime("%H:%M:%S")
            mensaje_formateado = f"[{ts_real}] [{nombre.upper()}] {texto}"
            
            print(f"{color}{mensaje_formateado}")
            guardar_en_log(mensaje_formateado)
            
        except Exception:
            pass

def lanzar_organismo():
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}🧠 CEREBRO TRADING ALPHA v3.0 - MODO: {'[LIVE MT5]' if MODO_LIVE else '[SIMULACIÓN CSV]'}")
    print(f"{Fore.CYAN}{'='*60}\n")
    print(f"{Fore.YELLOW}📂 Caja Negra activa en: {MASTER_LOG_FILE}\n")
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = os.getcwd()

    procesos = []
    for s in SCRIPTS_A_LANZAR:
        script_path = os.path.normcase(s)
        nombre = os.path.basename(s).replace('.py', '')
        
        try:
            proc = subprocess.Popen(
                [sys.executable, script_path], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                env=env,
                text=False 
            )
            t = threading.Thread(target=capturar_flujo, args=(proc, nombre), daemon=True)
            t.start()
            procesos.append(proc)
        except Exception as e:
            print(f"{Fore.RED}❌ Error al despertar lóbulo {nombre}: {e}")

    try:
        for p in procesos:
            p.wait()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}🛑 Apagando organismo digital...")
        for p in procesos:
            p.terminate()

if __name__ == "__main__":
    lanzar_organismo()  