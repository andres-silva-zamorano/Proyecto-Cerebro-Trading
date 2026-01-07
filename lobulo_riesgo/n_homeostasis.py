import redis, json, sys, os
from rich.console import Console
sys.path.append(os.getcwd())
from config import *
console = Console()

def finalizar_cluster(r, pnl, regimen, razon=""):
    r.publish(CH_RESULTS, json.dumps({"win": pnl > 0, "regimen": regimen, "final_pnl": pnl, "razon": razon}))
    r.setex(f"{CH_BLOCK}_active", 10, "true") 
    console.print(f"\n[bold yellow]🏁 CIERRE {razon}:[/bold yellow] PnL Realizado: [bold]{pnl:.2f}[/bold]")

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    pubsub.subscribe(CH_DECISION, CH_MARKET_DATA, CH_BRAIN_STATE)

    ORDENES_ABIERTAS = []
    PNL_DIARIO_ACUMULADO = 0.0
    PNL_TOTAL_HISTORICO = 0.0
    ULTIMA_FECHA = None
    MAX_PNL_FLOTANTE = 0.0

    # PARÁMETROS MAESTROS DE OPTUNA
    TP_OPTIMO = 236.11
    TRAIL_PCT = 0.7979
    UMBRAL_CIERRE = 0.2837
    MAX_ORDENES = 10

    console.print(f"[bold red]🛡️ Homeostasis v5.2: OPTUNA-EDITION[/bold red]")
    console.print(f"[dim]TP: {TP_OPTIMO} | Trail: {TRAIL_PCT*100:.1f}% | Cierre: {UMBRAL_CIERRE} | MaxOrd: {MAX_ORDENES}[/dim]")

    for message in pubsub.listen():
        if message['type'] == 'message':
            canal = message['channel'].decode('utf-8')
            payload = json.loads(message['data'])

            if canal == CH_MARKET_DATA:
                ts = payload.get('Timestamp', '')
                precio = payload.get('Close_Price', 0)
                if ts:
                    fecha = ts.split(' ')[0]
                    if ULTIMA_FECHA and fecha > ULTIMA_FECHA:
                        if ORDENES_ABIERTAS:
                            pnl_eod = sum([(precio - o['entrada']) if o['tipo'] == 'BUY' else (o['entrada'] - precio) for o in ORDENES_ABIERTAS])
                            PNL_TOTAL_HISTORICO += (PNL_DIARIO_ACUMULADO + pnl_eod)
                            finalizar_cluster(r, pnl_eod, 0, "FIN_DIA_EOD")
                            ORDENES_ABIERTAS = []
                        else:
                            PNL_TOTAL_HISTORICO += PNL_DIARIO_ACUMULADO
                        PNL_DIARIO_ACUMULADO = 0.0
                        MAX_PNL_FLOTANTE = 0.0
                    ULTIMA_FECHA = fecha

                pnl_f = sum([(precio - o['entrada']) if o['tipo'] == 'BUY' else (o['entrada'] - precio) for o in ORDENES_ABIERTAS]) if ORDENES_ABIERTAS else 0.0
                if pnl_f > MAX_PNL_FLOTANTE: MAX_PNL_FLOTANTE = pnl_f
                
                # --- LÓGICA DE SALIDA MATEMÁTICA ---
                cerrar_monetario = False
                razon_m = ""

                if pnl_f >= TP_OPTIMO:
                    cerrar_monetario = True
                    razon_m = "OBJETIVO_OPTUNA"
                elif MAX_PNL_FLOTANTE > 100 and pnl_f < (MAX_PNL_FLOTANTE * TRAIL_PCT):
                    cerrar_monetario = True
                    razon_m = "TRAILING_OPTUNA"

                if cerrar_monetario:
                    PNL_DIARIO_ACUMULADO += pnl_f
                    finalizar_cluster(r, pnl_f, 0, razon_m)
                    ORDENES_ABIERTAS = []
                    MAX_PNL_FLOTANTE = 0.0
                    pnl_f = 0.0

                r.publish(CH_HOMEOSTASIS, json.dumps({
                    "Timestamp": ts, "open_orders": len(ORDENES_ABIERTAS),
                    "floating_pnl": round(pnl_f, 2), "daily_pnl": round(PNL_DIARIO_ACUMULADO, 2),
                    "total_pnl": round(PNL_TOTAL_HISTORICO + PNL_DIARIO_ACUMULADO + pnl_f, 2)
                }))

            elif canal == CH_BRAIN_STATE and ORDENES_ABIERTAS:
                consenso = payload.get('consenso_actual', 0.0)
                tipo = ORDENES_ABIERTAS[0]['tipo']
                # Cierre por umbral de duda detectado por Optuna
                if (tipo == "BUY" and consenso < UMBRAL_CIERRE) or (tipo == "SELL" and consenso > -UMBRAL_CIERRE):
                    precio_c = payload.get('Close_Price', 0)
                    pnl_c = sum([(precio_c - o['entrada']) if o['tipo'] == 'BUY' else (o['entrada'] - precio_c) for o in ORDENES_ABIERTAS])
                    PNL_DIARIO_ACUMULADO += pnl_c
                    finalizar_cluster(r, pnl_c, payload.get('regime_id'), "CONVICCION_BAJA_OPTUNA")
                    ORDENES_ABIERTAS = []
                    MAX_PNL_FLOTANTE = 0.0

            elif canal == CH_DECISION:
                if PNL_DIARIO_ACUMULADO > SL_MAXIMO_DIARIO and len(ORDENES_ABIERTAS) < MAX_ORDENES:
                    ORDENES_ABIERTAS.append({"tipo": payload['action'], "entrada": payload['price_at_entry']})

if __name__ == "__main__": main()