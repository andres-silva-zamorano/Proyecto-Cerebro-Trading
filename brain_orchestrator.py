import subprocess
import threading
import sys
import os
import datetime
from colorama import Fore, Style, init

init(autoreset=True)

# Crear carpeta de logs si no existe
LOG_DIR = "logs_sistema"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Nombre del archivo de log para esta sesion
session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
MASTER_LOG_FILE = os.path.join(LOG_DIR, f"log_maestro_{session_id}.txt")

COLORES = {
    "sensor_feeder": Fore.WHITE,  
    "n_talamo": Fore.CYAN,                
    "n_vestibular": Fore.MAGENTA,         
    "n_ejecutor": Fore.GREEN,             
    "n_homeostasis": Fore.YELLOW,         
    "n_momentum": Fore.BLUE,              
    "n_visual": Fore.BLUE,                
    "n_guardian_vestibular": Fore.RED,      
}

def guardar_en_log(mensaje):
    """Escribe el mensaje en el archivo de log maestro."""
    with open(MASTER_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(mensaje + "\n")

def capturar_flujo(proceso, nombre):
    """Lee la salida de cada .py, la colorea y la guarda en disco."""
    for linea in iter(proceso.stdout.readline, b''):
        try:
            texto = linea.decode('utf-8', errors='replace').strip()
            if not texto: continue
            
            color = COLORES.get(nombre, Fore.WHITE)
            ts_real = datetime.datetime.now().strftime("%H:%M:%S")
            mensaje_formateado = f"[{ts_real}] [{nombre.upper()}] {texto}"
            
            # 1. Mostrar en pantalla
            print(f"{color}{mensaje_formateado}")
            
            # 2. Guardar en Caja Negra
            guardar_en_log(mensaje_formateado)
            
        except Exception:
            pass

def lanzar_cerebro():
    scripts = [
        "lobulo_percepcion/sensor_feeder.py",
        "lobulo_percepcion/n_talamo.py",
        "lobulo_percepcion/n_vestibular.py",
        "lobulo_percepcion/n_momentum.py",
        "lobulo_percepcion/n_visual.py",
        "lobulo_riesgo/n_homeostasis.py",
        "lobulo_riesgo/n_guardian_vestibular.py",
        "lobulo_ejecucion/n_ejecutor.py",
        "lobulo_riesgo/n_log_hipocampo.py" # Añadimos el hipocampo a la lista
    ]

    print(f"{Fore.GREEN}--- 🧠 Iniciando Organismo Digital con Caja Negra Activa ---")
    print(f"{Fore.YELLOW} Archivo de log: {MASTER_LOG_FILE}")
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = os.getcwd()

    procesos = []
    for s in scripts:
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
            print(f"Error al lanzar {nombre}: {e}")

    try:
        for p in procesos:
            p.wait()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}🛑 Apagando organismo...")
        for p in procesos:
            p.terminate()

if __name__ == "__main__":
    lanzar_cerebro()