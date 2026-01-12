import redis
import json
import os
import sys
from rich.console import Console

# Asegurar importación de configuración global desde la raíz del proyecto
sys.path.append(os.getcwd())
from config import *

console = Console()

class EjecutorMaestro:
    def __init__(self):
        """
        Calcula el Consenso Colectivo para Entradas y Salidas.
        Integra a los 4 votantes: IA Visual, Momentum, Talamo y Vestibular.
        Fórmula: C = (Σ(V_i * Rep_i * Conf_i)) * Potencial_Vestibular
        """
        try:
            # Conexión a la Médula Espinal (Redis)
            self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
            self.pubsub = self.r.pubsub()
            
            # Suscripción integral al sistema nervioso central
            # CH_VOTES: Votos de los expertos (IA, Momentum, Talamo)
            # CH_RESULTS: Confirmaciones físicas del broker para sincronizar estado
            # CH_BRAIN_PULSE: El latido del Tálamo que gatilla la evaluación
            # CH_VESTIBULAR: Filtro de ruido que inhibe el potencial de acción
            self.pubsub.subscribe(CH_VOTES, CH_RESULTS, CH_BRAIN_PULSE, CH_VESTIBULAR)
            
            # --- MEMORIA SINÁPTICA EN TIEMPO REAL ---
            self.votos_activos = {}       # {experto_id: dirección_voto}
            self.confidencias_locales = {} # {experto_id: nivel_confianza}
            self.potencial_vestibular = 1.0 # 1.0 (Estable) o 0.1 (Inhibición por ruido)
            
            # Estado de sincronización de la posición con Pepperstone
            self.posicion_actual = None # "BUY", "SELL" o None
            
            # Carga de la matriz de pesos aprendida por el Hipocampo
            self.matriz_reputacion = self.cargar_matriz()
            
            console.print("--- 🧠 Ejecutor Maestro v3.8.2: Consenso Dual (4 Votantes) ACTIVO ---")
        except Exception as e:
            console.print(f"[bold red]❌ Error fatal al inicializar el Ejecutor:[/bold red] {e}")
            sys.exit(1)

    def cargar_matriz(self):
        """Carga los pesos de reputación histórica por cada uno de los 7 regímenes."""
        if os.path.exists(PATH_MATRIZ_REPUTACION):
            try:
                with open(PATH_MATRIZ_REPUTACION, 'r') as f:
                    return json.load(f)
            except: pass
        # Si no hay matriz, inicializamos pesos neutros para los regímenes 0 a 6
        return {str(i): {} for i in range(7)}

    def evaluar_consenso(self, regime_id, price, timestamp):
        """
        Calcula la fuerza democrática del comité y decide si se dispara o se liquida.
        """
        reg = str(regime_id)
        suma_sinaptica = 0.0
        conteo_expertos = 0

        # 1. CÁLCULO DE SUMA PONDERADA (Factor de Confianza Colectivo)
        for exp_id, voto in self.votos_activos.items():
            # El guardián vestibular no vota dirección, solo inhibe mediante el potencial_vestibular
            if exp_id == "guardian_vestibular_v1": continue 
            
            # Recuperamos el peso (reputación) asignado a este experto en el régimen actual
            peso_rep = self.matriz_reputacion.get(reg, {}).get(exp_id, 1.0)
            
            # Recuperamos la confianza específica enviada por el lóbulo experto (0.0 a 1.0)
            conf_local = self.confidencias_locales.get(exp_id, 1.0)
            
            # Aporte individual: Voto * Reputación * Confianza
            suma_sinaptica += (voto * peso_rep * conf_local)
            conteo_expertos += 1

        # 2. APLICACIÓN DE LA INHIBICIÓN VESTIBULAR
        # Si hay ruido excesivo, el consenso se atenúa drásticamente (multiplicado por 0.1)
        consenso_final = (suma_sinaptica * self.potencial_vestibular)

        # 3. PUBLICAR ESTADO AL MONITOR ALPHA
        self.r.publish(CH_BRAIN_STATE, json.dumps({
            "Timestamp": timestamp,
            "regime_id": regime_id,
            "Close_Price": price,
            "consenso_actual": round(consenso_final, 2),
            "posicion_vuelo": self.posicion_actual,
            "expertos_en_comite": list(self.votos_activos.keys())
        }))

        # 4. LÓGICA DE ENTRADA (Umbral de Disparo: 0.75)
        if self.posicion_actual is None:
            # Verificamos si no hay un bloqueo temporal de Homeostasis y si hay convicción
            if not self.r.exists(f"{CH_BLOCK}_active") and abs(consenso_final) >= 0.75:
                accion = "BUY" if consenso_final > 0 else "SELL"
                
                payload_decision = {
                    "action": accion,
                    "price_at_entry": price,
                    "regime": regime_id,
                    "consenso": round(consenso_final, 2),
                    "Timestamp": timestamp
                }
                
                # Emitimos la intención de disparo al Gateway
                self.r.publish(CH_DECISION, json.dumps(payload_decision))
                console.print(f"[bold cyan]🚀 INTENCIÓN DE DISPARO:[/bold cyan] {accion} | Consenso: {consenso_final:.2f} | R{regime_id}")

        # 5. LÓGICA DE SALIDA (Umbral de Duda Neuronal: 0.28)
        # Si la convicción colectiva se disuelve, el bot liquida para proteger capital
        elif self.posicion_actual is not None:
            umbral_duda = 0.2837
            cerrar = False
            razon = ""

            if self.posicion_actual == "BUY":
                if consenso_final < umbral_duda:
                    cerrar, razon = True, "PERDIDA_CONVICCION_COMPRA"
            elif self.posicion_actual == "SELL":
                if consenso_final > -umbral_duda:
                    cerrar, razon = True, "PERDIDA_CONVICCION_VENTA"

            if cerrar:
                # Orden de liquidación física dirigida al MT5 Gateway
                self.r.publish(CH_DECISION, json.dumps({
                    "action": "CLOSE_ALL", 
                    "reason": razon
                }))
                console.print(f"[bold yellow]🛑 INTENCIÓN DE LIQUIDACIÓN:[/bold yellow] {razon} ({consenso_final:.2f})")

    def escuchar(self):
        """Bucle infinito de procesamiento de señales del sistema nervioso."""
        for message in self.pubsub.listen():
            if message['type'] != 'message':
                continue
                
            canal = message['channel'].decode('utf-8')
            data = json.loads(message['data'])

            # A. REGISTRO DINÁMICO DE VOTOS
            if canal == CH_VOTES:
                exp_id = data['experto_id']
                self.votos_activos[exp_id] = data['voto']
                self.confidencias_locales[exp_id] = data.get('confianza', 1.0)
            
            # B. AJUSTE DE POTENCIAL VESTIBULAR (Filtro de Ruido)
            elif canal == CH_VESTIBULAR:
                self.potencial_vestibular = data.get('action_potential', 1.0)
            
            # C. SINCRONIZACIÓN DE POSICIÓN REAL (Feedback del Broker)
            elif canal == CH_RESULTS:
                status = data.get('status')
                if status == 'executed':
                    self.posicion_actual = data['action']
                elif status == 'closed':
                    self.posicion_actual = None
                    # Forzamos recarga de matriz por si el Hipocampo actualizó pesos
                    self.matriz_reputacion = self.cargar_matriz()
            
            # D. PROCESAMIENTO POR PULSO (Invocado por el Tálamo cada vela/tick)
            elif canal == CH_BRAIN_PULSE:
                self.evaluar_consenso(data['regime_id'], data['Close_Price'], data['Timestamp'])

if __name__ == "__main__":
    try:
        EjecutorMaestro().escuchar()
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Deteniendo el Lóbulo de Ejecución...[/bold red]")