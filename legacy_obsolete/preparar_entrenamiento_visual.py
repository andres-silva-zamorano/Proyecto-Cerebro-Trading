import polars as pl
import numpy as np
import os

def preparar_datos():
    file_path = 'data/Dataset_Con_Regimenes.csv'
    print(f"📖 Cargando datos con Polars...")
    
    # 1. Cargar solo las columnas necesarias para ahorrar memoria
    columnas_ema = ['EMA_10', 'EMA_20', 'EMA_40', 'EMA_80', 'EMA_160', 'EMA_320']
    columnas_necesarias = ['Close_Price'] + columnas_ema
    
    df = pl.read_csv(file_path).select(columnas_necesarias)
    
    ventana = 30
    horizonte = 15
    umbral_cambio = 0.001 # 0.1%

    print(f"🔄 Calculando etiquetas y normalización...")

    # 2. Mirar al futuro para la etiqueta (Y) usando 'shift'
    df = df.with_columns([
        ((pl.col("Close_Price").shift(-horizonte) - pl.col("Close_Price")) / pl.col("Close_Price")).alias("fut_pct_change")
    ])

    # 3. Crear etiquetas: 1 (BUY), 2 (SELL), 0 (NEUTRAL)
    df = df.with_columns([
        pl.when(pl.col("fut_pct_change") > umbral_cambio).then(1)
        .when(pl.col("fut_pct_change") < -umbral_cambio).then(2)
        .otherwise(0)
        .alias("label")
    ])

    # 4. Convertir a NumPy para el procesado de ventanas (donde Polars es limitado para IA)
    # Eliminamos las últimas filas que no tienen futuro (por el horizonte)
    datos_ema_np = df.select(columnas_ema).to_numpy()
    labels_np = df.select("label").to_numpy().flatten()
    
    total_muestras = len(df) - ventana - horizonte
    X = []
    Y = []

    print(f"⚡ Generando {total_muestras} ventanas temporales...")

    # Usamos una vista de NumPy para acelerar el slicing
    for i in range(ventana, len(df) - horizonte):
        # Extraer ventana
        foto = datos_ema_np[i-ventana:i]
        
        # Normalización local (Forma del abanico)
        punto_ref = foto[0, 0]
        if punto_ref == 0: continue # Evitar división por cero
        
        foto_norm = (foto - punto_ref) / punto_ref
        
        X.append(foto_norm)
        Y.append(labels_np[i])

        if i % 100000 == 0:
            print(f"✅ Ventanas creadas: {i}...")

    X = np.array(X, dtype=np.float32)
    Y = np.array(Y, dtype=np.int8)

    # 5. Guardar dataset comprimido
    output_path = 'data/data_visual_train.npz'
    print(f"💾 Guardando en {output_path}...")
    if not os.path.exists('data'): os.makedirs('data')
    np.savez_compressed(output_path, x=X, y=Y)
    
    print(f"✨ ¡Listo! Dataset final: {X.shape} (Ventanas, Tiempo, EMAs)")

if __name__ == "__main__":
    preparar_datos()