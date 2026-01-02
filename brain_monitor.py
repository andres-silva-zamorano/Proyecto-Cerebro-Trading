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

    # Estructura de datos para la interfaz
    brain_view = {
        "market_time": "Sincronizando...",
        "talamo": {"regime": "N/A"},
        "visual": {"fan_state": "N/A", "confidence": 0.0},
        "momentum": {"energy": 0.0},
        "vestibular": {"noise": 0.0, "stable": True},
        "decision": {"action": "WAIT", "reason": "N/A"},
        "salud": {"open_orders": 0, "floating_pnl": 0.0, "daily_pnl": 0.0}
    }

    print("--- Monitor del Cerebro Alpha Iniciado ---")

    for message in pubsub.listen():
        if message['type'] == 'message':
            canal = message['channel'].decode('utf-8')
            payload = json.loads(message['data'])

            # Sincronización de Tiempo
            if 'Timestamp' in payload: 
                brain_view["market_time"] = payload['Timestamp']

            # 1. TÁLAMO (Contexto)
            if canal == CH_BRAIN_STATE:
                brain_view["talamo"]["regime"] = payload.get('regime_id', '???')

            # 2. VISUAL (IA Alpha)
            elif canal == CH_VISUAL:
                brain_view["visual"]["fan_state"] = payload.get('fan_order', 'N/A')
                brain_view["visual"]["confidence"] = payload.get('confidence', 0.0)

            # 3. MOMENTUM (Energía)
            elif canal == CH_MOMENTUM:
                brain_view["momentum"]["energy"] = payload.get('energy_score', 0.0)

            # 4. VESTIBULAR (Ruido)
            elif canal == CH_VESTIBULAR:
                brain_view["vestibular"]["noise"] = payload.get('noise_level', 0.0)
                brain_view["vestibular"]["stable"] = payload.get('is_stable', True)

            # 5. DECISIÓN (Ejecutor)
            elif canal == CH_DECISION:
                brain_view["decision"]["action"] = payload.get('action', 'WAIT')
                brain_view["decision"]["reason"] = payload.get('reason', 'N/A')

            # 6. HOMEOSTASIS (Riesgo y PnL)
            elif canal == CH_HOMEOSTASIS:
                brain_view["salud"]["open_orders"] = payload.get('open_orders', 0)
                brain_view["salud"]["floating_pnl"] = payload.get('floating_pnl', 0.0)
                brain_view["salud"]["daily_pnl"] = payload.get('daily_pnl', 0.0)

            # --- RENDERIZADO EN CONSOLA ---
            # Se actualiza con cada pulso de Market Data para fluidez constante
            if canal == CH_MARKET_DATA:
                clear_console()
                print(f"============================================================")
                print(f"🧠 CEREBRO ALPHA HFT | TIEMPO: {brain_view['market_time']}")
                print(f"============================================================")
                print(f"📍 TÁLAMO      >> RÉGIMEN: [{brain_view['talamo']['regime']}]")
                
                # Estado de la IA Visual con Confianza
                ia_label = brain_view['visual']['fan_state'].upper()
                conf_val = brain_view['visual']['confidence'] * 100
                print(f"👁️  VISUAL AI   >> ESTADO: {ia_label} | CONF: {conf_val:.2f}%")
                
                print(f"⚡ MOMENTUM    >> ENERGÍA: {brain_view['momentum']['energy']:.2f}")
                
                # Estado Vestibular (Seguridad)
                estabilidad = "✅ ESTABLE" if brain_view['vestibular']['stable'] else "❌ RUIDO ALTO"
                print(f"⚖️  VESTIBULAR  >> RUIDO: {brain_view['vestibular']['noise']:.6f} | {estabilidad}")
                
                print(f"------------------------------------------------------------")
                
                # Decisión y Órdenes
                print(f"🚀 ACCIÓN: {brain_view['decision']['action']} | 📦 ÓRDENES: {brain_view['salud']['open_orders']}")
                print(f"📝 RAZÓN: {brain_view['decision']['reason']}")
                
                # PnL y Salud de la Cuenta
                pnl = brain_view['salud']['floating_pnl']
                pnl_icon = "🟢" if pnl >= 0 else "🔴"
                print(f"📉 PnL ACTUAL: {pnl_icon} {pnl:.2f} | PnL DÍA: {brain_view['salud']['daily_pnl']:.2f}")
                print(f"============================================================")

if __name__ == "__main__":
    main()