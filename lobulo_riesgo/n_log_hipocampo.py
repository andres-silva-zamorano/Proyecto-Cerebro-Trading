import redis
import json
import datetime
import os
from config import REDIS_HOST, REDIS_PORT, CH_VISUAL, CH_MARKET_DATA

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    # Escuchamos todo lo relevante para la bitácora
    pubsub.subscribe('brain_decision', 'homeostasis_status', CH_VISUAL)

    log_dir = "logs_trading"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    print("--- 🧠 Hipocampo Activo: Registrando Memoria del Cerebro ---")

    for message in pubsub.listen():
        if message['type'] == 'message':
            canal = message['channel'].decode('utf-8')
            payload = json.loads(message['data'])
            ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            log_file = f"{log_dir}/bitacora_{datetime.datetime.now().strftime('%Y%m%d')}.txt"
            
            with open(log_file, "a", encoding="utf-8") as f:
                if canal == 'brain_decision':
                    msg = f"[{ahora}] 🚀 ENTRADA: {payload['action']} | Precio: {payload['price_at_entry']} | Confianza: {payload['confidence']:.2%}\n"
                    f.write(msg)
                    print(msg.strip())

                elif canal == 'homeostasis_status':
                    # Solo logueamos si hubo un cierre (cuando pasan de 1 a 0 órdenes)
                    # O podrías loguear el estado del PnL cada X tiempo.
                    if payload['open_orders'] == 0:
                        msg = f"[{ahora}] 🏁 CIERRE DE CLÚSTER: PnL Flotante: {payload['floating_pnl']} | PnL Día: {payload['daily_pnl']}\n"
                        # Nota: El motivo lo imprime la homeostasis en consola, 
                        # pero este log registra el resultado final.
                        f.write(msg)
                        f.write("-" * 50 + "\n")

                elif canal == CH_VISUAL:
                    # Loguear solo si la confianza es muy alta o muy baja (eventos de interés)
                    if payload['confidence'] > 0.90 or payload['confidence'] < 0.30:
                        msg = f"[{ahora}] 👁️ ALERTA IA: {payload['fan_order']} | Conf: {payload['confidence']:.2%}\n"
                        f.write(msg)

if __name__ == "__main__":
    main()