import redis
import json
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA

def main():
    # Conexión a la "Médula Espinal"
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    pubsub.subscribe(CH_MARKET_DATA)

    print("--- Neurona Visual: Analizando Estructura de Medias Móviles ---")

    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                data = json.loads(message['data'])
            except Exception:
                continue
            
            # 1. Extraer el tiempo para sincronía global
            ts = data.get('Timestamp', 'N/A')
            
            # 2. Análisis de Pendiente (Slope) de la EMA Principal
            slope = data.get('EMA_Princ_Slope', 0)
            
            # 3. Análisis de Alineación del Abanico (Fan-Out)
            # Extraemos las EMAs en orden: 10, 20, 40, 80, 160, 320
            emas = {
                10: data.get('EMA_10', 0),
                20: data.get('EMA_20', 0),
                40: data.get('EMA_40', 0),
                80: data.get('EMA_80', 0),
                160: data.get('EMA_160', 0),
                320: data.get('EMA_320', 0)
            }
            
            # Lógica de orden jerárquico
            # Alcista: 10 > 20 > 40 > 80 > 160 > 320
            is_bullish = (emas[10] > emas[20] > emas[40] > emas[80] > emas[160] > emas[320])
            
            # Bajista: 10 < 20 < 40 < 80 < 160 < 320
            is_bearish = (emas[10] < emas[20] < emas[40] < emas[80] < emas[160] < emas[320])
            
            if is_bullish:
                fan_order = "bullish_expand"
            elif is_bearish:
                fan_order = "bearish_expand"
            else:
                fan_order = "congested"

            # 4. Cálculo del Potencial de Acción Visual
            # Es una combinación de la pendiente y la claridad del abanico
            base_potential = abs(slope)
            if fan_order != "congested":
                base_potential *= 1.5  # Multiplicador de confianza si hay orden claro
            
            # 5. Construcción del paquete de percepción
            visual_perception = {
                "Timestamp": ts,
                "fan_order": fan_order,
                "slope_intensity": round(slope, 4),
                "action_potential": round(base_potential, 2)
            }
            
            # 6. Publicar en Redis para el Monitor y futuros ejecutores
            r.publish('visual_perception', json.dumps(visual_perception))
            
            # Log de diagnóstico para la terminal del orquestador
            print(f"👁️ VISUAL [{ts}]: Fan {fan_order.upper()} | Pot: {base_potential:.2f}")

if __name__ == "__main__":
    main()