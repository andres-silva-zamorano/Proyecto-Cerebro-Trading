import optuna
import polars as pl
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks

# 1. Cargamos el dataset una sola vez en memoria para velocidad máxima
RAW_DF = pl.read_csv('data/Dataset_Con_Regimenes.csv')

def objective(trial):
    # --- HIPER-PARÁMETROS DE MERCADO ---
    # ¿Cuánta historia debe mirar la IA para ser efectiva?
    ventana = trial.suggest_int('ventana', 15, 90)
    # ¿En cuántos minutos debemos ver el resultado para scalping HFT?
    horizonte = trial.suggest_int('horizonte', 3, 20)
    # ¿Qué tan explosivo debe ser el movimiento para considerarlo 'Ganador'?
    mult_atr = trial.suggest_float('mult_atr', 0.8, 2.5)
    
    # --- SELECCIÓN DE CARACTERÍSTICAS ---
    # Optuna decidirá si incluir o no ciertos indicadores para maximizar el accuracy
    columnas = ['EMA_10', 'EMA_20', 'EMA_40', 'EMA_80', 'EMA_160', 'EMA_320', 
                'DI_Plus', 'DI_Minus', 'ADX_Val', 'RSI_Val', 'MACD_Val', 'ATR_Rel']
    
    # --- PREPARACIÓN DINÁMICA DE DATOS ---
    df = RAW_DF.with_columns([
        ((pl.col("Close_Price").shift(-horizonte) - pl.col("Close_Price")) / pl.col("Close_Price")).alias("target"),
        (pl.col("ATR_Rel") * mult_atr).alias("threshold")
    ])
    
    df = df.with_columns([
        pl.when(pl.col("target") > pl.col("threshold")).then(1)
        .when(pl.col("target") < -pl.col("threshold")).then(2)
        .otherwise(0).alias("label")
    ])

    # Slicing rápido con NumPy
    input_data = df.select(columnas).to_numpy()
    labels = df.select("label").to_numpy().flatten()
    
    X, Y = [], []
    # Tomamos una muestra representativa de 150k filas para cada trial
    indices = np.random.randint(ventana, len(df) - horizonte, 150000)
    for i in indices:
        foto = input_data[i-ventana:i].copy()
        # Normalización Z-Score (mejor para indicadores mixtos)
        foto = (foto - np.mean(foto, axis=0)) / (np.std(foto, axis=0) + 1e-8)
        X.append(foto)
        Y.append(labels[i])
    
    X, Y = np.array(X), np.array(Y)

    # --- ARQUITECTURA DE IA ---
    model = models.Sequential([
        layers.Conv1D(trial.suggest_categorical('filters', [32, 64]), 3, activation='relu', input_shape=(ventana, len(columnas))),
        layers.LSTM(trial.suggest_int('lstm_units', 32, 128)),
        layers.Dense(3, activation='softmax')
    ])
    
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=trial.suggest_float('lr', 1e-4, 1e-2, log=True)),
                  loss='sparse_categorical_crossentropy', metrics=['accuracy'])

    # Entrenamiento ultra-corto para evaluar la combinación
    history = model.fit(X, Y, epochs=3, batch_size=1024, validation_split=0.1, verbose=0)
    
    accuracy = history.history['val_accuracy'][-1]
    return accuracy

if __name__ == "__main__":
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=1000) # Sube esto a 500 para mayor precisión
    
    print("🏆 RESULTADOS PARA EL SISTEMA HFT PERFECTO:")
    print(study.best_params)