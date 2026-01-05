import redis
import json
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA, CH_VISUAL, CH_BRAIN_STATE

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    pubsub.subscribe('brain_decision', CH_MARKET_DATA, CH_VISUAL, CH_BRAIN_STATE)

    print("--- Homeostasis Proactiva: Neurona de Salida Inteligente ---")

    ORDENES_ABIERTAS = []
    PNL_DIARIO = 0.0
    ULTIMA_CONFIANZA_IA = 0.0
    ULTIMA_ACCION_IA = "neutral"

    for message in pubsub.listen():
        if message['type'] == 'message':
            canal = message['channel'].decode('utf-8')
            payload = json.loads(message['data'])

            # A. Actualizar estado mental de la IA (para saber si las condiciones cambiaron)
            if canal == CH_VISUAL:
                ULTIMA_CONFIANZA_IA = payload.get('confidence', 0)
                ULTIMA_ACCION_IA = payload.get('fan_order', 'neutral')
            
            # B. Recibir Nueva Orden
            if canal == 'brain_decision':
                nueva_orden = {
                    "tipo": payload.get('action'),
                    "entrada": payload.get('price_at_entry', 0),
                    "confianza_inicio": payload.get('confidence', 0)
                }
                ORDENES_ABIERTAS.append(nueva_orden)

            # C. LÓGICA DE SALIDA INTELIGENTE (Cada Tick)
            elif canal == CH_MARKET_DATA and ORDENES_ABIERTAS:
                precio_actual = payload.get('Close_Price', 0)
                pnl_flotante = sum([(precio_actual - o['entrada']) if o['tipo'] == 'BUY' else (o['entrada'] - precio_actual) for o in ORDENES_ABIERTAS])

                cerrar_todo = False
                razon = ""

                # --- CIRCUITO DE DOPAMINA (Si vamos ganando) ---
                if pnl_flotante > 0:
                    # Si la IA cambia de opinión radicalmente o la confianza cae al suelo
                    if ULTIMA_ACCION_IA == "neutral" or ULTIMA_CONFIANZA_IA < 0.40:
                        cerrar_todo = True
                        razon = "PROTECCIÓN DE BENEFICIO: IA perdió interés."
                    # Si el abanico se pone en contra
                    tipo_actual = ORDENES_ABIERTAS[0]['tipo']
                    if (tipo_actual == "BUY" and ULTIMA_ACCION_IA == "bearish_alpha") or \
                       (tipo_actual == "SELL" and ULTIMA_ACCION_IA == "bullish_alpha"):
                        cerrar_todo = True
                        razon = "REVERSIÓN DETECTADA: IA cambió de bando."

                # --- CIRCUITO DE AVERSIÓN AL DOLOR (Si vamos perdiendo) ---
                else:
                    # Si la IA ya no cree en la recuperación
                    if ULTIMA_CONFIANZA_IA < 0.30:
                        cerrar_todo = True
                        razon = "EUTANASIA: IA ya no ve salida."

                # --- EJECUCIÓN DEL CIERRE ---
                if cerrar_todo:
                    print(f"🛑 CIERRE INTELIGENTE: {razon} | PnL Final: {pnl_flotante:.2f}")
                    PNL_DIARIO += pnl_flotante
                    ORDENES_ABIERTAS = []

                # Informar al Monitor
                r.publish('homeostasis_status', json.dumps({
                    "Timestamp": payload.get('Timestamp'),
                    "open_orders": len(ORDENES_ABIERTAS),
                    "floating_pnl": round(pnl_flotante, 2),
                    "daily_pnl": round(PNL_DIARIO, 2)
                }))

if __name__ == "__main__":
    main()