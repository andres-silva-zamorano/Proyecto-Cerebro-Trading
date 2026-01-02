import redis
import json
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA

def main():
    # Conexión a la Médula Espinal
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    pubsub.subscribe(CH_MARKET_DATA)

    print("--- Neurona Somatosensorial: Sintiendo Energía de Momentum ---")

    for message in pubsub.listen():
        if message['type'] == 'message':
            data = json.loads(message['data'])
            
            # 1. Extraer sensores de fuerza del dataset
            rsi = data.get('RSI_Val', 50)
            rsi_vel = data.get('RSI_Velocidad', 0)
            adx = data.get('ADX_Val', 0)
            adx_diff = data.get('ADX_Diff', 0)
            
            # 2. Lógica de "Excitación Neuronal" (Analogía del esfuerzo muscular)
            # Si el ADX sube y el RSI tiene velocidad, hay "Ignición"
            hambre_de_movimiento = 0.0
            
            # Umbral de ADX: > 25 indica tendencia iniciada
            if adx > 25:
                hambre_de_movimiento += 0.4
                
            # Si la aceleración (ADX_Diff) es positiva, sumamos carga eléctrica
            if adx_diff > 0:
                hambre_de_movimiento += 0.3
                
            # Si el RSI se mueve rápido a favor de la tendencia (RSI_Velocidad)
            if abs(rsi_vel) > 5:
                hambre_de_movimiento += 0.3

            # 3. Detectar "Fatiga" (Divergencia sensorial)
            # Si el precio sube pero la velocidad del RSI es negativa, el músculo falla
            está_cansado = False
            if (rsi > 70 and rsi_vel < 0) or (rsi < 30 and rsi_vel > 0):
                está_cansado = True
                hambre_de_movimiento *= 0.5 # Inhibimos el impulso por cansancio

            # 4. Publicar la percepción de energía
            momentum_payload = {
                "energy_score": round(hambre_de_movimiento, 2),
                "is_exhausted": está_cansado,
                "adx_intensity": adx,
                "action_potential": hambre_de_movimiento
            }
            
            r.publish('momentum_perception', json.dumps(momentum_payload))
            
            # Feedback visual para el usuario
            status = "🔥 IGNICIÓN" if hambre_de_movimiento > 0.7 else "☁️ CALMA"
            if está_cansado: status = "💤 FATIGA"
            
            print(f"Momentum: Score {hambre_de_movimiento:.2f} | {status} (ADX: {adx:.1f})")

if __name__ == "__main__":
    main()