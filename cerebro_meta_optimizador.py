import polars as pl
import numpy as np
import tensorflow as tf
import optuna
import os
import sys

# Configuración de rutas
sys.path.append(os.getcwd())
DATA_PATH = 'data/Dataset_Con_Regimenes.csv'
MODEL_PATH = 'modelos/cerebro_hft_alpha.h5'

# 1. CARGA ULTRA-RÁPIDA
print("📖 Cargando datos con Polars...")
df = pl.read_csv(DATA_PATH)

VENTANA = 45
COLUMNAS_IA = ['EMA_10', 'EMA_20', 'EMA_40', 'EMA_80', 'EMA_160', 'EMA_320', 
               'DI_Plus', 'DI_Minus', 'ADX_Val', 'RSI_Val', 'MACD_Val', 'ATR_Rel']

# 2. PRE-CALCULO TURBO (Uso masivo de 32 núcleos)
def precalcular_senales_turbo():
    print("🧠 Iniciando Pre-cálculo TURBO...")
    
    # Extraer datos a NumPy
    data_ia = df.select(COLUMNAS_IA).to_numpy()
    precios = df.select("Close_Price").to_numpy().flatten()
    fechas = df.select("Timestamp").to_numpy().flatten()
    adx = df.select("ADX_Val").to_numpy().flatten()
    rsi = df.select("RSI_Val").to_numpy().flatten()
    
    print("🧩 Preparando matriz de ventanas (esto usa RAM)...")
    # Creamos todas las ventanas de golpe usando 'sliding_window_view' de NumPy
    from numpy.lib.stride_tricks import sliding_window_view
    windows = sliding_window_view(data_ia, (VENTANA, len(COLUMNAS_IA))).reshape(-1, VENTANA, len(COLUMNAS_IA))
    
    print(f"⚡ Ejecutando IA sobre {len(windows)} velas en paralelo...")
    # Normalización masiva (vectorizada)
    # Z-Score: (x - mean) / std
    means = windows.mean(axis=1, keepdims=True)
    stds = windows.std(axis=1, keepdims=True) + 1e-8
    windows_norm = (windows - means) / stds
    
    # CARGAR MODELO
    model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    
    # PREDICCIÓN EN BATCH (Aquí es donde los 32 núcleos brillan)
    # batch_size alto para aprovechar la RAM y los hilos
    preds = model.predict(windows_norm, batch_size=4096, verbose=1)
    idx_clases = np.argmax(preds, axis=1)
    
    # Mapear a votos (-1, 0, 1)
    ia_votes = np.zeros(len(idx_clases))
    ia_votes[idx_clases == 1] = 1   # BUY
    ia_votes[idx_clases == 2] = -1  # SELL

    return {
        "precios": precios[VENTANA:],
        "ia_votes": ia_votes,
        "adx": adx[VENTANA:],
        "rsi": rsi[VENTANA:],
        "fechas": fechas[VENTANA:]
    }

CACHE = precalcular_senales_turbo()

# 3. MOTOR DE OPTIMIZACIÓN (Backtest en memoria)
def objective(trial):
    u_disparo = trial.suggest_float('umbral_disparo', 0.70, 0.95)
    u_cierre = trial.suggest_float('umbral_cierre', -0.2, 0.4)
    tp_cluster = trial.suggest_float('tp_cluster', 200, 800)
    trail_pct = trial.suggest_float('trailing_pct', 0.65, 0.85)
    max_ord = trial.suggest_int('max_ordenes', 5, 25)

    pnl_total = 0.0
    pnl_diario = 0.0
    ordenes = []
    max_pnl_f = 0.0
    ultima_fecha = None
    pnl_historico = [0.0]
    
    precios = CACHE["precios"]
    ia_votes = CACHE["ia_votes"]
    adx = CACHE["adx"]
    rsi = CACHE["rsi"]
    fechas = CACHE["fechas"]

    # Simulación de la lógica del bot a la velocidad del rayo
    for i in range(1, len(precios)):
        precio = precios[i]
        fecha = fechas[i][:10]
        
        if ultima_fecha and fecha != ultima_fecha:
            if ordenes:
                pnl_eod = sum([(precio - o['p']) if o['t'] == 1 else (o['p'] - precio) for o in ordenes])
                pnl_diario += pnl_eod
            pnl_total += pnl_diario
            pnl_diario = 0.0
            ordenes = []
            max_pnl_f = 0.0
        ultima_fecha = fecha

        # Consenso
        voto_mom = 0
        if adx[i] > 25:
            if precio > precios[i-1] and rsi[i] > 50: voto_mom = 1
            elif precio < precios[i-1] and rsi[i] < 50: voto_mom = -1
        consenso = ia_votes[i] + voto_mom

        # Lógica Homeostasis
        if ordenes:
            pnl_f = sum([(precio - o['p']) if o['t'] == 1 else (o['p'] - precio) for o in ordenes])
            if pnl_f > max_pnl_f: max_pnl_f = pnl_f
            
            cerrar = False
            if (ordenes[0]['t'] == 1 and consenso < u_cierre) or (ordenes[0]['t'] == -1 and consenso > -u_cierre):
                cerrar = True
            elif pnl_f >= tp_cluster: cerrar = True
            elif max_pnl_f > 150 and pnl_f < (max_pnl_f * trail_pct): cerrar = True
            
            if cerrar:
                pnl_diario += pnl_f
                pnl_historico.append(pnl_total + pnl_diario)
                ordenes = []
                max_pnl_f = 0.0

        # Lógica Ejecutor
        if len(ordenes) < max_ord and abs(consenso) >= u_disparo:
            accion = 1 if consenso > 0 else -1
            if not ordenes or ordenes[0]['t'] == accion:
                ordenes.append({'p': precio, 't': accion})

    series = np.array(pnl_historico)
    cummax = np.maximum.accumulate(series)
    dd = np.max(cummax - series)
    return (pnl_total + pnl_diario) / (dd + 1e-9)

if __name__ == "__main__":
    study = optuna.create_study(direction='maximize')
    print("🚀 Iniciando optimización masiva paralela...")
    # n_jobs=-1 usa todos los procesadores para los trials
    study.optimize(objective, n_trials=200, n_jobs=-1) 
    
    print("\n🏆 CONFIGURACIÓN MAESTRA ENCONTRADA:")
    print(study.best_params)
    print(f"📈 Eficiencia lograda: {study.best_value:.4f}")