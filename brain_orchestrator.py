import subprocess
import time
import sys
import os

# Lista completa de procesos del Lóbulo de Percepción
NEURONAS = [
    "lobulo_percepcion/sensor_feeder.py",
    "lobulo_percepcion/n_talamo.py",
    "lobulo_percepcion/n_visual.py",
    "lobulo_percepcion/n_momentum.py",
    "lobulo_percepcion/n_vestibular.py",
    "lobulo_ejecucion/n_ejecutor.py",
    "lobulo_riesgo/n_homeostasis.py"  # <--- INTEGRACIÓN FINAL
]

def launch_brain():
    processes = []
    print("--- Iniciando Ciclo de Vida del Cerebro Modular ---")
    
    # Obtenemos la ruta raíz del proyecto (donde está config.py)
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Configuramos el entorno para que las neuronas encuentren a 'config'
    env = os.environ.copy()
    env["PYTHONPATH"] = root_dir + os.pathsep + env.get("PYTHONPATH", "")

    # Lanzamos cada neurona con el entorno actualizado
    for neurona in NEURONAS:
        # Usamos sys.executable para asegurar que usamos el mismo Python (base)
        p = subprocess.Popen([sys.executable, neurona], env=env)
        processes.append(p)
        print(f"✅ Neurona activada: {neurona}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Apagando organismo...")
        for p in processes:
            p.terminate()

if __name__ == "__main__":
    launch_brain()