import redis
import json
import sys
import os
from rich.console import Console

# Asegurar importación de configuración global desde la raíz del proyecto
sys.path.append(os.getcwd())
from config import *

console = Console()

class HomeostasisBTC:
    def __init__(self):
        """
        Lóbulo de Riesgo (Amígdala): Capa de supervivencia financiera.
        Gestiona el PnL y los objetivos de salida por riesgo matemático.
        Sincronizado con el feedback real del broker para evitar lag en el monitor.
        """
        try:
            self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
            self.pubsub = self.r.pubsub()
            
            # Suscripción a canales vitales:
            # CH_MARKET_DATA: Para el cálculo de PnL flotante tick a tick.
            # CH_RESULTS: Para confirmar que el Gateway cerró la posición en MT5.
            self.pubsub.subscribe(CH_MARKET_DATA, CH_RESULTS)
            
            # Memoria operativa del organismo
            self.ordenes_activas = []
            self.pnl_diario_realizado = 0.0
            self.max_pnl_flotante = 0.0  # Marca de agua para el Trailing Stop
            
            # --- PARÁMETROS MAESTROS ALPHA (BTCUSD) ---
            self.tp_optimo = 236.11      # Objetivo de ganancia en USD
            self.trail_pct = 0.7979      # Protección del 79.79% del máximo
            self.trail_trigger = 100.0   # Activa trailing stop tras ganar $100
            
            console.print(f"[bold red]🛡️ Homeostasis v5.8.1: Sincronía de Cúmulo ACTIVA[/bold red]")
            console.print(f"[dim]Configuración: TP: ${self.tp_optimo} | Trail: {self.trail_pct*100:.1f}%[/dim]")
        except Exception as e:
            console.print(f"[bold red]❌ Error de conexión en Homeostasis:[/bold red] {e}")
            sys.exit(1)

    def publicar_estado(self, pnl_f=0.0):
        """
        Informa al bus de datos el estado actual para que el Monitor lo refleje.
        """
        status_payload = {
            "open_orders": len(self.ordenes_activas),
            "floating_pnl": round(pnl_f, 2),
            "daily_pnl": round(self.pnl_diario_realizado, 2)
        }
        self.r.publish(CH_HOMEOSTASIS, json.dumps(status_payload))

    def procesar(self):
        """
        Bucle de procesamiento síncrono que protege el capital.
        """
        for message in self.pubsub.listen():
            if message['type'] != 'message':
                continue
                
            canal = message['channel'].decode('utf-8')
            data = json.loads(message['data'])

            # --- 1. LATIDO DE MERCADO: CÁLCULO DE RIESGO ---
            if canal == CH_MARKET_DATA:
                if not self.ordenes_activas:
                    self.publicar_estado(0.0)
                    continue

                precio_actual = data.get('Close_Price', 0)
                pnl_f = 0.0
                
                # Cálculo de PnL monetario basado en el volumen (0.01 lotes)
                for o in self.ordenes_activas:
                    diff = (precio_actual - o['entrada']) if o['tipo'] == 'BUY' else (o['entrada'] - precio_actual)
                    pnl_f += diff * o['volumen']
                
                # Actualizar marca de agua (High-Water Mark)
                if pnl_f > self.max_pnl_flotante:
                    self.max_pnl_flotante = pnl_f
                
                # Evaluación de Gatillos de Salida
                lanzar_cierre = False
                razon = ""

                # A. Take Profit Objetivo
                if pnl_f >= self.tp_optimo:
                    lanzar_cierre = True
                    razon = "OBJETIVO_GANANCIA"
                
                # B. Trailing Stop dinámico
                elif self.max_pnl_flotante > self.trail_trigger and pnl_f < (self.max_pnl_flotante * self.trail_pct):
                    lanzar_cierre = True
                    razon = "TRAILING_STOP_RIESGO"

                if lanzar_cierre:
                    self.r.publish(CH_DECISION, json.dumps({
                        "action": "CLOSE_ALL", 
                        "reason": razon
                    }))
                    console.print(f"[bold yellow]💰 GESTIÓN DE RIESGO:[/bold yellow] Ordenando cierre por {razon} (${pnl_f:.2f})")
                
                self.publicar_estado(pnl_f)

            # --- 2. SINCRONIZACIÓN FÍSICA: RESULTADOS DEL BROKER ---
            elif canal == CH_RESULTS:
                status = data.get('status')
                
                # Añadir orden al cúmulo solo si fue ejecutada en Pepperstone
                if status == 'executed':
                    self.ordenes_activas.append({
                        "tipo": data['action'], 
                        "entrada": data['price'],
                        "volumen": data.get('volume', 0.01), 
                        "ticket": data.get('ticket')
                    })
                    console.print(f"[bold green]✅ CÚMULO SYNC:[/bold green] {data['action']} agregada.")

                # Limpiar cúmulo solo si el Gateway confirma el cierre físico
                elif status == 'closed':
                    pnl_cierre = data.get('final_pnl', 0.0)
                    self.pnl_diario_realizado += pnl_cierre
                    self.ordenes_activas = []
                    self.max_pnl_flotante = 0.0
                    
                    # Bloqueo de refractariedad para estabilizar el sistema (15 segundos)
                    self.r.setex(f"{CH_BLOCK}_active", 15, "true")
                    
                    console.print(f"[bold blue]🔄 RESET HOMEOTASIS:[/bold blue] Operaciones liquidadas. PnL Real: ${pnl_cierre:.2f}")
                
                # Refrescar monitor inmediatamente tras cambio en las órdenes
                self.publicar_estado()

if __name__ == "__main__":
    h = HomeostasisBTC()
    try:
        h.procesar()
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Lóbulo Homeostasis detenido.[/bold red]")