# Configuración central del cerebro
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# Canales de comunicación (Médula Espinal)
# 1. El latido del mercado (Sensor -> Todos)
CH_MARKET_DATA = 'market_data_stream'

# 2. El estado de consciencia (Tálamo -> Todos)
CH_BRAIN_STATE = 'brain_state'

# 3. Canales sensoriales específicos (Neuronas -> Ejecutor/Monitor)
CH_VISUAL = 'visual_perception'
CH_MOMENTUM = 'momentum_perception'
CH_VESTIBULAR = 'vestibular_perception'

# 4. Canales de acción y riesgo
CH_DECISION = 'brain_decision'
CH_HOMEOSTASIS = 'homeostasis_status'
CH_BLOCK = "brain_block_signal"

# --- PARÁMETROS DE RIESGO ---
# Límite de pérdida acumulada diaria antes de apagar el cerebro
SL_MAXIMO_DIARIO = -2000.00