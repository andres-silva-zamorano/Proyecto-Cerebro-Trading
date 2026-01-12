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
from rich import box

# Forzar UTF-8 en terminales Windows para evitar errores con iconos y bordes
if sys.platform == "win32":
    os.system("chcp 65001 > nul")

# Asegurar importación de configuración global desde la raíz
sys.path.append(os.getcwd())
from config import *

console = Console()

def generar_dashboard(view):
    """
    Construye la interfaz visual avanzada del monitor.
    Organiza la información en tres paneles: Mercado, Comité y Riesgo.
    """
    last_update = view.get("last_seen", "---")
    status_color = "green" if view["is_active"] else "red"
    header_text = Text(f" STATUS: {'CONECTADO' if view['is_active'] else 'DESCONECTADO'} | ÚLTIMO TICK: {last_update}", style=f"bold {status_color}")

    # --- PANEL 1: SEÑALES DE MERCADO (Contexto) ---
    market_table = Table(show_header=False, expand=True, box=None)
    market_table.add_column("Propiedad", style="cyan", width=25)
    market_table.add_column("Valor", justify="right")

    market_table.add_row("Reloj Servidor (MT5)", f"[bold white]{view['time']}[/bold white]")
    market_table.add_row("Precio BTCUSD", f"[bold yellow]${view['price']:,.2f}[/bold yellow]")
    
    id_reg = str(view['regime'])
    desc_reg = {
        "0": "CANAL LATERAL", 
        "1": "C. ALCISTA (V↓)", "2": "C. BAJISTA (V↓)",
        "3": "C. ALCISTA (V↑)", "4": "C. BAJISTA (V↑)",
        "5": "TENDENCIA ALCISTA", "6": "TENDENCIA BAJISTA"
    }
    reg_color = "green" if id_reg in ["1", "3", "5"] else ("red" if id_reg in ["2", "4", "6"] else "cyan")
    market_table.add_row("Régimen Dominante", f"[bold {reg_color}]ID: {id_reg} ({desc_reg.get(id_reg, '---')})[/]")
    
    # Distribución Mental (Probabilidades del Tálamo H5)
    dist = view.get("distribution", {})
    prob_str = ""
    for i in range(7):
        p = dist.get(f"prob_regimen_{i}", 0.0)
        if p > 0.05:
            p_color = "green" if i in [1, 3, 5] else ("red" if i in [2, 4, 6] else "white")
            prob_str += f"[{p_color}]R{i}:{p:.0%}[/] "
    market_table.add_row("Distribución Mental", prob_str if prob_str else "[dim]Calculando probabilidades...[/dim]")

    # --- PANEL 2: COMITÉ DE DECISIÓN (Los 4 Votantes) ---
    voter_table = Table(title="🗳️ COMITÉ DE DECISIÓN ALPHA", title_style="bold magenta", expand=True, box=box.DOUBLE_EDGE, border_style="magenta")
    voter_table.add_column("Experto / Lóbulo", style="bold white")
    voter_table.add_column("Voto / Dirección", justify="center")
    voter_table.add_column("Confianza (Peso)", justify="right")

    # Mapeo de los 4 pilares de decisión
    committee_members = [
        ("IA Visual (Estructura H5)", "ia_visual_alpha_v1"),
        ("Momentum (Energía BTC)", "momentum_v1"),
        ("Tálamo (Contexto Votante)", "talamo_v1"),
        ("Vestibular (Filtro Ruido)", "guardian_vestibular_v1")
    ]

    for label, expert_id in committee_members:
        info = view["votos_activos"].get(expert_id, {"voto": 0, "confianza": 0.0})
        voto = info["voto"]
        conf = info["confianza"]

        if expert_id == "guardian_vestibular_v1":
            # El vestibular muestra su multiplicador de bloqueo
            status_icon = "⚖️ ESTABLE" if view["pot_vest"] > 0.5 else "⚠️ RUIDO ALTO"
            color = "green" if view["pot_vest"] > 0.5 else "red"
            voter_table.add_row(label, f"[{color}]{status_icon}[/]", f"[bold white]{view['pot_vest']:.1f}x[/]")
        else:
            icon = "▲ BUY" if voto > 0 else ("▼ SELL" if voto < 0 else "○ NEUTRAL")
            color = "green" if voto > 0 else ("red" if voto < 0 else "white")
            voter_table.add_row(label, f"[{color}]{icon}[/]", f"[bold white]{conf:.0%}[/]")

    # --- PANEL 3: SUPERVIVENCIA Y RIESGO (Ejecución) ---
    risk_table = Table(show_header=False, expand=True, box=None)
    risk_table.add_column("Propiedad", style="dim", width=25)
    risk_table.add_column("Valor", justify="right")

    consenso = view['consenso']
    color_cons = "green" if consenso >= 0.75 else ("red" if consenso <= -0.75 else "white")
    risk_table.add_row("CONSENSO TOTAL (FUERZA)", f"[bold {color_cons}]{consenso:.2f}[/bold {color_cons}]")
    
    risk_table.add_row("Acción Sugerida", f"[bold white on blue] {view['ultima_accion']} [/bold white on blue]")
    
    # Mostrar órdenes activas sincronizadas con CH_RESULTS
    risk_table.add_row("Órdenes en Cúmulo", f"[bold]{view['open_orders']}[/bold] / 10")
    
    color_pnl = "green" if view["daily_pnl"] >= 0 else "red"
    risk_table.add_row("PnL Diario Realizado", f"[bold {color_pnl}]${view['daily_pnl']:,.2f}[/bold {color_pnl}]")

    # --- ENSAMBLAJE DEL LAYOUT ---
    layout = Layout()
    layout.split_column(
        Layout(Panel(market_table, title="[bold blue]📊 LATIDOS DE MERCADO[/]", border_style="blue"), size=7),
        Layout(voter_table),
        Layout(Panel(risk_table, title="[bold yellow]🛡️ ESTADO OPERATIVO Y RIESGO[/]", border_style="yellow"), size=8)
    )

    return Panel(layout, title="[bold cyan]🧠 MONITOR CEREBRO ALPHA v3.8.1 - LIVE[/]", subtitle=header_text, border_style="cyan")

def main():
    """
    Hilo principal del monitor. Escucha todos los canales de Redis y actualiza la UI.
    """
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    
    # Suscripción integral para visión 360 del organismo
    pubsub.subscribe(
        CH_MARKET_DATA, CH_BRAIN_STATE, CH_DECISION, 
        CH_HOMEOSTASIS, CH_VOTES, CH_BRAIN_PULSE, CH_VESTIBULAR
    )

    # Estado inicial de la vista
    view = {
        "time": "Sincronizando...", "price": 0.0, "regime": "0", "consenso": 0.0,
        "votos_activos": {}, "open_orders": 0, "daily_pnl": 0.0, "distribution": {},
        "ultima_accion": "CALIBRANDO SENSORES", "is_active": False, "last_seen": "---",
        "pot_vest": 1.0
    }

    print("🚀 Monitor Alpha v3.8.1 iniciado. Esperando pulso de Redis...")

    with Live(generar_dashboard(view), refresh_per_second=4, screen=False) as live:
        for message in pubsub.listen():
            if message['type'] == 'message':
                canal = message['channel'].decode('utf-8')
                data = json.loads(message['data'])
                
                # Latido de conexión
                view["is_active"] = True
                view["last_seen"] = datetime.now().strftime("%H:%M:%S")

                # Procesamiento por canal
                if canal == CH_MARKET_DATA:
                    view["time"] = data.get('Timestamp', '---')
                    view["price"] = data.get('Close_Price', 0.0)
                
                elif canal == CH_BRAIN_PULSE:
                    view["regime"] = str(data.get('regime_id', '0'))
                    view["distribution"] = data.get('regime_distribution', {})
                
                elif canal == CH_BRAIN_STATE:
                    view["consenso"] = data.get('consenso_actual', 0.0)
                
                elif canal == CH_VOTES:
                    exp_id = data.get('experto_id')
                    view["votos_activos"][exp_id] = {
                        "voto": data.get('voto', 0),
                        "confianza": data.get('confianza', 0.0)
                    }
                
                elif canal == CH_VESTIBULAR:
                    view["pot_vest"] = data.get('action_potential', 1.0)
                
                elif canal == CH_DECISION:
                    accion = data.get('action')
                    if accion == "CLOSE_ALL":
                        view["ultima_accion"] = f"LIQUIDANDO: {data.get('reason', 'Consenso')}"
                    else:
                        view["ultima_accion"] = f"DISPARO: {accion}"
                
                elif canal == CH_HOMEOSTASIS:
                    view["open_orders"] = data.get('open_orders', 0)
                    view["daily_pnl"] = data.get('daily_pnl', 0.0)
                
                # Actualizar pantalla
                live.update(generar_dashboard(view))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Monitor detenido por el usuario.[/]")
    except Exception as e:
        console.print(f"\n[bold red]❌ Error crítico en Monitor: {e}[/]")