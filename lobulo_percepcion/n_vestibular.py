import redis
import json
import sys
import os
from rich.console import Console

# Asegurar que reconozca la raíz para importar la configuración global
sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA, CH_BRAIN_PULSE, CH_VESTIBULAR, CH_BRAIN_STATE

console = Console()

class GuardianVestibular:
    def __init__(self):
        """
        Inicializa el filtro de equilibrio dinámico.
        Su función es monitorear el ruido (ATR) y compararlo con el régimen actual.
        """
        try:
            # Conexión a la Médula Espinal (Redis)
            self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
            self.pubsub = self.r.pubsub()
            
            # Escuchamos el Pulso del Tálamo (Regímenes) y el Sensor (Datos de Mercado/ATR)
            self.pubsub.subscribe(CH_MARKET_DATA, CH_BRAIN_PULSE)
            
            console.print("[bold blue]⚖️ Neurona Vestibular: Equilibrio Dinámico BTCUSD Activo[/bold blue]")
        except Exception as e:
            console.print(f"[bold red]❌ Error de conexión en Vestibular:[/bold red] {e}")
            sys.exit(1)

        # Estado inicial
        self.regimen_actual = 0
        
        # --- UMBRALES DE TOLERANCIA BTCUSD ---
        # Bitcoin es significativamente más volátil que el Forex tradicional.
        # Estos umbrales de ATR_Relativo están calibrados para la acción de precio de BTC.
        self.tolerancias = {
            "0": 0.0016, # Régimen 0: Rango/Lateral (Umbral estricto para evitar whipsaws)
            "3": 0.0025, # Régimen 3: Volatilidad/Giro (Permite más movimiento)
            "5": 0.0022, # Régimen 5: Tendencia Alcista (Permite respiración de tendencia)
            "6": 0.0022  # Régimen 6: Tendencia Bajista
        }

    def escuchar(self):
        """
        Bucle infinito de procesamiento de señales sensoriales.
        """
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                canal = message['channel'].decode('utf-8')
                data = json.loads(message['data'])
                
                # 1. ACTUALIZACIÓN DE RÉGIMEN (Desde el Tálamo)
                if canal == CH_BRAIN_PULSE:
                    # Guardamos el régimen detectado para la siguiente evaluación de ruido
                    self.regimen_actual = data.get('regime_id', 0)
                    continue 

                # 2. EVALUACIÓN DE RUIDO (Desde el MT5 Feeder)
                elif canal == CH_MARKET_DATA:
                    ts = data.get('Timestamp', 'N/A')
                    atr_rel = data.get('ATR_Rel', 0)
                    
                    # Seleccionamos la tolerancia basada en lo que el Tálamo dice del mercado
                    umbral_ruido = self.tolerancias.get(str(self.regimen_actual), 0.0018) # Default 0.0018
                    
                    # Verificamos si el mercado está "tranquilo" dentro de sus parámetros
                    is_stable = atr_rel < umbral_ruido
                    
                    # El 'action_potential' es el multiplicador de seguridad para el Ejecutor
                    # 1.0 = Permiso total para operar las señales de la IA
                    # 0.1 = Bloqueo casi total (neutraliza el consenso por ruido excesivo)
                    potencial = 1.0 if is_stable else 0.1
                    
                    vestibular_payload = {
                        "Timestamp": ts,
                        "regime_eval": self.regimen_actual,
                        "noise_level": round(atr_rel, 6),
                        "threshold_used": umbral_ruido,
                        "is_stable": is_stable,
                        "action_potential": potencial
                    }
                    
                    # Emitimos el juicio vestibular al sistema nervioso
                    self.r.publish(CH_VESTIBULAR, json.dumps(vestibular_payload))
                    
                    # Feedback visual para el log del orquestador
                    color = "green" if is_stable else "red"
                    status = "ESTABLE" if is_stable else "RUIDO ALTO"
                    console.print(f"⚖️ [{ts}] Reg:{self.regimen_actual} | Ruido:{atr_rel:.6f} vs {umbral_ruido} | [bold {color}]{status}[/bold {color}]")

if __name__ == "__main__":
    v = GuardianVestibular()
    try:
        v.escuchar()
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Lóbulo Vestibular apagado.[/bold red]")