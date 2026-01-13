import subprocess
import threading
import sys
import os
import datetime
import time
from colorama import Fore, Style, init

# Inicializar colorama para una visualización profesional en la terminal de Vision Global
init(autoreset=True)

# ==========================================================
# ⚡ CONFIGURACIÓN DE ENTORNO ALPHA v3.9.3 - FRACTAL DUAL
# ==========================================================
MODO_LIVE = True  

scripts_percepcion = [
    "lobulo_percepcion/n_talamo.py",      # Tálamo Fractal: M1 + M15
    "lobulo_percepcion/n_vestibular.py",  # Filtro de Ruido
    "lobulo_percepcion/n_momentum.py",    # Energía de Precio
    "lobulo_percepcion/n_visual.py"       # IA Visual H5
]

scripts_riesgo = [
    "lobulo_riesgo/n_homeostasis.py",     # Gestión de Ráfagas
    "lobulo_riesgo/n_guardian_vestibular.py", 
    "lobulo_riesgo/n_log_hipocampo.py"    # Memoria de Sesión
]

scripts_ejecucion = ["lobulo_ejecucion/n_ejecutor.py"]

if MODO_LIVE:
    SENSOR = "lobulo_percepcion/mt5_feeder.py"    
    BRAZO = "lobulo_ejecucion/mt5_gateway.py"     
else:
    SENSOR = "lobulo_percepcion/sensor_feeder.py" 
    BRAZO = None                                  

SCRIPTS_A_LANZAR = [SENSOR] + scripts_percepcion + scripts_riesgo + scripts_ejecucion
if BRAZO:
    SCRIPTS_A_LANZAR.append(BRAZO)

# Gestión de Logs
LOG_DIR = "logs_sistema"
if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)

session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
MASTER_LOG_FILE = os.path.join(LOG_DIR, f"log_v393_FRACTAL_{session_id}.txt")

COLORES = {
    "mt5_feeder": Fore.GREEN + Style.BRIGHT,
    "mt5_gateway": Fore.RED + Style.BRIGHT,
    "n_talamo": Fore.CYAN + Style.BRIGHT,
    "n_visual": Fore.BLUE + Style.BRIGHT,
    "n_homeostasis": Fore.YELLOW + Style.BRIGHT,
    "n_ejecutor": Fore.MAGENTA + Style.BRIGHT,
    "n_vestibular": Fore.WHITE + Style.DIM,
}

def guardar_en_log(mensaje):
    """Escribe cada evento en la bitácora con manejo de errores de codificación."""
    try:
        with open(MASTER_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(mensaje + "\n")
    except:
        pass

def capturar_flujo(proceso, nombre):
    """Lee la salida estándar de forma continua y sin bloqueos."""
    while True:
        linea = proceso.stdout.readline()
        if not linea and proceso.poll() is not None:
            break
        if linea:
            try:
                texto = linea.decode('utf-8', errors='replace').strip()
                if not texto: continue
                
                color = COLORES.get(nombre, Fore.WHITE)
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                msg = f"[{ts}] [{nombre.upper()}] {texto}"
                
                print(f"{color}{msg}", flush=True)
                guardar_en_log(msg)
            except:
                pass

def lanzar_organismo():
    """Inicializa el cerebro Alpha v3.9.3 con blindaje de tuberías."""
    print(f"\n{Fore.CYAN}{'='*75}")
    print(f"{Fore.CYAN}🧠 CEREBRO TRADING ALPHA v3.9.3 - FRACTAL DUAL")
    print(f"{Fore.CYAN}ESTADO: Despertando Organismo en Modo Live (Vision Global)")
    print(f"{Fore.CYAN}{'='*75}\n")
    
    # Configuración de entorno crítica para evitar el "pegado" por buffering
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = os.getcwd()

    procesos = []
    
    for s in SCRIPTS_A_LANZAR:
        nombre = os.path.basename(s).replace('.py', '')
        print(f"{Fore.WHITE}🌱 Despertando lóbulo: {nombre.upper()}...", flush=True)
        
        try:
            # Usamos bufsize=1 para forzar el paso de líneas individuales
            proc = subprocess.Popen(
                [sys.executable, "-u", s], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                env=env,
                bufsize=1
            )
            
            t = threading.Thread(target=capturar_flujo, args=(proc, nombre), daemon=True)
            t.start()
            procesos.append(proc)
            # Pequeña pausa para no saturar la inicialización de MT5/Redis
            time.sleep(0.8)
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error fatal en {nombre}: {e}")

    try:
        # Mantenemos el orquestador vivo monitoreando la salud de los hijos
        while True:
            time.sleep(10)
            if all(p.poll() is not None for p in procesos):
                print(f"\n{Fore.YELLOW}ℹ️ Todos los procesos han terminado.")
                break
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}🛑 Apagando organismo digital por orden del usuario...")
        for p in procesos:
            p.terminate()

if __name__ == "__main__":
    lanzar_organismo()