import redis
import json
import os
import sys
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

# Forzar UTF-8 en Windows
if sys.platform == "win32":
    os.system("chcp 65001 > nul")

# Importar configuración global
sys.path.append(os.getcwd())
from config import *

console = Console()

def generar_dashboard(view):
    """
    Crea la interfaz visual del monitor usando Rich.
    """
    # 1. Cabecera con estatus de conexión
    last_update = view.get("last_seen", "N/A")
    status_color = "green" if view["is_active"] else "red"
    header_text = Text(f" STATUS: {'CONECTADO' if view['is_active'] else 'DESCONECTADO'} | ÚLTIMO PULSO: {last_update}", style=f"bold {status_color}")

    # 2. Tabla Principal de Métricas
    table = Table(show_header=True, header_style="bold cyan", expand=True, border_style="dim")
    table.add_column("Métrica de Mercado", style="dim")
    table.add_column("Valor Actual", justify="right")

    # Precio y Reloj
    table.add_row("Reloj Servidor (MT5)", f"[bold white]{view['time']}[/bold white]")
    table.add_row("Precio BTCUSD", f"[bold yellow]${view['price']:,.2f}[/bold yellow]")
    
    # Régimen y Estado Mental
    color_reg = "magenta" if int(view['regime']) > 4 else "cyan"
    table.add_row("Régimen de Mercado", f"[bold {color_reg}]ID: {view['regime']}[/bold {color_reg}]")
    
    # Consenso y Votos
    table.add_section()
    consenso = view['consenso']
    color_cons = "green" if consenso >= 0.75 else ("red" if consenso <= -0.75 else "white")
    table.add_row("CONSENSO TOTAL", f"[bold {color_cons}]{consenso:.2f}[/bold {color_cons}]")
    
    votos_str = ""
    for exp, voto in view["votos_activos"].items():
        icon = "▲" if voto > 0 else ("▼" if voto < 0 else "○")
        color = "green" if voto > 0 else ("red" if voto < 0 else "white")
        votos_str += f"[{color}]{exp}: {icon}[/] | "
    table.add_row("Votos Activos", votos_str)

    # Operativa Live
    table.add_section()
    table.add_row("Acción Sugerida", f"[bold white on blue] {view['ultima_accion']} [/bold white on blue]")
    table.add_row("Órdenes en Cúmulo", f"[bold]{view['open_orders']}[/bold] / 10")
    
    color_pnl = "green" if view["daily_pnl"] >= 0 else "red"
    table.add_row("PnL Diario (Broker)", f"[bold {color_pnl}]${view['daily_pnl']:,.2f}[/bold {color_pnl}]")

    return Panel(table, title="[bold blue]🧠 MONITOR CEREBRO ALPHA - LIVE BTCUSD[/]", subtitle=header_text, border_style="blue")

def main():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    
    # Nos suscribimos a todos los canales del sistema nervioso
    pubsub.subscribe(CH_MARKET_DATA, CH_BRAIN_STATE, CH_DECISION, CH_HOMEOSTASIS, CH_VOTES)

    view = {
        "time": "Sincronizando...", "price": 0.0, "regime": "0", "consenso": 0.0,
        "votos_activos": {}, "open_orders": 0, "daily_pnl": 0.0,
        "ultima_accion": "BUSCANDO ENTRADA", "is_active": False, "last_seen": "---"
    }

    with Live(generar_dashboard(view), refresh_per_second=4) as live:
        for message in pubsub.listen():
            if message['type'] == 'message':
                canal = message['channel'].decode('utf-8')
                data = json.loads(message['data'])
                
                # Actualizar latido
                view["is_active"] = True
                view["last_seen"] = datetime.now().strftime("%H:%M:%S")

                # Mapeo de canales a la vista
                if canal == CH_MARKET_DATA:
                    view["time"] = data.get('Timestamp', '---')
                    view["price"] = data.get('Close_Price', 0.0)
                
                elif canal == CH_BRAIN_STATE:
                    view["regime"] = str(data.get('regime_id', '0'))
                    view["consenso"] = data.get('consenso_actual', 0.0)
                
                elif canal == CH_VOTES:
                    view["votos_activos"][data['experto_id']] = data['voto']
                
                elif canal == CH_DECISION:
                    view["ultima_accion"] = f"DISPARO: {data.get('action')}"
                
                elif canal == CH_HOMEOSTASIS:
                    view["open_orders"] = data.get('open_orders', 0)
                    view["daily_pnl"] = data.get('daily_pnl', 0.0)
                
                live.update(generar_dashboard(view))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Monitor cerrado.[/]")