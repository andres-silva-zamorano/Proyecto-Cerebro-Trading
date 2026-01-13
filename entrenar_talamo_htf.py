import polars as pl
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os

# Rutas
DATA_PATH = 'data/Dataset_Con_Regimenes.csv'
MODEL_DIR = 'modelos'
H5_PATH_HTF = os.path.join(MODEL_DIR, 'talamo_regimenes_HTF.h5')
SCALER_PATH_HTF = os.path.join(MODEL_DIR, 'talamo_scaler_HTF.pkl')

def entrenar_htf():
    print("📖 Consolidando datos de 1M a 15M para entrenamiento HTF...")
    if not os.path.exists(DATA_PATH):
        print("❌ Error: No existe el dataset base."); return

    # 1. Cargar datos con Polars
    df = pl.read_csv(DATA_PATH)
    
    # --- SOLUCIÓN AL ERROR: Derivar regime_id si no existe ---
    if "regime_id" not in df.columns:
        print("🔄 Derivando regime_id de las columnas de probabilidad...")
        prob_cols = [f"prob_regimen_{i}" for i in range(7)]
        # Convertimos a numpy para buscar el índice de la mayor probabilidad
        probs_np = df.select(prob_cols).to_numpy()
        regime_ids = np.argmax(probs_np, axis=1)
        df = df.with_columns(pl.Series("regime_id", regime_ids))

    # 2. Agrupar por 15 minutos
    df = df.with_columns(pl.col("Timestamp").str.to_datetime())
    # Agrupamos: Tomamos el último estado de cada bloque de 15m
    df_htf = df.group_by_dynamic("Timestamp", every="15m").agg(pl.all().last())
    
    features_cols = [
        'ATR_Act', 'ATR_Rel', 'EMA_Princ', 'ADX_Val', 'RSI_Val', 'MACD_Val', 
        'DI_Plus', 'DI_Minus', 'EMA_10', 'EMA_20', 'EMA_40', 'EMA_80', 
        'EMA_160', 'EMA_320', 'EMA_Princ_Slope', 'ADX_Diff', 'RSI_Velocidad', 
        'Volumen_Relativo', 'Close_Price'
    ]

    # Limpieza de nulos tras la agrupación
    df_htf = df_htf.drop_nulls(subset=features_cols + ["regime_id"])
    X = df_htf.select(features_cols).to_numpy()
    y = df_htf.select("regime_id").to_numpy().flatten()

    print(f"🧩 Dataset HTF consolidado: {len(df_htf)} velas de 15 min.")

    # 3. Preprocesamiento
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.1, random_state=42)

    # 4. Arquitectura H5 HTF
    model = models.Sequential([
        layers.Input(shape=(len(features_cols),)),
        layers.Dense(128, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.2),
        layers.Dense(64, activation='relu'),
        layers.Dense(7, activation='softmax')
    ])

    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    early_stop = callbacks.EarlyStopping(monitor='val_loss', patience=7, restore_best_weights=True)

    print("🏋️ Entrenando Tálamo Fractal (M15)...")
    model.fit(X_train, y_train, epochs=100, batch_size=128, validation_split=0.15, callbacks=[early_stop], verbose=1)

    # 5. Guardar Conocimiento
    if not os.path.exists(MODEL_DIR): os.makedirs(MODEL_DIR)
    model.save(H5_PATH_HTF)
    joblib.dump(scaler, SCALER_PATH_HTF)
    print(f"✨ Modelo HTF guardado exitosamente en {H5_PATH_HTF}")

if __name__ == "__main__":
    entrenar_htf()