import redis
import json
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA

def main():
    # Conexión a la "Médula Espinal" (Redis)
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        pubsub = r.pubsub()
        pubsub.subscribe(CH_MARKET_DATA)
    except Exception as e:
        print(f"❌ Error de conexión en N_Vestibular: {e}")
        return

    print("--- Neurona Vestibular: Analizando Equilibrio y Ruido ---")

    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                data = json.loads(message['data'])
            except Exception:
                continue
            
            # 1. Extraer Timestamp para sincronía global
            ts = data.get('Timestamp', 'N/A')
            
            # 2. Análisis de Ruido (Basado en ATR Relativo)
            # El ATR_Rel mide qué tan grande es la volatilidad respecto al precio.
            atr_rel = data.get('ATR_Rel', 0)
            
            # Definimos umbrales de estabilidad (ajustables según el activo)
            # Un ruido > 0.0008 suele indicar velas con mechas muy largas o gaps.
            umbral_ruido = 0.0008
            nivel_de_ruido = atr_rel
            
            # 3. Determinación de Estabilidad
            # Si el ruido es muy alto, el sistema pierde el "equilibrio"
            is_stable = atr_rel < umbral_ruido
            
            # 4. Análisis de Vértigo (Divergencia de volatilidad)
            # Si el precio se mueve mucho pero con poco volumen o sin dirección clara
            # (Aquí podríamos añadir más lógica en el futuro)
            
            # 5. Construcción del paquete de percepción vestibular
            vestibular_perception = {
                "Timestamp": ts,
                "noise_level": round(nivel_de_ruido, 6),
                "is_stable": is_stable,
                "action_potential": round(1.0 if is_stable else 0.1, 2)
            }
            
            # 6. Publicar en Redis para el Monitor y el Ejecutor
            r.publish('vestibular_perception', json.dumps(vestibular_perception))
            
            # Log de diagnóstico para la terminal del orquestador
            status_v = "✅ ESTABLE" if is_stable else "⚠️ RUIDO ALTO"
            print(f"⚖️ VESTIBULAR [{ts}]: Ruido {nivel_de_ruido:.6f} | {status_v}")

if __name__ == "__main__":
    main()