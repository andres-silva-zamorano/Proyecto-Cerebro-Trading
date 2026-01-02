import redis
import json
from config import REDIS_HOST, REDIS_PORT, CH_BRAIN_STATE

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    
    # El ejecutor escucha a TODOS los lóbulos de percepción
    pubsub.subscribe(
        CH_BRAIN_STATE, 
        'visual_perception', 
        'momentum_perception', 
        'vestibular_perception'
    )

    print("--- Ejecutor Maestro: Integrando Decisiones Prefrontales ---")

    # Memoria de corto plazo para la última opinión de cada neurona
    percepciones = {
        "talamo": None,
        "visual": None,
        "momentum": None,
        "vestibular": None
    }

    for message in pubsub.listen():
        if message['type'] == 'message':
            canal = message['channel'].decode('utf-8')
            payload = json.loads(message['data'])
            
            # 1. Actualizar memoria de percepciones
            if canal == CH_BRAIN_STATE: percepciones["talamo"] = payload
            elif canal == 'visual_perception': percepciones["visual"] = payload
            elif canal == 'momentum_perception': percepciones["momentum"] = payload
            elif canal == 'vestibular_perception': percepciones["vestibular"] = payload

            # 2. Solo intentar decidir si tenemos el cuadro completo (todas las neuronas activas)
            if all(percepciones.values()):
                decidir_accion(percepciones, r)

def decidir_accion(p, r):
    # --- REGLAS DE ORO DE LA CORTEZA PREFRONTAL ---
    
    # A. Filtro de Seguridad (Vestibular)
    if not p["vestibular"]["is_stable"]:
        # print("Ejecutor: Bloqueado por Ruido Alto.")
        return

    # B. Filtro de Contexto (Tálamo)
    regime = p["talamo"]["regime_id"]
    confianza = p["talamo"]["confidence"]
    
    # C. Filtro Estructural (Visual)
    visual_state = p["visual"]["fan_order"]
    
    # D. Filtro de Energía (Momentum)
    energia = p["momentum"]["energy_score"]
    fatiga = p.get("momentum", {}).get("is_exhausted", False)

    signal = "WAIT"

    # --- LÓGICA DE COMPRA (BUY) ---
    if regime == 5 and visual_state == "bullish_expand":
        if energia >= 0.7 and not fatiga:
            signal = "BUY"

    # --- LÓGICA DE VENTA (SELL) ---
    elif regime == 6 and visual_state == "bearish_expand":
        if energia >= 0.7 and not fatiga:
            signal = "SELL"

    # 3. Publicar la Decisión Final
    if signal != "WAIT":
        decision_payload = {
            "Timestamp": p["talamo"]["Timestamp"],
            "action": signal,
            "price_at_entry": p["talamo"].get('Close_Price', 0),
            "reason": f"Reg:{regime} | Vis:{visual_state} | En:{energia}",
            "confidence": confianza
        }
        r.publish('brain_decision', json.dumps(decision_payload))
        print(f"🚀 DECISIÓN: {signal} en {p['talamo']['Timestamp']} | Razón: {decision_payload['reason']}")

if __name__ == "__main__":
    main()