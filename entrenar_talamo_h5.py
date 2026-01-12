import polars as pl
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os

# Configuración de rutas
DATA_PATH = 'data/Dataset_Con_Regimenes.csv'
MODEL_DIR = 'modelos'
H5_PATH = os.path.join(MODEL_DIR, 'talamo_regimenes.h5')
SCALER_PATH = os.path.join(MODEL_DIR, 'talamo_scaler.pkl')

def entrenar():
    print("📖 Iniciando lectura de Dataset_Con_Regimenes.csv...")
    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: No se encuentra el archivo en {DATA_PATH}")
        return

    # 1. Definir columnas de entrada (19 features)
    features_cols = [
        'ATR_Act', 'ATR_Rel', 'EMA_Princ', 'ADX_Val', 'RSI_Val', 'MACD_Val', 
        'DI_Plus', 'DI_Minus', 'EMA_10', 'EMA_20', 'EMA_40', 'EMA_80', 
        'EMA_160', 'EMA_320', 'EMA_Princ_Slope', 'ADX_Diff', 'RSI_Velocidad', 
        'Volumen_Relativo', 'Close_Price'
    ]
    
    # 2. Cargar datos con Polars
    df = pl.read_csv(DATA_PATH)
    
    # Aseguramos que existan las etiquetas de régimen
    # Si no tienes regime_id pero tienes las prob_regimen_X, calculamos el argmax
    if "regime_id" not in df.columns:
        print("🔄 Calculando regime_id basado en prob_regimen_0-6...")
        prob_cols = [f"prob_regimen_{i}" for i in range(7)]
        probs_np = df.select(prob_cols).to_numpy()
        regime_ids = np.argmax(probs_np, axis=1)
        df = df.with_columns(pl.Series("regime_id", regime_ids))

    # Limpieza de nulos
    df = df.drop_nulls(subset=features_cols + ["regime_id"])
    
    X = df.select(features_cols).to_numpy()
    y = df.select("regime_id").to_numpy().flatten()

    # 3. Preprocesamiento (Escalado Z-Score)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Dividir en entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.1, random_state=42)

    # 4. Arquitectura de la Neurona de Regímenes (H5)
    # Una red densa con salida Softmax para 7 clases
    model = models.Sequential([
        layers.Input(shape=(len(features_cols),)),
        layers.Dense(64, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.2),
        layers.Dense(32, activation='relu'),
        layers.Dense(16, activation='relu'),
        layers.Dense(7, activation='softmax') # 7 Regímenes (0 a 6)
    ])

    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    print(f"🏋️ Entrenando neurona sobre {len(X_train)} velas...")
    model.fit(X_train, y_train, epochs=20, batch_size=256, validation_split=0.1, verbose=1)

    # Evaluación rápida
    loss, acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"✅ Entrenamiento completado. Precisión en Test: {acc:.2%}")

    # 5. Guardar el conocimiento
    if not os.path.exists(MODEL_DIR): os.makedirs(MODEL_DIR)
    model.save(H5_PATH)
    joblib.dump(scaler, SCALER_PATH)
    
    # Guardar lista de features para el lóbulo de producción
    joblib.dump(features_cols, os.path.join(MODEL_DIR, 'talamo_features.pkl'))

    print(f"💾 Modelo guardado en: {H5_PATH}")
    print(f"💾 Escalador guardado en: {SCALER_PATH}")

if __name__ == "__main__":
    entrenar()