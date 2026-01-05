# --- config.py ---
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# Canales existentes
CH_MARKET_DATA = 'market_data_stream'
CH_BRAIN_STATE = 'brain_state'
CH_VISUAL = 'visual_perception'
CH_MOMENTUM = 'momentum_perception'
CH_VESTIBULAR = 'vestibular_perception'
CH_DECISION = 'brain_decision'
CH_HOMEOSTASIS = 'homeostasis_status'

# --- NUEVOS CANALES PARA EXPERTOS ---
CH_VOTES = 'expert_votes_stream'      # Donde todos los expertos lanzan su voto
CH_RESULTS = 'reporte_operativa'      # Donde Homeostasis informa si ganamos/perdimos
CH_BLOCK = 'brain_block_signal'       # Fusible de seguridad

# Parámetros de Riesgo
SL_MAXIMO_DIARIO = -10000.00
PATH_MATRIZ_REPUTACION = "modelos/matriz_reputacion.json"