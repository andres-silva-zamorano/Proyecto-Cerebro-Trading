import redis
import json
import os
import sys
from rich.console import Console

# Asegurar que reconozca la raíz para importar config
sys.path.append(os.getcwd())
from config import *

console = Console()

class EjecutorMaestro:
    def __init__(self):
        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        self.matriz_reputacion = self.cargar_pesos()
        
        # MEMORIA SENSORIAL Y DE CLÚSTER
        self.votos_actuales = {}           
        self.expertos_en_el_cluster = set() 
        
        self.guardar_matriz()
        console.print("[bold green]🏛️ Lóbulo Prefrontal:[/bold green] Gestión de Cúmulos y Reputación Activa.")

    def cargar_pesos(self):
        if os.path.exists(PATH_MATRIZ_REPUTACION):
            try:
                with open(PATH_MATRIZ_REPUTACION, 'r') as f:
                    return json.load(f)
            except: pass
        # Crea estructura para los 7 regímenes si no existe
        return {str(i): {} for i in range(7)}

    def guardar_matriz(self):
        os.makedirs(os.path.dirname(PATH_MATRIZ_REPUTACION), exist_ok=True)
        with open(PATH_MATRIZ_REPUTACION, 'w') as f:
            json.dump(self.matriz_reputacion, f, indent=4)

    def aprender_y_limpiar(self, reporte):
        """Ajusta pesos según el resultado del cluster y limpia la mesa."""
        reg = str(reporte['regimen'])
        win = reporte['win']
        pnl = reporte.get('final_pnl', 0)
        
        console.print(f"\n[bold magenta]🧠 APRENDIZAJE:[/bold magenta] Cluster en Reg {reg} | ¿Ganó?: {win} | PnL: {pnl:.2f}")

        for exp_id in self.expertos_en_el_cluster:
            if exp_id not in self.matriz_reputacion[reg]:
                self.matriz_reputacion[reg][exp_id] = 1.0
            
            # Recompensa/Castigo ponderado
            cambio = 0.10 if win else -0.25
            nuevo_peso = self.matriz_reputacion[reg][exp_id] + cambio
            self.matriz_reputacion[reg][exp_id] = round(max(0.1, min(5.0, nuevo_peso)), 2)
            
            color = "green" if cambio > 0 else "red"
            console.print(f"   [dim]→ {exp_id:20}:[/dim] [{color}]{self.matriz_reputacion[reg][exp_id]}[/{color}]")

        self.guardar_matriz()
        self.expertos_en_el_cluster.clear() # Reset escuadrón
        self.votos_actuales.clear()        # Limpia votos viejos
        console.print("[italic gray]🧹 Mesa limpia. Esperando nuevos votos.[/italic gray]")

    def decidir(self, regime_id, price, timestamp):
        reg = str(regime_id)
        
        # El canal de bloqueo impide abrir órdenes si hubo un cierre reciente o SL Diario
        if self.r.exists(f"{CH_BLOCK}_active"):
            return

        voto_final = 0.0
        participantes_del_pulso = []

        # Suma Sináptica Ponderada por Reputación del Régimen
        for exp_id, voto in self.votos_actuales.items():
            if voto != 0:
                peso = self.matriz_reputacion.get(reg, {}).get(exp_id, 1.0)
                voto_final += (voto * peso)
                participantes_del_pulso.append(exp_id)

        # Umbral de disparo (Potencial de Acción)
        if abs(voto_final) >= 0.7:
            accion = "BUY" if voto_final > 0 else "SELL"
            
            # Registramos quiénes causaron este movimiento para el aprendizaje
            self.expertos_en_el_cluster.update(participantes_del_pulso)

            payload = {
                "action": accion,
                "price_at_entry": price,
                "regime": regime_id,
                "consenso": round(voto_final, 2),
                "Timestamp": timestamp,
                "reason": f"Consenso Ponderado: {voto_final:.2f}"
            }
            self.r.publish(CH_DECISION, json.dumps(payload))
            console.print(f"[bold cyan]🚀 DISPARO:[/bold cyan] {accion} | Consenso: {voto_final:.2f} | Reg: {reg}")

def main():
    e = EjecutorMaestro()
    pubsub = e.r.pubsub()
    pubsub.subscribe(CH_VOTES, CH_RESULTS, CH_BRAIN_STATE)

    console.print("--- [bold white]🏛️ Ejecutor Maestro: Comandante de Cúmulos[/bold white] ---")

    for message in pubsub.listen():
        if message['type'] == 'message':
            canal = message['channel'].decode('utf-8')
            data = json.loads(message['data'])

            if canal == CH_VOTES:
                e.votos_actuales[data['experto_id']] = data['voto']
            elif canal == CH_RESULTS:
                e.aprender_y_limpiar(data)
            elif canal == CH_BRAIN_STATE:
                e.decidir(data['regime_id'], data['Close_Price'], data['Timestamp'])

if __name__ == "__main__":
    main()