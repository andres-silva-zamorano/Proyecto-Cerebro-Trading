import redis
import json
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    
    # Suscribirse a las decisiones y al chorro de datos del mercado
    pubsub.subscribe('brain_decision', CH_MARKET_DATA)

    print("--- Neurona de Homeostasis: Gestionando Clúster de Órdenes ---")

    SL_MAXIMO_DIARIO = -1000.0  
    ORDENES_ABIERTAS = []       
    PNL_DIARIO_ACUMULADO = 0.0
    ULTIMO_DIA = None

    for message in pubsub.listen():
        if message['type'] == 'message':
            canal = message['channel'].decode('utf-8')
            payload = json.loads(message['data'])
            ts = payload.get('Timestamp', '')
            dia_actual = ts.split(' ')[0] if ts else None

            # A. Reset Diario
            if dia_actual != ULTIMO_DIA:
                PNL_DIARIO_ACUMULADO = 0.0
                ULTIMO_DIA = dia_actual

            # B. Recibir Nueva Orden
            if canal == 'brain_decision':
                # Solo abrir si no hemos quemado el SL diario
                if PNL_DIARIO_ACUMULADO > SL_MAXIMO_DIARIO:
                    nueva_orden = {
                        "tipo": payload.get('action'),
                        "entrada": payload.get('price_at_entry', 0),
                    }
                    ORDENES_ABIERTAS.append(nueva_orden)
            
            # C. Calcular PnL del Clúster cada vez que llega un precio nuevo
            elif canal == CH_MARKET_DATA:
                precio_actual = payload.get('Close_Price', 0)
                
                if ORDENES_ABIERTAS:
                    pnl_flotante = 0.0
                    for orden in ORDENES_ABIERTAS:
                        if orden['tipo'] == 'BUY':
                            pnl_flotante += (precio_actual - orden['entrada'])
                        else:
                            pnl_flotante += (orden['entrada'] - precio_actual)
                    
                    # Control de SL Diario
                    if (PNL_DIARIO_ACUMULADO + pnl_flotante) <= SL_MAXIMO_DIARIO:
                        print(f"🚨 HOMEOTASIS: Corte de circuito en {ts}. Cerrando clúster.")
                        PNL_DIARIO_ACUMULADO += pnl_flotante
                        ORDENES_ABIERTAS = []
                    
                    # Informar al Monitor
                    health_payload = {
                        "Timestamp": ts,
                        "open_orders": len(ORDENES_ABIERTAS),
                        "floating_pnl": round(pnl_flotante, 2),
                        "daily_pnl": round(PNL_DIARIO_ACUMULADO, 2)
                    }
                    r.publish('homeostasis_status', json.dumps(health_payload))

if __name__ == "__main__":
    main()