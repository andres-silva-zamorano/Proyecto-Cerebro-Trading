import redis
import json
import sys
import os

# Asegurar que el sistema reconozca la raíz para importar config
sys.path.append(os.getcwd())
from config import (
    REDIS_HOST, REDIS_PORT, 
    CH_BRAIN_STATE, CH_VISUAL, CH_MOMENTUM, CH_VESTIBULAR, CH_DECISION,
    CH_BLOCK  # Usamos el canal de bloqueo definido en config
)

# --- MEMORIA DE REFRACTARIEDAD ---
ULTIMO_TIMESTAMP_ORDEN = ""

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    
    # Suscripción a la médula espinal sensorial
    pubsub.subscribe(CH_BRAIN_STATE, CH_VISUAL, CH_MOMENTUM, CH_VESTIBULAR)

    print("--- 🚀 Ejecutor Maestro Alpha (Versión Blindada) ---")
    print(f"📡 Escuchando canales y respetando bloqueo en canal: {CH_BLOCK}")

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
            
            # Actualizar memoria sensorial
            if canal == CH_BRAIN_STATE: percepciones["talamo"] = payload
            elif canal == CH_VISUAL: percepciones["visual"] = payload
            elif canal == CH_MOMENTUM: percepciones["momentum"] = payload
            elif canal == CH_VESTIBULAR: percepciones["vestibular"] = payload

            # Solo decidir si tenemos el cuadro completo
            if all(percepciones.values()):
                decidir_accion(percepciones, r)

def decidir_accion(p, r):
    global ULTIMO_TIMESTAMP_ORDEN
    
    # 0. Sincronía de tiempo
    timestamp_actual = p["talamo"]["Timestamp"]
    
    # --- FILTRO 1: BLOQUEO POR HOMEÓSTASIS ---
    # Si la Homeostasis activó el flag de bloqueo en Redis, no operamos.
    if r.get(f"{CH_BLOCK}_active"):
        return

    # --- FILTRO 2: REFRACTARIEDAD MINUTAL ---
    if timestamp_actual == ULTIMO_TIMESTAMP_ORDEN:
        return

    # 1. Extracción de percepciones
    regime = p["talamo"]["regime_id"]
    energia = p["momentum"]["energy_score"]
    ruido = p["vestibular"].get("noise_level", 0.0)
    confianza_ia = p["visual"].get("confidence", 0.0)
    visual_state = p["visual"].get("fan_order", "neutral")

    # --- CONFIGURACIÓN DE UMBRALES ---
    UMBRAL_ENERGIA_MIN = 0.40  
    UMBRAL_RUIDO_MAX = 0.0015  
    
    signal = "WAIT"
    motivo_bloqueo = ""

    # --- LÓGICA DE FILTRADO ---
    
    # A. Filtro de Ruido
    if ruido > UMBRAL_RUIDO_MAX:
        motivo_bloqueo = f"❌ RUIDO EXCESIVO: {ruido:.6f}"
    
    # B. Filtro de Régimen (Tálamo)
    elif regime not in [5, 6]:
        motivo_bloqueo = f"❌ TÁLAMO NEUTRAL ({regime})"
    
    # C. Filtro de Energía (Momentum)
    elif energia < UMBRAL_ENERGIA_MIN:
        motivo_bloqueo = f"❌ ENERGÍA INSUFICIENTE: {energia:.2f}"
        
    # D. FILTRO DE SEGURIDAD IA (Evitar el estado neutral que causó pérdidas)
    elif visual_state == "neutral":
        motivo_bloqueo = "❌ IA EN ESTADO NEUTRAL (Sin dirección)"

    # --- DETERMINACIÓN DE SEÑAL ---
    if motivo_bloqueo == "":
        # Solo disparamos si hay consenso entre Tálamo e IA Visual
        if regime == 5 and visual_state == "bullish_alpha":
            signal = "BUY"
        elif regime == 6 and visual_state == "bearish_alpha":
            signal = "SELL"
        else:
            motivo_bloqueo = f"❌ SIN CONSENSO (Reg:{regime} | IA:{visual_state})"

    # --- DISPARO DE SEÑAL ---
    if signal != "WAIT":
        ULTIMO_TIMESTAMP_ORDEN = timestamp_actual
        
        decision_payload = {
            "Timestamp": timestamp_actual,
            "action": signal,
            "price_at_entry": p["talamo"].get('Close_Price', 0),
            "reason": f"Reg:{regime} | Vis:{visual_state} | En:{energia:.2f}",
            "confidence": confianza_ia
        }
        
        r.publish(CH_DECISION, json.dumps(decision_payload))
        print(f"🚀 [ORDEN DISPARADA]: {signal} en {timestamp_actual} | Precio: {decision_payload['price_at_entry']} | Conf: {confianza_ia:.2%}")
    else:
        # Log de diagnóstico cada 5 minutos para ver que el bot sigue vivo
        minuto = int(timestamp_actual.split(":")[-1])
        if minuto % 5 == 0:
             print(f"DEBUG [{timestamp_actual}]: {motivo_bloqueo}")

if __name__ == "__main__":
    main()