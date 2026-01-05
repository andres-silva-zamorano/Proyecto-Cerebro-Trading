import redis
import json
import sys
import os
from rich.console import Console

sys.path.append(os.getcwd())
from config import *

console = Console()

def finalizar_cluster(r, pnl, regimen):
    """Informa el resultado y bloquea la operativa temporalmente."""
    r.publish(CH_RESULTS, json.dumps({
        "win": pnl > 0, 
        "regimen": regimen, 
        "final_pnl": pnl
    }))
    r.setex(f"{CH_BLOCK}_active", 60, "true") # Bloqueo de 1 min para evitar ráfagas
    console.print(f"\n[bold yellow]🏁 CLÚSTER CERRADO[/bold yellow] | PnL: [bold]{pnl:.2f}[/bold]")

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    pubsub.subscribe(CH_DECISION, CH_MARKET_DATA, CH_BRAIN_STATE)

    console.print(f"[bold red]🛡️ Homeostasis v3.2: Liquidador de Cúmulos[/bold red]")

    ORDENES_ABIERTAS = []
    PNL_DIARIO_ACUMULADO = 0.0
    REGIMEN_ACTUAL = 0

    for message in pubsub.listen():
        if message['type'] == 'message':
            canal = message['channel'].decode('utf-8')
            payload = json.loads(message['data'])

            if canal == CH_BRAIN_STATE:
                REGIMEN_ACTUAL = payload.get('regime_id', 0)

            elif canal == CH_DECISION:
                accion = payload.get('action')
                
                if accion in ["BUY", "SELL"]:
                    if PNL_DIARIO_ACUMULADO <= SL_MAXIMO_DIARIO:
                        console.print("[bold red]🚫 BLOQUEO:[/bold red] Límite diario excedido.")
                        continue
                    
                    ORDENES_ABIERTAS.append({
                        "tipo": accion, 
                        "entrada": payload.get('price_at_entry', 0)
                    })
                    console.print(f"[green]📦 Nueva orden en cúmulo:[/green] {accion} | Total: {len(ORDENES_ABIERTAS)}")

                elif accion == "CLOSE_ALL" and ORDENES_ABIERTAS:
                    # Cierre forzado por lógica externa (ej. cambio de régimen)
                    finalizar_cluster(r, 0.0, REGIMEN_ACTUAL) # PnL neutral o calculado
                    ORDENES_ABIERTAS = []

            elif canal == CH_MARKET_DATA:
                precio = payload.get('Close_Price', 0)
                pnl_f = 0.0
                if ORDENES_ABIERTAS:
                    pnl_f = sum([(precio - o['entrada']) if o['tipo'] == 'BUY' else (o['entrada'] - precio) for o in ORDENES_ABIERTAS])

                    # 1. Eutanasia por SL Diario (Protección de cuenta)
                    if (PNL_DIARIO_ACUMULADO + pnl_f) <= SL_MAXIMO_DIARIO:
                        console.print("[bold white on red]💥 STOP LOSS DIARIO ALCANZADO 💥[/bold white on red]")
                        finalizar_cluster(r, pnl_f, REGIMEN_ACTUAL)
                        PNL_DIARIO_ACUMULADO += pnl_f
                        ORDENES_ABIERTAS = []
                        pnl_f = 0.0
                    
                    # 2. Cierre por Take Profit del Cúmulo (Opcional, ajustable)
                    elif pnl_f >= 1000.0: 
                        finalizar_cluster(r, pnl_f, REGIMEN_ACTUAL)
                        PNL_DIARIO_ACUMULADO += pnl_f
                        ORDENES_ABIERTAS = []
                        pnl_f = 0.0

                # Reportar estado actual al monitor
                r.publish(CH_HOMEOSTASIS, json.dumps({
                    "Timestamp": payload.get('Timestamp'),
                    "open_orders": len(ORDENES_ABIERTAS),
                    "floating_pnl": round(pnl_f, 2),
                    "daily_pnl": round(PNL_DIARIO_ACUMULADO, 2)
                }))

if __name__ == "__main__":
    main()