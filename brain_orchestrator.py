import subprocess
import threading
import sys
import os
from colorama import Fore, Style, init

init(autoreset=True)

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

def capturar_flujo(proceso, nombre):
    # IMPORTANTE: Usamos errors='replace' para que no muera el hilo si hay un caracter raro
    for linea in iter(proceso.stdout.readline, b''):
        try:
            texto = linea.decode('utf-8', errors='replace').strip()
            color = COLORES.get(nombre, Fore.WHITE)
            if "ESTABLE" in texto and "sensor" in nombre:
                continue
            print(f"{color}[{nombre.upper()}] {texto}")
        except Exception:
            pass # Si falla el print, seguimos adelante

def lanzar_cerebro():
    scripts = [
        "lobulo_percepcion/sensor_feeder.py",
        "lobulo_percepcion/n_talamo.py",
        "lobulo_percepcion/n_vestibular.py",
        "lobulo_percepcion/n_momentum.py",
        "lobulo_percepcion/n_visual.py",
        "lobulo_riesgo/n_homeostasis.py",
        "lobulo_riesgo/n_guardian_vestibular.py",
        "lobulo_ejecucion/n_ejecutor.py"
    ]

    print(f"{Fore.GREEN}--- Iniciando Organismo Digital ---")
    
    # Forzar UTF-8 en las variables de entorno para los hijos
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = os.getcwd()

    procesos = []
    for s in scripts:
        script_path = os.path.normcase(s)
        nombre = os.path.basename(s).replace('.py', '')
        
        try:
            # Usamos shell=True en Windows para mejorar compatibilidad de pipes
            proc = subprocess.Popen(
                [sys.executable, script_path], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                env=env,
                text=False # Manejamos los bytes manualmente para evitar UnicodeError
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
        for p in procesos:
            p.terminate()

if __name__ == "__main__":
    lanzar_cerebro()