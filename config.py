import os

# --- CONEXIÓN A LA MÉDULA ESPINAL (INFRAESTRUCTURA) ---
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# --- CANALES DE FLUJO SENSORIAL (PERCEPCIÓN FRACTAL) ---
CH_MARKET_DATA = 'market_data_stream'      # Datos en tiempo real M1
CH_HTF_CONTEXT = 'htf_context_stream'      # Datos estructurales M15
CH_VESTIBULAR = 'vestibular_perception'    # Monitoreo de ruido (ATR)

# --- CANALES DE PROCESAMIENTO CEREBRAL ---
CH_BRAIN_PULSE = 'brain_raw_pulse'         # Gatillo del Tálamo (id_m1 + id_htf)
CH_BRAIN_STATE = 'brain_consensus_state'    # Estado del Consenso para el Monitor
CH_VOTES = 'expert_votes_stream'           # Votos de los 4 expertos activos

# --- CANALES DE DECISIÓN Y CONTROL OPERATIVO ---
CH_DECISION = 'brain_decision'             # Intenciones de Disparo (BUY/SELL/CLOSE)
CH_RESULTS = 'reporte_operativa'           # Confirmación real desde Gateway MT5
CH_BLOCK = 'brain_block_signal'            # Señal de refractariedad (bloqueo temporal)
CH_HOMEOSTASIS = 'homeostasis_status'      # Estado financiero para el Monitor

# --- PARÁMETROS DE RIESGO Y REPUTACIÓN ---
SL_MAXIMO_DIARIO = -10000.00               # Límite de pérdida catastrófica
PATH_MATRIZ_REPUTACION = "modelos/matriz_reputacion.json"

# --- LÓGICA DE RÁFAGAS (BURST MODE) v3.9.1 ---
# Estos parámetros controlan la piramidación bajo confluencia fractal
MAX_ORDENES_CUMULO = 10                    # Límite estricto de 10 órdenes por ráfaga
INTERVALO_RAFAGA_SEG = 20                  # Tiempo entre disparos de ráfaga (20s)
UMBRAL_CONSENSO_BURST = 0.50               # Consenso mínimo para seguir añadiendo al cúmulo