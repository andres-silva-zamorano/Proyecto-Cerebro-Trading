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
        Lóbulo de Riesgo (Amígdala) v5.8.3.
        Misión: Vigilancia de PnL y disparo de liquidación por metas USD o Trailing Stop.
        Esta versión es pasiva: no abre órdenes, solo vigila y ordena el cierre.
        """
        try:
            # Conexión a la Médula Espinal (Redis)
            self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
            self.pubsub = self.r.pubsub()
            
            # Suscripción a canales críticos:
            # CH_MARKET_DATA: Para el cálculo de PnL flotante en cada tick de precio.
            # CH_RESULTS: Para recibir la confirmación FÍSICA de apertura/cierre desde MT5.
            self.pubsub.subscribe(CH_MARKET_DATA, CH_RESULTS)
            
            # Memoria operativa del organismo
            self.ordenes_activas = []
            self.pnl_diario_realizado = 0.0
            self.max_pnl_flotante = 0.0  # Marca de agua para el Trailing Stop (High-Water Mark)
            
            # --- PARÁMETROS MAESTROS ALPHA (BTCUSD) ---
            self.tp_optimo = 236.11      # Objetivo de ganancia en USD
            self.trail_pct = 0.7979      # Protección del 79.79% del profit máximo
            self.trail_trigger = 100.0   # Activa trailing tras ganar al menos $100 USD
            
            console.print(f"[bold red]🛡️ Homeostasis v5.8.3: Modo Supervivencia ACTIVO[/bold red]")
            console.print(f"[dim]Configuración: TP: ${self.tp_optimo} | Trail: {self.trail_pct*100:.1f}%[/dim]")
        except Exception as e:
            console.print(f"[bold red]❌ Error de conexión en Homeostasis:[/bold red] {e}")
            sys.exit(1)

    def publicar_estado(self, pnl_f=0.0):
        """
        Informa al bus de datos el estado financiero actual para el Monitor Alpha.
        """
        status_payload = {
            "open_orders": len(self.ordenes_activas),
            "floating_pnl": round(pnl_f, 2),
            "daily_pnl": round(self.pnl_diario_realizado, 2)
        }
        self.r.publish(CH_HOMEOSTASIS, json.dumps(status_payload))

    def procesar(self):
        """
        Bucle de procesamiento síncrono.
        """
        for message in self.pubsub.listen():
            if message['type'] != 'message':
                continue
                
            canal = message['channel'].decode('utf-8')
            data = json.loads(message['data'])

            # --- 1. SEGUIMIENTO DE RIESGO (Ticks de Mercado) ---
            if canal == CH_MARKET_DATA:
                if not self.ordenes_activas:
                    # Si no hay guerra, mantenemos el monitor en calma
                    self.publicar_estado(0.0)
                    continue

                precio_actual = data.get('Close_Price', 0)
                pnl_f = 0.0
                
                # Cálculo de PnL monetario real (Precio * Lote 0.01)
                for o in self.ordenes_activas:
                    diff = (precio_actual - o['entrada']) if o['tipo'] == 'BUY' else (o['entrada'] - precio_actual)
                    pnl_f += diff * o['volumen']
                
                # Actualizar marca de agua para el Trailing Stop
                if pnl_f > self.max_pnl_flotante:
                    self.max_pnl_flotante = pnl_f
                
                # Evaluación de Gatillos de Salida de Supervivencia
                lanzar_cierre = False
                motivo = ""

                # A. Take Profit Maestro
                if pnl_f >= self.tp_optimo:
                    lanzar_cierre = True
                    motivo = "OBJETIVO_GANANCIA_LOGRADO"
                
                # B. Trailing Stop (Protección de beneficios en vuelo)
                elif self.max_pnl_flotante > self.trail_trigger and pnl_f < (self.max_pnl_flotante * self.trail_pct):
                    lanzar_cierre = True
                    motivo = "TRAILING_STOP_ACTIVO"

                if lanzar_cierre:
                    # Ordenamos al Gateway la liquidación física inmediata
                    self.r.publish(CH_DECISION, json.dumps({
                        "action": "CLOSE_ALL", 
                        "reason": motivo
                    }))
                    console.print(f"[bold yellow]💰 RIESGO ({motivo}):[/bold yellow] Ordenando cierre de posiciones.")
                
                # Actualizar monitor con el flotante actual
                self.publicar_estado(pnl_f)

            # --- 2. SINCRONIZACIÓN DE REALIDAD (Confirmaciones del Gateway) ---
            elif canal == CH_RESULTS:
                status = data.get('status')
                
                # El Gateway confirma que la orden de apertura se ejecutó en MT5
                if status == 'executed':
                    self.ordenes_activas.append({
                        "tipo": data['action'], 
                        "entrada": data['price'],
                        "volumen": data.get('volume', 0.01), 
                        "ticket": data.get('ticket')
                    })
                    console.print(f"[bold green]✅ CÚMULO SYNC:[/bold green] Orden {data['action']} integrada a la memoria.")

                # El Gateway confirma que las posiciones se cerraron en MT5
                elif status == 'closed':
                    pnl_cierre = data.get('final_pnl', 0.0)
                    self.pnl_diario_realizado += pnl_cierre
                    self.ordenes_activas = []
                    self.max_pnl_flotante = 0.0
                    
                    # Activamos periodo refractario (15 segundos de calma)
                    self.r.setex(f"{CH_BLOCK}_active", 15, "true")
                    
                    console.print(f"[bold blue]🔄 RESET HOMEOTASIS:[/bold blue] Cierre real confirmado. PnL: ${pnl_cierre:.2f}")
                
                # El Gateway reporta un fallo crítico en MT5 (como el error NoneType)
                elif status == 'error_cierre':
                    console.print(f"[bold red]⚠️ ALERTA:[/bold red] MT5 falló al cerrar. Manteniendo órdenes en monitor para reintento.")

                # Forzamos actualización visual inmediata
                self.publicar_estado()

if __name__ == "__main__":
    h = HomeostasisBTC()
    try:
        h.procesar()
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Lóbulo Homeostasis detenido por el usuario.[/bold red]")