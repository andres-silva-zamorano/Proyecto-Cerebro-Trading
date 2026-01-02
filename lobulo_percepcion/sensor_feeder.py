import sys
import os
# Añade la carpeta superior al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import redis
import json
import time
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA

def start_historical_feeder(file_path):
    # Conectamos a la "Médula Espinal"
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    
    print(f"🧠 Leyendo Memoria Histórica: {file_path}")
    # Leemos el CSV (asegúrate de que la ruta sea correcta en tu carpeta /data)
    df = pd.read_csv(file_path)
    
    print(f"✅ Cargadas {len(df)} velas de un minuto. Iniciando flujo sensorial...")

    for index, row in df.iterrows():
        # Convertimos la fila a un diccionario
        tick_data = row.to_dict()
        
        # Publicamos el paquete sensorial completo en Redis
        # Todas las neuronas suscritas recibirán este pulso simultáneamente
        r.publish(CH_MARKET_DATA, json.dumps(tick_data))
        
        # Control de velocidad: 
        # 0.01 = 100 velas por segundo (Super-entrenamiento)
        # 1.0  = Velocidad real M1
        time.sleep(0.05) 

if __name__ == "__main__":
    start_historical_feeder('data/Dataset_Con_Regimenes.csv')