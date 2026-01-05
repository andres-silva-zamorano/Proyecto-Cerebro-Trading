import redis
import json
import datetime
import os
import sys

sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_VISUAL, CH_DECISION, CH_HOMEOSTASIS

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    # Escuchamos los canales clave para la bitácora
    pubsub.subscribe(CH_DECISION, CH_HOMEOSTASIS, CH_VISUAL)

    log_dir = "logs_trading"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    print("--- 🧠 Hipocampo v3: Registrando Memoria Democrática ---")

    for message in pubsub.listen():
        if message['type'] == 'message':
            canal = message['channel'].decode('utf-8')
            payload = json.loads(message['data'])
            ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            log_file = f"{log_dir}/bitacora_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
            
            with open(log_file, "a", encoding="utf-8") as f:
                if canal == CH_DECISION:
                    # Usamos .get() para evitar errores si falta una llave
                    consenso = payload.get('consenso', 0.0)
                    msg = f"[{ahora}] 🚀 ENTRADA: {payload['action']} | Precio: {payload['price_at_entry']} | Consenso: {consenso:.2f} | Razón: {payload.get('reason')}\n"
                    f.write(msg)
                    print(msg.strip())

                elif canal == CH_HOMEOSTASIS:
                    if payload.get('open_orders') == 0:
                        pnl_f = payload.get('floating_pnl', 0.0)
                        pnl_d = payload.get('daily_pnl', 0.0)
                        msg = f"[{ahora}] 🏁 CIERRE: PnL Flotante: {pnl_f} | PnL Día: {pnl_d}\n"
                        f.write(msg)
                        f.write("-" * 50 + "\n")

if __name__ == "__main__":
    main()