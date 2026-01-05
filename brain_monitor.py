import redis
import json
import os
import sys
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

# Forzar a Windows a usar UTF-8 en la terminal
if sys.platform == "win32":
    os.system("chcp 65001 > nul")

from config import *

console = Console()

def generar_dashboard(view):
    # CAMBIO: Se usa expand=True en lugar de full_width
    table = Table(show_header=True, header_style="bold cyan", expand=True)
    table.add_column("Metrica", style="dim", width=20)
    table.add_column("Valor", justify="right")

    table.add_row("Reloj del Sistema", view["time"])
    table.add_row("Regimen Actual", f"[bold yellow]{view['regime']}[/bold yellow]")
    
    votos_str = ""
    for exp, voto in view["votos_activos"].items():
        icon = "OK" if voto > 0 else ("X" if voto < 0 else "-")
        votos_str += f"{exp}: {icon} ({voto}) | "
    
    table.add_section()
    table.add_row("Consenso Total", f"{view['consenso']:.2f}")
    table.add_row("Votos Activos", votos_str)
    
    table.add_section()
    table.add_row("Accion/Estado", f"[bold white on blue] {view['ultima_accion']} [/bold white on blue]")
    table.add_row("Ordenes en Cumulo", str(view["open_orders"]))
    
    color_pnl = "green" if view["daily_pnl"] >= 0 else "red"
    table.add_row("PnL Diario", f"[bold {color_pnl}]{view['daily_pnl']:.2f}[/bold {color_pnl}]")
    
    return Panel(table, title="MONITOR CEREBRO ALPHA", border_style="blue")

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    pubsub.subscribe(CH_MARKET_DATA, CH_BRAIN_STATE, CH_DECISION, CH_HOMEOSTASIS, CH_VOTES)

    view = {
        "time": "---", "regime": "N/A", "consenso": 0.0,
        "votos_activos": {}, "open_orders": 0, "daily_pnl": 0.0,
        "ultima_accion": "IDLE", "ultima_razon": "N/A"
    }

    # El refresh_per_second ayuda a no saturar la CPU del server
    with Live(generar_dashboard(view), refresh_per_second=2) as live:
        for message in pubsub.listen():
            if message['type'] == 'message':
                canal = message['channel'].decode('utf-8')
                data = json.loads(message['data'])

                if canal == CH_MARKET_DATA:
                    view["time"] = data.get('Timestamp', '---')
                elif canal == CH_BRAIN_STATE:
                    view["regime"] = data.get('regime_id', '?')
                elif canal == CH_VOTES:
                    view["votos_activos"][data['experto_id']] = data['voto']
                elif canal == CH_DECISION:
                    view["ultima_accion"] = data.get('action')
                    view["consenso"] = data.get('consenso', 0.0)
                elif canal == CH_HOMEOSTASIS:
                    view["open_orders"] = data.get('open_orders')
                    view["daily_pnl"] = data.get('daily_pnl')
                
                live.update(generar_dashboard(view))

if __name__ == "__main__":
    main()