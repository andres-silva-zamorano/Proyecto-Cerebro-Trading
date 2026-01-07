import os

REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# Canales de Flujo
CH_MARKET_DATA = 'market_data_stream'
CH_VESTIBULAR = 'vestibular_perception'
CH_BRAIN_PULSE = 'brain_raw_pulse'
CH_BRAIN_STATE = 'brain_consensus_state'
CH_VOTES = 'expert_votes_stream'
CH_DECISION = 'brain_decision'

# Canales de Control
CH_RESULTS = 'reporte_operativa'
CH_BLOCK = 'brain_block_signal'
CH_HOMEOSTASIS = 'homeostasis_status'

# Riesgo y Rutas
SL_MAXIMO_DIARIO = -10000.00
PATH_MATRIZ_REPUTACION = "modelos/matriz_reputacion.json"