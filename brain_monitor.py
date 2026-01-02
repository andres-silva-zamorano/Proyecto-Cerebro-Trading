import redis
import json
import os
from config import REDIS_HOST, REDIS_PORT, CH_BRAIN_STATE, CH_MARKET_DATA, CH_VISUAL, CH_MOMENTUM, CH_VESTIBULAR, CH_DECISION, CH_HOMEOSTASIS

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    
    # Suscribirse a la Médula Espinal completa
    pubsub.subscribe(
        CH_MARKET_DATA, CH_BRAIN_STATE, CH_VISUAL, 
        CH_MOMENTUM, CH_VESTIBULAR, CH_DECISION, CH_HOMEOSTASIS
    )

    brain_view = {
        "market_time": "Sincronizando...",
        "talamo": {"regime": "N/A"},
        "visual": {"fan_state": "N/A"},
        "momentum": {"energy": 0.0},
        "vestibular": {"noise": 0.0, "stable": True},
        "decision": {"action": "WAIT"},
        "salud": {"open_orders": 0, "floating_pnl": 0.0, "daily_pnl": 0.0}
    }

    for message in pubsub.listen():
        if message['type'] == 'message':
            canal = message['channel'].decode('utf-8')
            payload = json.loads(message['data'])

            if 'Timestamp' in payload: brain_view["market_time"] = payload['Timestamp']

            # Enrutamiento de señales por canal
            if canal == CH_BRAIN_STATE:
                brain_view["talamo"]["regime"] = payload.get('regime_id', '???')
            elif canal == CH_VISUAL:
                brain_view["visual"]["fan_state"] = payload.get('fan_order', 'N/A')
            elif canal == CH_MOMENTUM:
                brain_view["momentum"]["energy"] = payload.get('energy_score', 0.0)
            elif canal == CH_VESTIBULAR:
                brain_view["vestibular"]["noise"] = payload.get('noise_level', 0.0)
                brain_view["vestibular"]["stable"] = payload.get('is_stable', True)
            elif canal == CH_DECISION:
                brain_view["decision"]["action"] = payload.get('action', 'WAIT')
            elif canal == CH_HOMEOSTASIS:
                brain_view["salud"]["open_orders"] = payload.get('open_orders', 0)
                brain_view["salud"]["floating_pnl"] = payload.get('floating_pnl', 0.0)
                brain_view["salud"]["daily_pnl"] = payload.get('daily_pnl', 0.0)

            # RENDERIZADO (Solo se limpia cuando llega data del stream para evitar parpadeo excesivo)
            if canal == CH_MARKET_DATA:
                clear_console()
                print(f"============================================================")
                print(f"🧠 CEREBRO MODULAR | TIEMPO: {brain_view['market_time']}")
                print(f"============================================================")
                print(f"📍 TÁLAMO      >> RÉGIMEN: [{brain_view['talamo']['regime']}]")
                print(f"👁️  VISUAL      >> ABANICO: {brain_view['visual']['fan_state'].upper()}")
                print(f"⚡ MOMENTUM    >> ENERGÍA: {brain_view['momentum']['energy']:.2f}")
                print(f"⚖️  VESTIBULAR  >> RUIDO: {brain_view['vestibular']['noise']:.6f} | {'✅' if brain_view['vestibular']['stable'] else '❌'}")
                print(f"------------------------------------------------------------")
                print(f"🚀 ACCIÓN: {brain_view['decision']['action']} | 📦 ÓRDENES: {brain_view['salud']['open_orders']}")
                print(f"📉 PnL: {'🟢' if brain_view['salud']['floating_pnl'] >= 0 else '🔴'} {brain_view['salud']['floating_pnl']:.2f} | DÍA: {brain_view['salud']['daily_pnl']:.2f}")
                print(f"============================================================")

if __name__ == "__main__":
    main() 