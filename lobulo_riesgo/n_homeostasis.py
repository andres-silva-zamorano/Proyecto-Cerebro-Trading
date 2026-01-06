import redis
import json
import sys
import os
from rich.console import Console

# Asegurar que reconozca la raíz para importar config
sys.path.append(os.getcwd())
from config import *

console = Console()

def finalizar_cluster(r, pnl, regimen):
    """Informa el resultado y activa el fusible de seguridad temporal."""
    r.publish(CH_RESULTS, json.dumps({
        "win": pnl > 0, 
        "regimen": regimen, 
        "final_pnl": pnl
    }))
    # Bloqueo de 60 segundos (tiempo real) para evitar sobre-operar tras un cierre
    r.setex(f"{CH_BLOCK}_active", 60, "true") 
    console.print(f"\n[bold yellow]🏁 CLÚSTER CERRADO[/bold yellow] | PnL: [bold]{pnl:.2f}[/bold] | Reg: {regimen}")

def main():
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        pubsub = r.pubsub()
        pubsub.subscribe(CH_DECISION, CH_MARKET_DATA, CH_BRAIN_STATE)
    except Exception as e:
        console.print(f"[bold red]❌ Error de conexión en Homeostasis:[/bold red] {e}")
        return

    console.print(f"[bold red]🛡️ Homeostasis v3.5: Gestión de Ciclo Circadiano Activa[/bold red]")

    # --- ESTADO INTERNO ---
    ORDENES_ABIERTAS = []
    PNL_DIARIO_ACUMULADO = 0.0
    REGIMEN_ACTUAL = 0
    ULTIMA_FECHA = None  # Para detectar el cambio de día en el mercado

    for message in pubsub.listen():
        if message['type'] == 'message':
            canal = message['channel'].decode('utf-8')
            payload = json.loads(message['data'])

            # --- 1. DETECCIÓN DE CAMBIO DE DÍA (RESET DIARIO) ---
            ts_mercado = payload.get('Timestamp', '')
            if ts_mercado:
                # Extraemos la fecha (YYYY.MM.DD) del string '2024.09.16 00:01'
                fecha_actual = ts_mercado.split(' ')[0]
                
                if ULTIMA_FECHA is not None and fecha_actual != ULTIMA_FECHA:
                    # Si hay órdenes abiertas al cambio de día, las arrastramos, 
                    # pero el contador de pérdida cerrada vuelve a cero.
                    PNL_DIARIO_ACUMULADO = 0.0
                    console.print(f"\n[bold blue]🌅 NUEVO DÍA DETECTADO ({fecha_actual}):[/bold blue] Reset de PnL Diario.")
                
                ULTIMA_FECHA = fecha_actual

            # --- 2. GESTIÓN DE SEÑALES DE ENTRADA ---
            if canal == CH_DECISION:
                accion = payload.get('action')
                precio_entrada = payload.get('price_at_entry', 0)
                
                if accion in ["BUY", "SELL"]:
                    # Verificación de Stop Loss Diario
                    if PNL_DIARIO_ACUMULADO <= SL_MAXIMO_DIARIO:
                        console.print(f"[bold red]🚫 BLOQUEO:[/bold red] SL Diario alcanzado ({PNL_DIARIO_ACUMULADO:.2f}). Esperando nuevo día...")
                        continue

                    # Lógica de Coherencia: Si el clúster es BUY y llega un SELL (o viceversa),
                    # cerramos el clúster actual para "girar" la posición.
                    if ORDENES_ABIERTAS and ORDENES_ABIERTAS[0]['tipo'] != accion:
                        console.print(f"[bold orange]🔄 GIRO DE SENTIDO:[/bold orange] Cerrando {ORDENES_ABIERTAS[0]['tipo']} para abrir {accion}")
                        pnl_f_cierre = sum([(precio_entrada - o['entrada']) if o['tipo'] == 'BUY' else (o['entrada'] - precio_entrada) for o in ORDENES_ABIERTAS])
                        PNL_DIARIO_ACUMULADO += pnl_f_cierre
                        finalizar_cluster(r, pnl_f_cierre, REGIMEN_ACTUAL)
                        ORDENES_ABIERTAS = []

                    # Añadir orden al cúmulo
                    # Limitamos a 30 órdenes para no saturar el margen (ajustable)
                    if len(ORDENES_ABIERTAS) < 30:
                        ORDENES_ABIERTAS.append({
                            "tipo": accion, 
                            "entrada": precio_entrada
                        })
                        console.print(f"[green]📦 Nueva orden {len(ORDENES_ABIERTAS)}:[/green] {accion} @ {precio_entrada}")

            # --- 3. GESTIÓN DE CIERRE FORZADO ---
            elif canal == CH_BRAIN_STATE:
                nuevo_regimen = payload.get('regime_id', 0)
                # Si el régimen cambia bruscamente (ej. de Tendencia a Rango), podemos elegir cerrar.
                # Opcional: Descomenta si quieres cerrar todo al cambiar de régimen
                # if nuevo_regimen != REGIMEN_ACTUAL and ORDENES_ABIERTAS:
                #    ... lógica de cierre ...
                REGIMEN_ACTUAL = nuevo_regimen

            # --- 4. CÁLCULO DE PNL FLOTANTE Y SALIDAS POR OBJETIVO ---
            elif canal == CH_MARKET_DATA:
                precio_actual = payload.get('Close_Price', 0)
                pnl_flotante = 0.0
                
                if ORDENES_ABIERTAS:
                    # Calcular PnL de todas las órdenes
                    pnl_flotante = sum([(precio_actual - o['entrada']) if o['tipo'] == 'BUY' else (o['entrada'] - precio_actual) for o in ORDENES_ABIERTAS])

                    # A. Eutanasia por SL Diario (Protección Total)
                    if (PNL_DIARIO_ACUMULADO + pnl_flotante) <= SL_MAXIMO_DIARIO:
                        console.print("[bold white on red]💥 STOP LOSS DIARIO CRÍTICO ALCANZADO 💥[/bold white on red]")
                        PNL_DIARIO_ACUMULADO += pnl_flotante
                        finalizar_cluster(r, pnl_flotante, REGIMEN_ACTUAL)
                        ORDENES_ABIERTAS = []
                        pnl_flotante = 0.0
                    
                    # B. Take Profit del Cúmulo (Ajustable en config o aquí)
                    # Si el conjunto gana más de 500 unidades, cerramos y aseguramos.
                    elif pnl_flotante >= 500.0: 
                        console.print("[bold green]💰 OBJETIVO DE CÚMULO ALCANZADO 💰[/bold green]")
                        PNL_DIARIO_ACUMULADO += pnl_flotante
                        finalizar_cluster(r, pnl_flotante, REGIMEN_ACTUAL)
                        ORDENES_ABIERTAS = []
                        pnl_flotante = 0.0

                # --- 5. REPORTE CONSTANTE AL MONITOR ---
                r.publish(CH_HOMEOSTASIS, json.dumps({
                    "Timestamp": ts_mercado,
                    "open_orders": len(ORDENES_ABIERTAS),
                    "floating_pnl": round(pnl_flotante, 2),
                    "daily_pnl": round(PNL_DIARIO_ACUMULADO, 2)
                }))

if __name__ == "__main__":
    main()