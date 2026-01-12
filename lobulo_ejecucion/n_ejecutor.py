import redis, json, os, sys
from rich.console import Console
sys.path.append(os.getcwd())
from config import *
console = Console()

class EjecutorMaestro:
    def __init__(self):
        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        self.matriz_reputacion = self.cargar_pesos()
        self.votos_actuales = {}

    def cargar_pesos(self):
        if os.path.exists(PATH_MATRIZ_REPUTACION):
            try:
                with open(PATH_MATRIZ_REPUTACION, 'r') as f: return json.load(f)
            except: pass
        return {str(i): {} for i in range(7)}

    def decidir(self, regime_id, price, timestamp):
        reg = str(regime_id)
        voto_final = 0.0
        # El guardián ahora es un multiplicador, no suma votos
        multiplicador_seguridad = 1.0 

        for exp_id, voto in self.votos_actuales.items():
            # El Guardián Vestibular no suma puntos, solo reduce el consenso si hay ruido
            if exp_id == "guardian_vestibular_v1":
                if voto == 0: multiplicador_seguridad = 0.1 # Bloqueo por ruido
                continue 
            
            # Solo sumamos votos de expertos reales (IA, Momentum, etc.)
            peso = self.matriz_reputacion.get(reg, {}).get(exp_id, 1.0)
            voto_final += (voto * peso)

        # Aplicamos el filtro de seguridad
        consenso_final = voto_final * multiplicador_seguridad

        self.r.publish(CH_BRAIN_STATE, json.dumps({
            "Timestamp": timestamp, "regime_id": regime_id,
            "Close_Price": price, "consenso_actual": round(consenso_final, 2)
        }))

        # Umbral de Optuna: 0.75
        if not self.r.exists(f"{CH_BLOCK}_active") and abs(consenso_final) >= 0.75:
            accion = "BUY" if consenso_final > 0 else "SELL"
            payload = {
                "action": accion, "price_at_entry": price, "regime": regime_id,
                "consenso": round(consenso_final, 2), "Timestamp": timestamp
            }
            self.r.publish(CH_DECISION, json.dumps(payload))
            console.print(f"[bold cyan]🚀 DISPARO VALIDADO:[/bold cyan] {accion} | Cons: {consenso_final:.2f}")

def main():
    e = EjecutorMaestro()
    pubsub = e.r.pubsub()
    pubsub.subscribe(CH_VOTES, CH_RESULTS, CH_BRAIN_PULSE)
    for message in pubsub.listen():
        if message['type'] == 'message':
            canal = message['channel'].decode('utf-8')
            data = json.loads(message['data'])
            if canal == CH_VOTES: e.votos_actuales[data['experto_id']] = data['voto']
            elif canal == CH_RESULTS: e.matriz_reputacion = e.cargar_pesos()
            elif canal == CH_BRAIN_PULSE: e.decidir(data['regime_id'], data['Close_Price'], data['Timestamp'])

if __name__ == "__main__": main()