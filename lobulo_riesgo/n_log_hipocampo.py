import redis, json, os, datetime, sys
sys.path.append(os.getcwd())
from config import *

LOG_DIR = "bitacora_trading"
if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    # AÑADIDO CH_RESULTS para no perder ningún cierre
    pubsub.subscribe(CH_BRAIN_STATE, CH_DECISION, CH_HOMEOSTASIS, CH_RESULTS)
    
    filename = os.path.join(LOG_DIR, f"historial_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("Timestamp_Mercado,Regimen,Evento,Detalle,PnL_Flotante,PnL_Total_Historico\n")

    print(f"🧠 Hipocampo grabando historial en: {filename}")
    estado_actual = {"regime": "0", "pnl_f": 0, "pnl_t": 0}

    for message in pubsub.listen():
        if message['type'] == 'message':
            canal = message['channel'].decode('utf-8')
            data = json.loads(message['data'])
            ts_m = data.get("Timestamp", "N/A")
            evento, detalle = "", ""

            if canal == CH_BRAIN_STATE:
                estado_actual["regime"] = data.get("regime_id", "?")
            elif canal == CH_RESULTS:
                evento = "CIERRE_COBRADO"
                detalle = f"PnL: {data.get('final_pnl'):.2f} | Razon: {data.get('razon')}"
            elif canal == CH_DECISION:
                evento = "DECISION_OPEN"
                detalle = f"{data.get('action')} (Cons: {data.get('consenso')})"
            elif canal == CH_HOMEOSTASIS:
                estado_actual["pnl_f"] = data.get("floating_pnl", 0)
                estado_actual["pnl_t"] = data.get("total_pnl", 0)
                if data.get("open_orders", 0) > 0:
                    evento = "ESTADO_MERCADO"
                    detalle = f"Ordenes: {data.get('open_orders')}"
            
            if evento:
                linea = f"{ts_m},{estado_actual['regime']},{evento},{detalle},{estado_actual['pnl_f']},{estado_actual['pnl_t']}\n"
                with open(filename, "a", encoding="utf-8") as f: f.write(linea)

if __name__ == "__main__": main()