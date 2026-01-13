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

# Asegurar importación de la configuración global
sys.path.append(os.getcwd())
from config import *

console = Console()

def generar_dashboard(view):
    """
    Construye la interfaz visual v3.9.2 optimizada para Visión Global.
    Muestra la confluencia fractal real (M1 vs M15 diferenciado).
    """
    last_update = view.get("last_seen", "---")
    status_color = "green" if view["is_active"] else "red"
    header_text = Text(f" STATUS: {'CONECTADO' if view['is_active'] else 'DESCONECTADO'} | ÚLTIMO TICK: {last_update}", style=f"bold {status_color}")

    # --- 1. PANEL DE MERCADO FRACTAL (M1 + M15 DIFERENCIADO) ---
    market_table = Table(show_header=False, expand=True, box=None)
    market_table.add_column("Propiedad", style="cyan", width=25)
    market_table.add_column("Valor", justify="right")

    market_table.add_row("Precio BTCUSD", f"[bold yellow]${view['price']:,.2f}[/bold yellow]")
    
    desc_reg = {
        "0": "CANAL LATERAL", 
        "1": "C. ALCISTA (V↓)", "2": "C. BAJISTA (V↓)",
        "3": "C. ALCISTA (V↑)", "4": "C. BAJISTA (V↑)",
        "5": "TENDENCIA ALCISTA", "6": "TENDENCIA BAJISTA"
    }
    
    # Régimen Operativo (M1) - Datos de alta frecuencia
    id_m1 = str(view['regime'])
    col_m1 = "green" if id_m1 in ["1", "3", "5"] else ("red" if id_m1 in ["2", "4", "6"] else "cyan")
    market_table.add_row("Régimen Micro (M1)", f"[bold {col_m1}]R{id_m1} ({desc_reg.get(id_m1, '---')})[/]")
    
    # Estructura Macro (M15) - El Filtro Fractal Real v3.9.2
    id_htf = str(view.get('regime_htf', 0))
    col_htf = "green" if id_htf in ["1", "3", "5"] else ("red" if id_htf in ["2", "4", "6"] else "cyan")
    
    # Lógica de Sincronía: Deben coincidir en polaridad y no ser Canal
    alineados = (col_m1 == col_htf and id_m1 != "0" and id_htf != "0")
    alineacion_txt = "[bold green]🔗 SINCRONIZADO[/]" if alineados else "[bold red]❌ DESALINEADO[/]"
    
    market_table.add_row("Estructura Macro (M15)", f"[bold {col_htf}]R{id_htf} ({desc_reg.get(id_htf, '---')})[/]")
    market_table.add_row("Estado de Confluencia", alineacion_txt)

    # --- 2. COMITÉ DE DECISIÓN ALPHA ---
    voter_table = Table(title="🗳️ COMITÉ DE DECISIÓN PONDERADA", title_style="bold magenta", expand=True, box=box.DOUBLE_EDGE, border_style="magenta")
    voter_table.add_column("Votante", style="bold white")
    voter_table.add_column("Voto", justify="center")
    voter_table.add_column("Confianza / Peso", justify="right")
    
    committee_members = [
        ("IA Visual (Estructura H5)", "ia_visual_alpha_v1"),
        ("Momentum (Energía BTC)", "momentum_v1"),
        ("Tálamo (Contexto Fractal)", "talamo_v1"),
        ("Vestibular (Filtro Ruido)", "guardian_vestibular_v1")
    ]

    for label, expert_id in committee_members:
        info = view["votos_activos"].get(expert_id, {"voto": 0, "confianza": 0.0})
        voto = info["voto"]
        conf = info["confianza"]

        if expert_id == "guardian_vestibular_v1":
            status_icon = "⚖️ OK" if view["pot_vest"] > 0.5 else "⚠️ RUIDO"
            color = "green" if view["pot_vest"] > 0.5 else "red"
            voter_table.add_row(label, f"[{color}]{status_icon}[/]", f"[bold white]{view['pot_vest']:.1f}x[/]")
        else:
            icon = "▲ BUY" if voto > 0 else ("▼ SELL" if voto < 0 else "○ NEUTRAL")
            color = "green" if voto > 0 else ("red" if voto < 0 else "white")
            voter_table.add_row(label, f"[{color}]{icon}[/]", f"[bold white]{conf:.0%}[/]")

    # --- 3. ESTADO OPERATIVO Y RÁFAGAS ---
    risk_table = Table(show_header=False, expand=True, box=None)
    risk_table.add_column("Propiedad", style="dim", width=25)
    risk_table.add_column("Valor", justify="right")

    consenso = view['consenso']
    color_cons = "green" if consenso >= 0.75 else ("red" if consenso <= -0.75 else "white")
    risk_table.add_row("CONSENSO COLECTIVO", f"[bold {color_cons}]{consenso:.2f}[/bold {color_cons}]")
    
    risk_table.add_row("Acción Actual", f"[bold white on blue] {view['ultima_accion']} [/bold white on blue]")
    
    # Contador de ráfagas (Límite de 10 órdenes)
    orders_text = f"[bold]{view['open_orders']}[/bold] / {MAX_ORDENES_CUMULO}"
    if view['open_orders'] >= 10:
        orders_text = f"[bold blink red]CÚMULO LLENO {view['open_orders']}/{MAX_ORDENES_CUMULO}[/]"
    elif view['open_orders'] > 1:
        orders_text += " [bold magenta]🔥 RÁFAGA ACTIVA[/]"
    
    risk_table.add_row("Órdenes en Cúmulo", orders_text)
    
    color_pnl = "green" if view["daily_pnl"] >= 0 else "red"
    risk_table.add_row("PnL Diario Realizado", f"[bold {color_pnl}]${view['daily_pnl']:,.2f}[/bold {color_pnl}]")

    # --- ENSAMBLAJE FINAL ---
    layout = Layout()
    layout.split_column(
        Layout(Panel(market_table, title="[bold blue]📊 ANÁLISIS FRACTAL M1+M15 (REAL)[/]", border_style="blue"), size=8),
        Layout(voter_table),
        Layout(Panel(risk_table, title="[bold yellow]🛡️ OPERATIVA Y RÁFAGAS[/]", border_style="yellow"), size=8)
    )

    return Panel(layout, title="[bold cyan]🧠 MONITOR CEREBRO ALPHA v3.9.2 - LIVE[/]", subtitle=header_text, border_style="cyan")

def main():
    """
    Bucle principal del Monitor.
    Sincronizado con la Médula Espinal (Redis).
    """
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    pubsub = r.pubsub()
    
    # Suscripción a los canales vitales
    pubsub.subscribe(
        CH_MARKET_DATA, CH_BRAIN_STATE, CH_DECISION, 
        CH_HOMEOSTASIS, CH_VOTES, CH_BRAIN_PULSE, CH_VESTIBULAR
    )

    view = {
        "price": 0.0, "regime": "0", "regime_htf": 0, "consenso": 0.0,
        "votos_activos": {}, "open_orders": 0, "daily_pnl": 0.0,
        "ultima_accion": "SINCRONIZANDO...", "is_active": False, 
        "last_seen": "---", "pot_vest": 1.0
    }

    print("🚀 Monitor Alpha v3.9.2 Iniciado. Esperando pulso fractal diferenciado...")

    with Live(generar_dashboard(view), refresh_per_second=4, screen=False) as live:
        for message in pubsub.listen():
            if message['type'] == 'message':
                canal = message['channel'].decode('utf-8')
                data = json.loads(message['data'])
                
                view["is_active"] = True
                view["last_seen"] = datetime.now().strftime("%H:%M:%S")

                if canal == CH_MARKET_DATA:
                    view["price"] = data.get('Close_Price', 0.0)
                
                elif canal == CH_BRAIN_PULSE:
                    # Capturamos ambos regímenes para la visualización fractal real
                    view["regime"] = str(data.get('regime_id', '0'))
                    view["regime_htf"] = data.get('regime_htf', 0)
                
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
                        view["ultima_accion"] = f"LIQUIDANDO: {data.get('reason', 'Duda')}"
                    else:
                        view["ultima_accion"] = f"DISPARO: {accion}"
                
                elif canal == CH_HOMEOSTASIS:
                    view["open_orders"] = data.get('open_orders', 0)
                    view["daily_pnl"] = data.get('daily_pnl', 0.0)
                
                live.update(generar_dashboard(view))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Monitor apagado.[/]")
    except Exception as e:
        console.print(f"\n[bold red]❌ Error crítico: {e}[/]")