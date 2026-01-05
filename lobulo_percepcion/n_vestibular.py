import redis
import json
import sys
import os
from rich.console import Console

sys.path.append(os.getcwd())
from config import *

console = Console()

def main():
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        pubsub = r.pubsub()
        pubsub.subscribe(CH_MARKET_DATA, CH_BRAIN_STATE)
    except Exception as e:
        console.print(f"[bold red]❌ Error de conexión:[/bold red] {e}")
        return

    console.print("[bold blue]⚖️ Neurona Vestibular: Equilibrio Dinámico por Régimen Activo[/bold blue]")

    REGIMEN_ACTUAL = "0"

    for message in pubsub.listen():
        if message['type'] == 'message':
            canal = message['channel'].decode('utf-8')
            data = json.loads(message['data'])
            
            if canal == CH_BRAIN_STATE:
                REGIMEN_ACTUAL = str(data.get('regime_id', 0))

            elif canal == CH_MARKET_DATA:
                ts = data.get('Timestamp', 'N/A')
                atr_rel = data.get('ATR_Rel', 0)
                
                # UMBRALES DINÁMICOS: El ruido permitido varía según el terreno
                tolerancia = {
                    "0": 0.0008, # Rango: Muy estricto
                    "5": 0.0015, # Tendencia: Más permisivo
                    "6": 0.0018  # Tendencia Explosiva: Permite mucho ruido
                }
                
                umbral_ruido = tolerancia.get(REGIMEN_ACTUAL, 0.0008) # Default 0.0008
                is_stable = atr_rel < umbral_ruido
                
                vestibular_perception = {
                    "Timestamp": ts,
                    "noise_level": round(atr_rel, 6),
                    "is_stable": is_stable,
                    "action_potential": round(1.0 if is_stable else 0.1, 2)
                }
                
                r.publish(CH_VESTIBULAR, json.dumps(vestibular_perception))
                
                color = "green" if is_stable else "red"
                status = "ESTABLE" if is_stable else "RUIDO ALTO"
                console.print(f"⚖️ [{ts}] Reg:{REGIMEN_ACTUAL} | Ruido:{atr_rel:.6f} | [bold {color}]{status}[/bold {color}]")

if __name__ == "__main__":
    main()