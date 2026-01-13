# Especificación Técnica: Lóbulo de Percepción (Corteza Sensorial)

## Índice de Contenidos

### Capítulo 1: El Sistema de Ingesta y Pre-procesamiento

- 1.1. El **Sensor de Ticks y Velas (MT5 Connector)**: Captura de datos brutos.
- 1.2. El **Alimentador de Memoria (CSV Historical Feeder)**: Inyección de datos históricos.
- 1.3. La **Unidad de Normalización Dinámica**: Adaptación de escalas (Min-Max, Z-Score) para RN.
- 1.4. El **Publicador Sensorial**: Estructuración del mensaje JSON en el bus de Redis.

### Capítulo 2: El Tálamo (Identificación de Contexto)

- 2.1. El **Monitor de Probabilidades de Régimen**: Procesamiento de `prob_regimen_0` a `6`.
- 2.2. Neurona de **Consistencia Contextual**: Detección de señales contradictorias entre regímenes.
- 2.3. Neurona de **Confianza de Clasificación**: Cálculo del umbral mínimo para validar el estado del mercado.

### Capítulo 3: Corteza Visual (Análisis de Estructura Fractal)

- 3.1. Neurona de **Alineación de Abanico (Fan-Out)**: Análisis de la jerarquía EMA (10-320).
- 3.2. Neurona de **Pendiente y Ángulo (Slope Analysis)**: Procesamiento de `EMA_Princ_Slope`.
- 3.3. Neurona de **Ruptura de Estructura (CNN 1D)**: Identificación de patrones geométricos en el precio de cierre.

### Capítulo 4: Sistema Somatosensorial (Momentum y Energía)

- 4.1. Neurona de **Aceleración de Osciladores**: Análisis de `RSI_Velocidad` y `ADX_Diff`.
- 4.2. Neurona de **Divergencia Estocástica**: Comparación de máximos/mínimos entre precio y RSI/MACD.
- 4.3. Neurona de **Inercia de Tendencia**: Cálculo de la fuerza bruta del movimiento (`ADX_Val`).

### Capítulo 5: El Sistema Vestibular (Volatilidad y Ruido)

- 5.1. Neurona de **Presión de Volumen**: Análisis del `Volumen_Relativo`.
- 5.2. Neurona de **Expansión de Rango (ATR Relativo)**: Detección de picos de volatilidad (`ATR_Rel`).
- 5.3. El **Autoencoder de Verificación de Realidad**: Validación de la señal frente al ruido blanco.



# Capítulo 1: El Sistema de Ingesta y Pre-procesamiento

Este capítulo define la **Puerta de Entrada Sensorial**. Su objetivo es la **Homogeneidad**: no importa si el dato viene de una simulación histórica o del mercado vivo, para el cerebro debe lucir idéntico.

## 1.1. El Sensor de Ticks y Velas (MT5 Connector)

Este componente es el equivalente a los **fotoreceptores de la retina**. Captura la realidad cruda del broker.

- **Función:** Se conecta a la terminal de MetaTrader 5 y extrae el símbolo, el precio (Bid/Ask), el volumen y los indicadores calculados en la plataforma (EMAs, RSI, ADX).
- **Frecuencia:** Puede trabajar por *tick* (cada cambio de precio) o por *vela cerrada* (cada minuto), dependiendo de la configuración de "Vigilia".
- **Código de Salida:** Un diccionario de Python que mapea exactamente las columnas de tu dataset.

## 1.2. El Alimentador de Memoria (CSV Historical Feeder)

Este es el sistema de **"Alucinación Controlada"**. Permite que el cerebro viva en el pasado para entrenarse.

- **Función:** Lee tu archivo `Dataset_Con_Regimenes.csv`. Para simular el tiempo real, este script no lee todo el archivo a la vez, sino que publica una fila cada "X" milisegundos en Redis.
- **Sincronía:** Incluye un campo `is_backtest: True` para que las neuronas sepan que están en modo entrenamiento y puedan ajustar sus procesos de aprendizaje.

## 1.3. La Unidad de Normalización Dinámica (El Filtro Adaptativo)

Las redes neuronales fallan si los números son muy grandes o varían mucho (ej. el precio está en 1.0800 pero el volumen en 500,000). Esta unidad actúa como la **pupila**, regulando la intensidad de la señal.

- **Técnica Min-Max:** Transforma valores como el RSI (0-100) a un rango de (0-1).
- **Técnica Z-Score:** Para datos como el `ATR_Rel`, calcula cuántas desviaciones estándar se aleja el valor actual del promedio reciente.
- **Importancia:** Esto asegura que la neurona de "Inercia" no le dé más importancia al precio que al volumen solo porque el número del precio es "más grande".

## 1.4. El Publicador Sensorial (La Sinapsis Aferente)

Una vez el dato está limpio y normalizado, se debe "gritar" al resto del cerebro a través de la médula espinal (Redis).

- **Protocolo:** Utiliza el canal `RAW_SENSES`.

- **Estructura del Mensaje:**

  JSON

  ```
  {
      "meta": {"symbol": "EURUSD", "time": "2025.05.20 14:00", "mode": "live"},
      "regime_probs": [0.05, 0.10, 0.05, 0.0, 0.0, 0.80, 0.0],
      "sensors": {
          "norm_ema_slope": 0.72,
          "norm_rsi_vel": 0.45,
          "norm_vol_rel": 0.88,
          "norm_atr": 0.30
      }
  }
  ```

------

### Analogía Neurobiológica del Capítulo 1:

Este capítulo es el **Sistema Nervioso Periférico**. Los nervios de tus dedos no "saben" qué es un objeto caliente, solo envían una señal eléctrica de "intensidad de calor". De la misma manera, el **Sensor** no sabe si hay una tendencia; solo envía la intensidad de la pendiente de la EMA. La normalización es como el proceso donde el cerebro ignora el peso de la ropa que llevas puesta (ruido constante) para enfocarse en estímulos nuevos y relevantes.



# Capítulo 2: El Tálamo (Identificación de Contexto)

El objetivo de este capítulo es la **Jerarquización del Estímulo**. Antes de que el cerebro gaste energía analizando patrones fractales o momentum, el Tálamo debe confirmar en qué tipo de entorno nos encontramos y cuánta validez tiene esa percepción.

## 2.1. El Monitor de Probabilidades de Régimen

Esta micro-neurona (`n_percep_regime_monitor.py`) es la encargada de interpretar las 7 columnas de probabilidad (`prob_regimen_0` a `6`).

- **Función:** No solo toma el valor más alto (ArgMax), sino que analiza la **Distribución de Probabilidad**.
- **Analogía Cerebral:** Es el sistema de atención. El cerebro no solo ve, sino que "enfoca". Esta neurona enfoca la atención del sistema en el régimen dominante, ignorando el ruido de los regímenes con baja probabilidad.

## 2.2. Neurona de Consistencia Contextual

Esta unidad analiza si el régimen detectado es coherente con el tiempo.

- **Función:** Compara el régimen actual con los de las últimas 5 a 10 velas. Si el sistema salta de "Canal Alcista" a "Rango" y luego a "Tendencia Bajista" en 3 minutos, esta neurona detecta una **Disonancia Cognitiva**.
- **Acción:** Si hay inconsistencia, publica en Redis un factor de "Inestabilidad Contextual", lo que alertará al Lóbulo de Ejecución de que el mercado está errático.
- **Analogía:** Es como el sentido del equilibrio. Si lo que ves (ojos) no coincide con lo que sientes (oído interno), te mareas. Esta neurona marea al sistema para que no opere en el caos.

## 2.3. Neurona de Confianza de Clasificación (El Umbral de Conciencia)

Aquí es donde decidimos si una señal es lo suficientemente fuerte como para ser considerada "real".

- **Función:** Calcula la entropía de las probabilidades. Si la `prob_regimen_5` es 0.40 y la `prob_regimen_0` es 0.38, la confianza es mínima.
- **Micro-decisión:** Solo si la probabilidad del régimen dominante supera un **Umbral de Activación** (ej. > 0.65), la neurona emite un impulso de "Conciencia Clara".
- **Analogía:** Es el umbral de percepción. El cerebro ignora sonidos muy bajos (ruido de fondo) y solo se vuelve consciente del sonido cuando este supera un nivel de decibelios específico.

## 2.4. Publicación del "Estado Mental" en Redis

El resultado de este capítulo se guarda en una clave global de Redis llamada `BRAIN_STATE`:

JSON

```
{
    "timestamp": "2025.05.20 14:01",
    "active_regime": 5,
    "confidence_score": 0.88,
    "stability_index": 0.95,
    "is_conscious": true
}
```

## 2.5. Inhibición Talamica (Gating)

Esta es la función más poderosa del Capítulo 2.

- **Lógica:** Si `is_conscious` es `false` o la `confidence_score` es menor a 0.50, el Tálamo envía un **neurotransmisor inhibitorio** a través de Redis.
- **Resultado:** Las neuronas de los Capítulos 3, 4 y 5 entrarán en un estado de "baja potencia" o ahorro de recursos, ya que el cerebro ha decidido que la realidad actual no es confiable.

------

### Analogía Neurobiológica del Capítulo 2:

Sin el Tálamo, el cerebro intentaría reaccionar a cada pequeño movimiento de precio como si fuera una oportunidad de vida o muerte. El Tálamo nos permite estar en un estado de "alerta relajada" durante el **Rango (Regimen 0)** y pasar a un estado de **"Foco Intenso"** solo cuando las probabilidades de **Tendencia (Regimen 5 o 6)** son claras.



# Capítulo 3: Corteza Visual (Análisis de Estructura Fractal)

El objetivo de este capítulo es la **Reconocimiento de Patrones Espaciales**. Aquí, el cerebro deja de ver números aislados y empieza a ver "formas" y "jerarquías" de fuerza.

## 3.1. Neurona de Alineación de Abanico (Fan-Out)

Esta micro-neurona (`n_percep_ema_fan.py`) analiza la relación entre las EMAs de 10 a 320 periodos.

- **Función:** Mide el orden jerárquico. Si la EMA 10 > 20 > 40 > 80 > 160 > 320, el abanico está "expandido" y en orden.
- **Micro-decisión:** Calcula un **Coeficiente de Expansión**. Un abanico abierto indica una tendencia madura; un abanico entrelazado indica una zona de congestión o "indecisión visual".
- **Analogía Cerebral:** Neuronas de la retina que detectan la profundidad. Si las líneas están paralelas y alejándose, el cerebro percibe un camino despejado.

## 3.2. Neurona de Pendiente y Ángulo (Slope Analysis)

Esta unidad procesa la `EMA_Princ_Slope`.

- **Función:** Traduce el valor de la pendiente en un ángulo trigonométrico. No es lo mismo una pendiente de 10° que una de 45°.
- **Micro-decisión:** Clasifica la "agresividad" del movimiento. Si el ángulo es demasiado vertical, la neurona informa de un posible movimiento "parabólico" (insostenible). Si es constante, informa de una tendencia saludable.
- **Analogía:** El sistema de detección de movimiento ocular (sacadas). El cerebro calcula la trayectoria de un objeto basándose en el ángulo de su desplazamiento.

## 3.3. Neurona de Ruptura de Estructura (CNN 1D)

Aquí es donde aplicamos una **Red Neuronal Convolucional (CNN)** sobre el `Close_Price`.

- **Función:** Busca patrones de **Market Structure Shift (MSS)** o **Break of Structure (BOS)**. La CNN escanea las últimas 30 velas buscando la forma característica de un "máximo más alto" seguido de un "mínimo más alto".
- **Micro-decisión:** Emite una probabilidad de "Ruptura Confirmada".
- **Analogía:** El área V4 de la corteza visual, especializada en reconocer formas complejas (como círculos o triángulos). Esta neurona reconoce la "forma" de una ruptura de soporte o resistencia.

## 3.4. Neurona de Continuidad Fractal (Multi-Timeframe)

Esta neurona verifica si lo que ve en M1 tiene sentido con lo que ocurre en temporalidades mayores.

- **Función:** Compara el `EMA_320` (que actúa como un proxy de una temporalidad mayor) con el precio actual.
- **Micro-decisión:** Si el precio está por encima de la EMA 320 pero la micro-estructura de la CNN es bajista, informa de un **Retroceso Técnico** en lugar de un cambio de tendencia real.
- **Analogía:** La integración visual. Tu cerebro sabe que un coche pequeño a lo lejos no es un juguete, sino un objeto grande que está distante. Integra la perspectiva.

## 3.5. Salida Sináptica del Capítulo 3

Los resultados de estas neuronas se empaquetan en Redis bajo la clave `VISUAL_STRUCTURE`:

JSON

```
{
    "fan_status": "expanded_bullish",
    "expansion_ratio": 0.85,
    "slope_angle": 32.5,
    "structural_break_detected": false,
    "fractal_confluence": 0.90,
    "action_potential": 0.82
}
```

------

### Analogía Neurobiológica del Capítulo 3:

Si el Tálamo (Capítulo 2) nos decía "estamos en un bosque", la Corteza Visual nos dice "estamos viendo un sendero inclinado con árboles alineados". No nos dice si debemos correr o no, solo nos da la **descripción geométrica perfecta** del terreno.



# Capítulo 4: Sistema Somatosensorial (Momentum y Energía)

El objetivo de este capítulo es la **Cuantificación de la Fuerza Dinámica**. Aquí dejamos de ver "formas" (geometría) para sentir la "presión" y la "velocidad" del mercado.

## 4.1. Neurona de Aceleración de Osciladores

Esta micro-neurona (`n_percep_momentum_accel.py`) procesa `RSI_Velocidad` y `ADX_Diff`.

- **Función:** No mira el valor absoluto del RSI, sino su **derivada** (qué tan rápido está cambiando).
- **Micro-decisión:** Detecta "Squeezes" o explosiones de velocidad. Si el `ADX_Diff` es positivo y creciente, la neurona informa de una **ignición de tendencia**.
- **Analogía Cerebral:** Corpúsculos de Pacini en la piel, que no detectan el contacto suave, sino la **vibración y los cambios rápidos de presión**. Esta neurona siente el "pulso" del mercado.

## 4.2. Neurona de Divergencia Estocástica (El Sensor de Fatiga)

Esta unidad compara los máximos del `Close_Price` con los máximos del `RSI_Val` y `MACD_Val`.

- **Función:** Busca discrepancias. Si el precio sube pero el momentum baja, la neurona detecta una **pérdida de presión interna**.
- **Micro-decisión:** Emite una señal de "Agotamiento Sensorial". Es una advertencia de que, aunque el mercado parece fuerte visualmente, su energía interna se está drenando.
- **Analogía:** Propiocepción de fatiga muscular. Tus ojos ven la meta, pero tus nervios sensoriales le informan al cerebro que el músculo ya no tiene glucosa para mantener ese ritmo.

## 4.3. Neurona de Inercia de Tendencia (Fuerza Bruta)

Esta neurona se especializa en el `ADX_Val` y la relación entre `DI_Plus` y `DI_Minus`.

- **Función:** Mide la **dominancia**. Calcula la brecha entre los compradores y vendedores.
- **Micro-decisión:** Define si el movimiento es "Tendencia Real" o solo un "Ruido Volátil". Si la brecha entre DI+ y DI- se ensancha, la neurona informa de una **Inercia Dominante**.
- **Analogía:** El sentido de la carga. Es como cargar una mochila: el cerebro siente el peso constante. El ADX alto le dice al cerebro que hay un peso real (masa de órdenes) moviendo el precio.

## 4.4. Neurona de Resonancia de Ciclos

- **Función:** Analiza si el ciclo del MACD está cruzando la línea de cero en sincronía con la `EMA_10`.
- **Micro-decisión:** Identifica el "Sweet Spot" o punto de máxima armonía donde todos los sensores de energía apuntan en la misma dirección.
- **Analogía:** El ritmo cardíaco. El cerebro detecta cuando la respiración y el pulso se sincronizan para un esfuerzo máximo (el "estado de flujo").

## 4.5. Salida Sináptica del Capítulo 4

Los resultados se publican en Redis bajo la clave `SOMATIC_MOMENTUM`:

JSON

```
{
    "momentum_velocity": 0.78,
    "acceleration_state": "increasing",
    "exhaustion_warning": false,
    "trend_inertia_score": 0.92,
    "divergence_detected": "none",
    "action_potential": 0.88
}
```

------

### Analogía Neurobiológica del Capítulo 4:

Si la Corteza Visual (Capítulo 3) nos decía que el terreno era una subida, el Sistema Somatosensorial nos dice **a qué velocidad corremos** y **qué tan cansados están nuestros pulmones**. Si el terreno es alcista pero el sistema somatosensorial detecta agotamiento, el cerebro empezará a preparar una señal de freno.





# Capítulo 5: Sistema Vestibular (Volatilidad y Ruido)

El objetivo de este capítulo es la **Verificación de la Realidad**. Aquí, el cerebro decide si el "terreno" es estable o si hay un terremoto (volatilidad extrema) que invalida cualquier patrón visual o de momentum detectado anteriormente.

## 5.1. Neurona de Presión de Volumen (Masa Crítica)

Esta micro-neurona (`n_percep_vol_pressure.py`) analiza el `Volumen_Relativo`.

- **Función:** Compara el volumen actual con su media móvil. Determina si los movimientos del precio están respaldados por "masa" (dinero real) o si son movimientos "huecos" producidos por falta de liquidez.
- **Micro-decisión:** Genera un coeficiente de **Validación de Esfuerzo**. Si el precio se mueve mucho pero con poco volumen, la neurona informa de una "Falsa Alerta".
- **Analogía Cerebral:** El sentido de la gravedad. Te dice si tienes los pies en suelo firme o si estás flotando. El volumen alto es el "suelo firme" del trading.

## 5.2. Neurona de Expansión de Rango (ATR Relativo)

Procesa el `ATR_Rel` y el `ATR_Act`.

- **Función:** Detecta picos de volatilidad inusuales. Mide si el rango de las velas actuales es "anormal" comparado con la historia reciente.
- **Micro-decisión:** Define el **Nivel de Turbulencia**. Si el ATR se dispara repentinamente, la neurona envía una señal de alerta de "Mercado Errático".
- **Analogía:** El sistema de equilibrio. Cuando hay turbulencia en un avión, tu sistema vestibular te dice que dejes de caminar. Aquí, la alta volatilidad le dice al cerebro: "No intentes calcular patrones, el equilibrio se ha perdido".

## 5.3. El Autoencoder de Verificación de Realidad (Filtro de Ruido)

Esta es la red más sofisticada del lóbulo (`n_percep_noise_filter.py`).

- **Arquitectura:** **Autoencoder Neuronal**.
- **Función:** Toma todas las variables del dataset e intenta comprimirlas y reconstruirlas.
- **Misión:** Si la red puede reconstruir el estado actual con bajo error, significa que el mercado sigue un **patrón lógico conocido**. Si el error de reconstrucción es alto, significa que el mercado está en un estado de **entropía total (ruido)**.
- **Analogía:** La coherencia sensorial. Si ves un objeto flotando y moviéndose en contra de la física, tu cerebro duda de lo que ve. El Autoencoder es el "detector de alucinaciones".

## 5.4. Neurona de Costo Transaccional (Filtro de Viabilidad)

- **Función:** Analiza el Spread y la latencia en tiempo real.
- **Micro-decisión:** Si el Spread es mayor al 10% del ATR actual, esta neurona publica una **Inhibición de Costo**.
- **Analogía:** El umbral del dolor. Si para conseguir comida tienes que cruzar un campo de espinas, el cerebro te dice que no vale la pena el esfuerzo.

## 5.5. Salida Sináptica Final: El Mapa Sensorial Completo

Este capítulo cierra el Lóbulo de Percepción publicando en Redis la clave `VESTIBULAR_VALIDITY`:

JSON

```
{
    "volume_confirmation": 0.85,
    "turbulence_index": 0.20,
    "reconstruction_error": 0.02,
    "market_is_logical": true,
    "cost_viability": 0.95,
    "action_potential": 0.90
}
```

------

### Resumen del Lóbulo de Percepción

Hemos completado los 5 capítulos. Ahora tu cerebro tiene:

1. **Datos limpios** (Capítulo 1).
2. **Contexto de Régimen** (Capítulo 2).
3. **Estructura Visual** (Capítulo 3).
4. **Energía de Momentum** (Capítulo 4).
5. **Validación de Realidad** (Capítulo 5).