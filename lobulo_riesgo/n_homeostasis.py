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
        Lóbulo de Supervivencia v5.8.4 (Amígdala Digital).
        Misión: Vigilancia financiera del clúster de ráfagas fractales.
        Gestiona el PnL colectivo de hasta 10 órdenes sincronizadas con MetaTrader 5.
        """
        try:
            # Conexión a la Médula Espinal (Redis)
            self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
            self.pubsub = self.r.pubsub()
            
            # Suscripción integral:
            # CH_MARKET_DATA: Para el cálculo de PnL flotante agregado en tiempo real.
            # CH_RESULTS: Confirmación física de ejecuciones y cierres desde el broker.
            self.pubsub.subscribe(CH_MARKET_DATA, CH_RESULTS)
            
            # Memoria operativa del cúmulo (Cluster Memory)
            self.ordenes_activas = []
            self.pnl_diario_realizado = 0.0
            self.max_pnl_flotante = 0.0  # Marca de agua (High-Water Mark)
            
            # --- PARÁMETROS MAESTROS ALPHA v3.9 (Optimizados para BTCUSD) ---
            self.tp_optimo = 236.11      # Take Profit objetivo para el clúster total ($ USD)
            self.trail_pct = 0.7979      # Protege el 79.79% del beneficio máximo alcanzado
            self.trail_trigger = 100.0   # Activa la lógica de trailing tras superar los $100 USD
            
            console.print(f"[bold red]🛡️ Homeostasis v5.8.4: Vigilancia de Ráfagas ACTIVA[/bold red]")
            console.print(f"[dim]Límite Cluster: {MAX_ORDENES_CUMULO} | TP Maestro: ${self.tp_optimo}[/dim]")
        except Exception as e:
            console.print(f"[bold red]❌ Error de conexión en Homeostasis:[/bold red] {e}")
            sys.exit(1)

    def publicar_estado(self, pnl_f=0.0):
        """
        Actualiza el Monitor Alpha v3.9.2 con la salud financiera del organismo.
        """
        status_payload = {
            "open_orders": len(self.ordenes_activas),
            "floating_pnl": round(pnl_f, 2),
            "daily_pnl": round(self.pnl_diario_realizado, 2)
        }
        self.r.publish(CH_HOMEOSTASIS, json.dumps(status_payload))

    def procesar(self):
        """
        Bucle principal de vigilancia síncrona.
        """
        for message in self.pubsub.listen():
            if message['type'] != 'message':
                continue
                
            canal = message['channel'].decode('utf-8')
            data = json.loads(message['data'])

            # --- 1. SEGUIMIENTO DE RIESGO DEL CLÚSTER (Ticks de Mercado) ---
            if canal == CH_MARKET_DATA:
                if not self.ordenes_activas:
                    self.publicar_estado(0.0)
                    continue

                precio_actual = data.get('Close_Price', 0)
                pnl_f_cluster = 0.0
                
                # Calculamos el PnL sumado de todas las posiciones de la ráfaga
                for o in self.ordenes_activas:
                    # Diferencial de precio x volumen (lotes 0.01 estándar)
                    diff = (precio_actual - o['entrada']) if o['tipo'] == 'BUY' else (o['entrada'] - precio_actual)
                    pnl_f_cluster += diff * o['volumen']
                
                # Actualizar High-Water Mark para el Trailing Stop del grupo
                if pnl_f_cluster > self.max_pnl_flotante:
                    self.max_pnl_flotante = pnl_f_cluster
                
                # Evaluación de Gatillos de Liquidación de Emergencia
                lanzar_cierre = False
                motivo = ""

                # A. Take Profit Global del Cúmulo
                if pnl_f_cluster >= self.tp_optimo:
                    lanzar_cierre = True
                    motivo = "CLUSTER_TP_ALCANZADO"
                
                # B. Trailing Stop del Cúmulo (Protección de rachas ganadoras)
                elif self.max_pnl_flotante > self.trail_trigger and pnl_f_cluster < (self.max_pnl_flotante * self.trail_pct):
                    lanzar_cierre = True
                    motivo = "CLUSTER_TRAILING_STOP"

                if lanzar_cierre:
                    # Orden de liquidación física inmediata para todo el grupo
                    self.r.publish(CH_DECISION, json.dumps({
                        "action": "CLOSE_ALL", 
                        "reason": motivo
                    }))
                    console.print(f"[bold yellow]💰 SUPERVIVENCIA ({motivo}):[/bold yellow] Liquidando clúster de {len(self.ordenes_activas)} órdenes.")
                
                # Notificar al monitor el flotante del clúster
                self.publicar_estado(pnl_f_cluster)

            # --- 2. SINCRONIZACIÓN DE REALIDAD (Confirmaciones del Broker) ---
            elif canal == CH_RESULTS:
                status = data.get('status')
                
                # Confirmación de que una nueva orden de la ráfaga entró al mercado
                if status == 'executed':
                    self.ordenes_activas.append({
                        "tipo": data['action'], 
                        "entrada": data['price'],
                        "volumen": data.get('volume', 0.01), 
                        "ticket": data.get('ticket')
                    })
                    console.print(f"[bold green]✅ CÚMULO SYNC:[/bold green] Orden {len(self.ordenes_activas)} integrada al clúster.")

                # Confirmación de que todo el clúster fue liquidado exitosamente
                elif status == 'closed':
                    pnl_cierre = data.get('final_pnl', 0.0)
                    self.pnl_diario_realizado += pnl_cierre
                    
                    # Limpieza total de la memoria operativa
                    self.ordenes_activas = []
                    self.max_pnl_flotante = 0.0
                    
                    # Bloqueo de refractariedad (15 segundos) para estabilizar el sistema post-cierre
                    self.r.setex(f"{CH_BLOCK}_active", 15, "true")
                    
                    console.print(f"[bold blue]🔄 RESET CLÚSTER:[/bold blue] Liquidación física confirmada. PnL: ${pnl_cierre:.2f}")
                
                # Manejo de fallos físicos en Pepperstone (Seguridad Vision Global)
                elif status == 'error_cierre':
                    console.print(f"[bold red]⚠️ ALERTA CRÍTICA:[/bold red] MT5 falló al cerrar. Manteniendo clúster en memoria para reintento.")

                # Forzar actualización visual inmediata tras cambios en el cúmulo
                self.publicar_estado()

if __name__ == "__main__":
    h = HomeostasisBTC()
    try:
        h.procesar()
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Lóbulo Homeostasis detenido por el usuario.[/bold red]")