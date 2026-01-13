import redis
import json
import os
import sys
import time
from rich.console import Console

# Asegurar importación de configuración global desde la raíz del proyecto
sys.path.append(os.getcwd())
from config import *

console = Console()

class EjecutorMaestro:
    def __init__(self):
        """
        Ejecutor v3.9.1: Mando de Ráfagas Fractales.
        Filtro Estructural: Solo permite operar si M1 (Micro) y M15 (Macro) coinciden.
        Burst Mode: Piramidación de hasta 10 órdenes cada 20 segundos.
        """
        try:
            self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
            self.pubsub = self.r.pubsub()
            
            # Suscripción integral a la red de datos del organismo
            # CH_VOTES: Decisiones de los expertos individuales
            # CH_RESULTS: Confirmaciones físicas del broker (Pepperstone)
            # CH_BRAIN_PULSE: Latido del Tálamo con los regímenes M1 y M15
            # CH_VESTIBULAR: Estado del ruido del mercado
            self.pubsub.subscribe(CH_VOTES, CH_RESULTS, CH_BRAIN_PULSE, CH_VESTIBULAR)
            
            # Memoria operativa del lóbulo
            self.votos_activos = {}
            self.confidencias_locales = {}
            self.potencial_vestibular = 1.0
            self.posicion_actual = None 
            self.num_ordenes = 0       # Contador de órdenes en el cúmulo actual
            self.last_burst_time = 0   # Cronómetro para gestionar los intervalos de ráfaga
            
            self.matriz_reputacion = self.cargar_matriz()
            console.print(f"--- 🧠 Ejecutor v3.9.1: Mando Fractal (Límite: {MAX_ORDENES_CUMULO}) ACTIVO ---")
        except Exception as e:
            console.print(f"[bold red]❌ Error fatal al inicializar el Ejecutor:[/bold red] {e}")
            sys.exit(1)

    def cargar_matriz(self):
        """Carga los pesos de reputación por cada régimen para la democracia ponderada."""
        if os.path.exists(PATH_MATRIZ_REPUTACION):
            try:
                with open(PATH_MATRIZ_REPUTACION, 'r') as f:
                    return json.load(f)
            except: pass
        return {str(i): {} for i in range(7)}

    def evaluar_consenso(self, id_m1, id_htf, price, timestamp):
        """
        Calcula el consenso ponderado y decide disparos de ráfaga o liquidaciones.
        """
        reg = str(id_m1)
        suma_sinaptica = 0.0
        
        # 1. SUMA PONDERADA DE EXPERTOS
        for exp_id, voto in self.votos_activos.items():
            if exp_id == "guardian_vestibular_v1": continue
            
            # Peso histórico (Reputación) * Confianza actual del lóbulo
            peso_rep = self.matriz_reputacion.get(reg, {}).get(exp_id, 1.0)
            conf_local = self.confidencias_locales.get(exp_id, 1.0)
            suma_sinaptica += (voto * peso_rep * conf_local)

        # 2. APLICACIÓN DE FILTRO DE RUIDO (Multiplicador Vestibular)
        consenso_final = suma_sinaptica * self.potencial_vestibular
        
        # 3. PUBLICAR ESTADO AL MONITOR ALPHA
        self.r.publish(CH_BRAIN_STATE, json.dumps({
            "Timestamp": timestamp,
            "regime_id": id_m1,
            "regime_htf": id_htf,
            "consenso_actual": round(consenso_final, 2),
            "posicion_vuelo": self.posicion_actual
        }))

        # --- LÓGICA DE ALINEACIÓN FRACTAL (M1 + M15) ---
        m1_alcista = id_m1 in [1, 3, 5]
        htf_alcista = id_htf in [1, 3, 5]
        m1_bajista = id_m1 in [2, 4, 6]
        htf_bajista = id_htf in [2, 4, 6]
        
        # Confluencia: Ambos marcos temporales deben coincidir en dirección
        confluencia_fractal = (m1_alcista and htf_alcista) or (m1_bajista and htf_bajista)
        
        abs_consenso = abs(consenso_final)
        direccion_sugerida = "BUY" if consenso_final > 0 else "SELL"

        # A. DISPARO INICIAL (Apertura de Cúmulo)
        if self.posicion_actual is None:
            if abs_consenso >= 0.75:
                if confluencia_fractal:
                    # Permiso concedido: Los fractales están alineados
                    self.disparar(direccion_sugerida, price, id_m1, consenso_final, timestamp)
                    self.last_burst_time = time.time()
                else:
                    # Bloqueo estructural para proteger el balance de canales laterales
                    console.print(f"[dim yellow]⏳ Filtro Fractal bloqueando entrada: M1(R{id_m1}) vs M15(R{id_htf})[/dim yellow]")

        # B. MODO RÁFAGA (BURST MODE): Piramidación controlada
        elif self.posicion_actual == direccion_sugerida and self.num_ordenes < MAX_ORDENES_CUMULO:
            ahora = time.time()
            if (ahora - self.last_burst_time) >= INTERVALO_RAFAGA_SEG:
                # En modo ráfaga somos más tolerantes si la confluencia persiste
                if confluencia_fractal and abs_consenso >= UMBRAL_CONSENSO_BURST:
                    console.print(f"[bold magenta]🔥 RÁFAGA {self.num_ordenes + 1}/{MAX_ORDENES_CUMULO}:[/bold magenta] Incrementando exposición...")
                    self.disparar(direccion_sugerida, price, id_m1, consenso_final, timestamp)
                    self.last_burst_time = ahora

        # C. LIQUIDACIÓN TOTAL POR DUDA NEURONAL
        elif self.posicion_actual is not None:
            umbral_duda = 0.2837
            cerrar = False
            
            # Cierre si el consenso se disuelve o hay señal de reversión
            if self.posicion_actual == "BUY" and consenso_final < umbral_duda:
                cerrar = True
            elif self.posicion_actual == "SELL" and consenso_final > -umbral_duda:
                cerrar = True
            
            if cerrar:
                self.r.publish(CH_DECISION, json.dumps({
                    "action": "CLOSE_ALL", 
                    "reason": "PERDIDA_CONVICCION_COLECTIVA"
                }))
                console.print(f"[bold yellow]🛑 LIQUIDACIÓN:[/bold yellow] Duda en el consenso fractal ({consenso_final:.2f})")

    def disparar(self, accion, price, regime, consenso, ts):
        """Publica la instrucción de ejecución para el Gateway."""
        if not self.r.exists(f"{CH_BLOCK}_active"):
            self.r.publish(CH_DECISION, json.dumps({
                "action": accion,
                "price_at_entry": price,
                "regime": regime,
                "consenso": round(consenso, 2),
                "Timestamp": ts
            }))

    def escuchar(self):
        """Bucle infinito de escucha de la Médula Espinal."""
        for message in self.pubsub.listen():
            if message['type'] != 'message':
                continue
                
            canal = message['channel'].decode('utf-8')
            data = json.loads(message['data'])

            # Registro de votos de expertos
            if canal == CH_VOTES:
                exp_id = data['experto_id']
                self.votos_activos[exp_id] = data['voto']
                self.confidencias_locales[exp_id] = data.get('confianza', 1.0)
            
            # Ajuste de potencial vestibular (filtro de ruido)
            elif canal == CH_VESTIBULAR:
                self.potencial_vestibular = data.get('action_potential', 1.0)
            
            # Sincronización física con el Broker (CH_RESULTS)
            elif canal == CH_RESULTS:
                status = data.get('status')
                if status == 'executed':
                    self.posicion_actual = data['action']
                    self.num_ordenes += 1
                elif status == 'closed':
                    self.posicion_actual = None
                    self.num_ordenes = 0
                    self.matriz_reputacion = self.cargar_matriz()
            
            # Gatillo de evaluación por pulso talamico fractal (M1 + M15)
            elif canal == CH_BRAIN_PULSE:
                self.evaluar_consenso(
                    data['regime_id'], 
                    data.get('regime_htf', 0), 
                    data['Close_Price'], 
                    data['Timestamp']
                )

if __name__ == "__main__":
    try:
        EjecutorMaestro().escuchar()
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Lóbulo de Ejecución detenido por el usuario.[/bold red]")