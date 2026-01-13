import polars as pl
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
import os

# CONFIGURACIÓN MAESTRA (Extraída del Trial 15)
BEST_PARAMS = {
    'ventana': 45,
    'horizonte': 3,
    'mult_atr': 2.2740,
    'filters': 64,
    'lstm_units': 128,
    'lr': 0.00019158
}

def crear_modelo_final():
    print("🚀 Iniciando Construcción del Cerebro Alpha (90% Acc)...")
    
    # 1. Preparación total de datos
    df = pl.read_csv('data/Dataset_Con_Regimenes.csv')
    columnas_input = ['EMA_10', 'EMA_20', 'EMA_40', 'EMA_80', 'EMA_160', 'EMA_320', 
                      'DI_Plus', 'DI_Minus', 'ADX_Val', 'RSI_Val', 'MACD_Val', 'ATR_Rel']
    
    # Etiquetado con los parámetros optimizados
    df = df.with_columns([
        ((pl.col("Close_Price").shift(-BEST_PARAMS['horizonte']) - pl.col("Close_Price")) / pl.col("Close_Price")).alias("target"),
        (pl.col("ATR_Rel") * BEST_PARAMS['mult_atr']).alias("threshold")
    ])
    
    df = df.with_columns([
        pl.when(pl.col("target") > pl.col("threshold")).then(1)
        .when(pl.col("target") < -pl.col("threshold")).then(2)
        .otherwise(0).alias("label")
    ])

    input_data = df.select(columnas_input).to_numpy()
    labels = df.select("label").to_numpy().flatten()
    
    X, Y = [], []
    ventana = BEST_PARAMS['ventana']
    
    print("🧠 Extrayendo secuencias temporales...")
    for i in range(ventana, len(df) - BEST_PARAMS['horizonte']):
        foto = input_data[i-ventana:i].copy()
        foto = (foto - np.mean(foto, axis=0)) / (np.std(foto, axis=0) + 1e-8)
        X.append(foto)
        Y.append(labels[i])
    
    X, Y = np.array(X), np.array(Y)

    # 2. Arquitectura Híbrida CNN-LSTM
    model = models.Sequential([
        layers.Conv1D(BEST_PARAMS['filters'], 3, activation='relu', input_shape=(ventana, len(columnas_input))),
        layers.BatchNormalization(),
        layers.LSTM(BEST_PARAMS['lstm_units'], return_sequences=False),
        layers.Dropout(0.2),
        layers.Dense(32, activation='relu'),
        layers.Dense(3, activation='softmax')
    ])
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=BEST_PARAMS['lr']),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    print("🏋️ Entrenando modelo de alto rendimiento (20 épocas)...")
    model.fit(X, Y, epochs=20, batch_size=512, validation_split=0.1)

    if not os.path.exists('modelos'): os.makedirs('modelos')
    model.save('modelos/cerebro_hft_alpha.h5')
    print("✨ CEREBRO ALPHA GUARDADO EXITOSAMENTE en 'modelos/cerebro_hft_alpha.h5'")

if __name__ == "__main__":
    crear_modelo_final()