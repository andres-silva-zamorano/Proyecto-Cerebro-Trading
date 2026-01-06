import redis
import json
import os
import datetime
import sys

sys.path.append(os.getcwd())
from config import *

# Crear carpeta de bitácora
LOG_DIR = "bitacora_trading"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    pubsub.subscribe(CH_BRAIN_STATE, CH_DECISION, CH_HOMEOSTASIS)

    # Archivo CSV de la sesion
    filename = os.path.join(LOG_DIR, f"historial_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    
    # Escribir cabecera
    with open(filename, "w", encoding="utf-8") as f:
        f.write("Timestamp_Mercado,Regimen,Evento,Detalle,PnL_Flotante,PnL_Acumulado\n")

    print(f"🧠 Hipocampo grabando historial en: {filename}")

    estado_actual = {"regime": "0", "pnl_f": 0, "pnl_a": 0}

    for message in pubsub.listen():
        if message['type'] == 'message':
            canal = message['channel'].decode('utf-8')
            data = json.loads(message['data'])
            ts_mercado = data.get("Timestamp", "N/A")
            
            evento = ""
            detalle = ""

            if canal == CH_BRAIN_STATE:
                estado_actual["regime"] = data.get("regime_id", "?")
                continue # No logueamos cada cambio de precio para no saturar

            elif canal == CH_DECISION:
                evento = "DECISION"
                detalle = f"{data.get('action')} (Consenso: {data.get('consenso')})"

            elif canal == CH_HOMEOSTASIS:
                estado_actual["pnl_f"] = data.get("floating_pnl", 0)
                estado_actual["pnl_a"] = data.get("daily_pnl", 0)
                
                # Solo logueamos si hay ordenes abiertas o hubo un cierre
                if data.get("open_orders", 0) > 0:
                    evento = "ESTADO_CLUSTER"
                    detalle = f"Ordenes: {data.get('open_orders')}"
                else:
                    continue # Ignorar si esta IDLE

            if evento:
                linea = f"{ts_mercado},{estado_actual['regime']},{evento},{detalle},{estado_actual['pnl_f']},{estado_actual['pnl_a']}\n"
                with open(filename, "a", encoding="utf-8") as f:
                    f.write(linea)

if __name__ == "__main__":
    main()