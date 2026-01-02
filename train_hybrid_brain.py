import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models

def entrenar_hibrido():
    with np.load('data/data_visual_v2.npz') as data:
        X, Y = data['x'], data['y']

    model = models.Sequential([
        # PARTE 1: CNN (Extracción de características visuales)
        layers.Conv1D(64, kernel_size=3, activation='relu', input_shape=(60, 8)),
        layers.BatchNormalization(),
        layers.MaxPooling1D(2),
        
        # PARTE 2: LSTM (Análisis de la secuencia temporal)
        layers.LSTM(64, return_sequences=False),
        layers.Dropout(0.3),
        
        # PARTE 3: Decisión
        layers.Dense(32, activation='relu'),
        layers.Dense(3, activation='softmax')
    ])

    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    
    # Entrenamos con un callback para no pasarnos de rosca (EarlyStopping)
    callback = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3)
    
    model.fit(X, Y, epochs=15, batch_size=512, validation_split=0.2, callbacks=[callback])
    model.save('modelos/neurona_visual_v2.h5')

if __name__ == "__main__":
    entrenar_hibrido()