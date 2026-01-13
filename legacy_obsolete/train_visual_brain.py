import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
import matplotlib.pyplot as plt

def entrenar_neurona_visual():
    print("🧠 Cargando memoria de entrenamiento...")
    with np.load('data/data_visual_train.npz') as data:
        X = data['x']
        Y = data['y']

    # 1. Arquitectura de la Neurona (CNN 1D para Series Temporales)
    model = models.Sequential([
        # Primera capa: Detecta micro-patrones en las EMAs
        layers.Conv1D(64, kernel_size=3, activation='relu', input_shape=(30, 6)),
        layers.MaxPooling1D(2),
        layers.Dropout(0.2), # Evita que la IA memorice, la obliga a aprender
        
        # Segunda capa: Detecta patrones más complejos (estructuras)
        layers.Conv1D(128, kernel_size=3, activation='relu'),
        layers.GlobalAveragePooling1D(),
        
        # Capas de decisión profunda
        layers.Dense(64, activation='relu'),
        layers.Dense(3, activation='softmax') # 3 Salidas: 0=Neutral, 1=BUY, 2=SELL
    ])

    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    print("🚀 Iniciando proceso de aprendizaje (Entrenamiento)...")
    # Entrenamos con el 80% y validamos con el 20% para ver si de verdad aprende
    history = model.fit(
        X, Y, 
        epochs=10, 
        batch_size=256, 
        validation_split=0.2,
        verbose=1
    )

    # 2. Guardar el "Conocimiento" (Cerebro entrenado)
    model.save('modelos/neurona_visual.h5')
    print("💾 ¡Neurona Visual guardada en 'modelos/neurona_visual.h5'!")

    # 3. Visualizar el aprendizaje
    plt.plot(history.history['accuracy'], label='Acierto Entrenamiento')
    plt.plot(history.history['val_accuracy'], label='Acierto Validación')
    plt.title('Curva de Aprendizaje de la Neurona Visual')
    plt.legend()
    plt.show()

if __name__ == "__main__":
    import os
    if not os.path.exists('modelos'): os.makedirs('modelos')
    entrenar_neurona_visual()