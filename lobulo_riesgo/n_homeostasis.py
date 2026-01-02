import redis
import json
import sys
import os

sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA, CH_VISUAL, CH_DECISION, CH_HOMEOSTASIS, SL_MAXIMO_DIARIO, CH_BLOCK

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    pubsub.subscribe(CH_DECISION, CH_MARKET_DATA, CH_VISUAL)

    print(f"--- 🛡️ Homeostasis: Límite Diario Configurado en {SL_MAXIMO_DIARIO} ---")

    ORDENES_ABIERTAS = []
    PNL_DIARIO_ACUMULADO = 0.0
    BLOQUEO_POR_DOLOR = False
    IA_STATE = {"order": "neutral", "conf": 0.0}

    for message in pubsub.listen():
        if message['type'] == 'message':
            canal = message['channel'].decode('utf-8')
            payload = json.loads(message['data'])

            # A. Actualizar estado de la IA
            if canal == CH_VISUAL:
                IA_STATE["order"] = payload.get('fan_order')
                IA_STATE["conf"] = payload.get('confidence', 0.0)

            # B. Registrar nuevas entradas (Solo si no hay bloqueo)
            if canal == CH_DECISION:
                if PNL_DIARIO_ACUMULADO <= SL_MAXIMO_DIARIO:
                    print("⚠️ Intento de apertura bloqueado: Límite de pérdida diaria alcanzado.")
                    continue
                
                ORDENES_ABIERTAS.append({
                    "tipo": payload.get('action'),
                    "entrada": payload.get('price_at_entry', 0)
                })

            # C. Gestión de Salida y Límite de Dolor
            elif canal == CH_MARKET_DATA and ORDENES_ABIERTAS:
                precio = payload.get('Close_Price', 0)
                pnl_flotante = sum([(precio - o['entrada']) if o['tipo'] == 'BUY' else (o['entrada'] - precio) for o in ORDENES_ABIERTAS])

                debe_cerrar = False
                motivo = ""

                # 1. VERIFICAR LÍMITE DE DOLOR (SL DIARIO)
                if (PNL_DIARIO_ACUMULADO + pnl_flotante) <= SL_MAXIMO_DIARIO:
                    debe_cerrar = True
                    motivo = f"💥 EUTANASIA TOTAL: Límite de dolor alcanzado ({SL_MAXIMO_DIARIO})"

                # 2. CIRCUITO DE COSECHA (Profit)
                elif pnl_flotante > 0 and IA_STATE["conf"] < 0.55:
                    debe_cerrar = True
                    motivo = "COSECHA: Pérdida de convicción IA"

                # 3. CIRCUITO DE EMERGENCIA (Duda IA en pérdida)
                elif pnl_flotante < 0 and IA_STATE["conf"] < 0.40:
                    debe_cerrar = True
                    motivo = "EUTANASIA ESTRATÉGICA: IA duda del recobro"

                if debe_cerrar:
                    print(f"✅ CIERRE EJECUTADO: {motivo} | PnL: {pnl_flotante:.2f}")
                    PNL_DIARIO_ACUMULADO += pnl_flotante
                    ORDENES_ABIERTAS = []
                    
                    # BLOQUEO USANDO CONFIG: Guardamos en Redis un flag temporal
                    # Usamos el nombre del canal como prefijo de la llave de bloqueo
                    r.setex(f"{CH_BLOCK}_active", 60, "true")

                # Informar estado al Monitor
                r.publish(CH_HOMEOSTASIS, json.dumps({
                    "Timestamp": payload.get('Timestamp'),
                    "open_orders": len(ORDENES_ABIERTAS),
                    "floating_pnl": round(pnl_flotante, 2),
                    "daily_pnl": round(PNL_DIARIO_ACUMULADO, 2)
                }))

if __name__ == "__main__":
    main()