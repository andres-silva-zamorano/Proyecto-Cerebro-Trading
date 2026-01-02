import polars as pl
import numpy as np
import os

def preparar_datos_v2():
    file_path = 'data/Dataset_Con_Regimenes.csv'
    df = pl.read_csv(file_path)
    
    # 8 Sensores: Estructura + Fuerza + Volatilidad
    columnas_input = ['EMA_10', 'EMA_20', 'EMA_40', 'EMA_80', 'EMA_160', 'EMA_320', 'RSI_Val', 'ATR_Rel']
    
    ventana = 60  # 1 hora de memoria
    horizonte = 15 
    
    # Etiquetado Dinámico: Solo es BUY/SELL si el movimiento supera el ruido (ATR)
    # Esto limpia el 30% de las señales falsas que ensucian el aprendizaje
    df = df.with_columns([
        ((pl.col("Close_Price").shift(-horizonte) - pl.col("Close_Price")) / pl.col("Close_Price")).alias("fut_pct_change"),
        (pl.col("ATR_Rel") * 1.5).alias("umbral_dinamico") 
    ])

    df = df.with_columns([
        pl.when(pl.col("fut_pct_change") > pl.col("umbral_dinamico")).then(1)
        .when(pl.col("fut_pct_change") < -pl.col("umbral_dinamico")).then(2)
        .otherwise(0)
        .alias("label")
    ])

    datos_input_np = df.select(columnas_input).to_numpy()
    labels_np = df.select("label").to_numpy().flatten()
    
    X, Y = [], []
    for i in range(ventana, len(df) - horizonte):
        foto = datos_input_np[i-ventana:i].copy()
        # Normalizamos solo las EMAs (columnas 0-5), RSI y ATR ya vienen normalizados
        punto_ref = foto[0, 0]
        foto[:, :6] = (foto[:, :6] - punto_ref) / punto_ref
        
        X.append(foto)
        Y.append(labels_np[i])

    X = np.array(X, dtype=np.float32)
    Y = np.array(Y, dtype=np.int8)
    np.savez_compressed('data/data_visual_v2.npz', x=X, y=Y)
    print(f"✨ Dataset V2 generado: {X.shape}")

if __name__ == "__main__":
    preparar_datos_v2()