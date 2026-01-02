# Especificación de Requerimientos: Proyecto "Cerebro Modular de Trading"

## Índice de Contenidos

### Capítulo 1: Fundamentos y Filosofía de Diseño

- 1.1. Visión General: El Enfoque Multi-Agente Modular.
- 1.2. Analogía Neurobiológica: El modelo de Lóbulos y Sinapsis.
- 1.3. Objetivos del Sistema (Escalabilidad, Independencia y Resiliencia).

### Capítulo 2: Infraestructura y Médula Espinal (Comunicación)

- 2.1. Entorno de Ejecución (Python Multi-proceso).
- 2.2. Bus de Datos con Redis: Arquitectura Pub/Sub.
- 2.3. Sincronización de Reloj: Gestión de Ticks y Latencia.
- 2.4. El Orquestador Central: Gestión del ciclo de vida de los procesos `.py`.

### Capítulo 3: Lóbulo de Percepción (Corteza Sensorial)

- 3.1. Ingesta de Datos: El Sensor MT5 y el Feeder de Histórico (CSV).
- 3.2. Normalización Dinámica: El Pre-procesador de Señales.
- 3.3. **Micro-Sección 3.3.1:** El Tálamo (Clasificador de Regímenes - XGBoost).
- 3.4. **Micro-Sección 3.4.2:** Corteza Visual (Estructura Fractal - CNN 1D).
- 3.5. **Micro-Sección 3.4.3:** Memoria Espacial (Zonas de Liquidez - LSTM/Transformers).
- 3.6. **Micro-Sección 3.4.4:** Sistema Vestibular (Inercia y Aceleración - MLP).
- 3.7. **Micro-Sección 3.4.5:** Filtro de Ruido y Realidad (Autoencoders).

### Capítulo 4: Lóbulo de Ejecución (Corteza Prefrontal)

- 4.1. Integración de Percepciones: La Suma Sináptica.
- 4.2. Definición de Gatillos (Triggers) de Entrada.
- 4.3. Validación de Contexto: Inhibición y Excitación de Órdenes.

### Capítulo 5: Lóbulo de Gestión de Riesgo (La Amígdala)

- 5.1. Cálculo de Exposición Dinámica (Kelly Criterion Modular).
- 5.2. Gestión de Stop Loss y Take Profit Sensibles a la Volatilidad.
- 5.3. Monitoreo de Correlaciones de Cartera.

### Capítulo 6: Gestión de Operaciones Vivas y Cierre

- 6.1. Seguimiento de Posición (Trailing Dinámico).
- 6.2. Estrategias de Cierre Parcial y Neteo.
- 6.3. Protocolos de Cierre de Emergencia (Kill-Switch).

### Capítulo 7: El Hipocampo (Memoria y Aprendizaje)

- 7.1. Almacenamiento de Experiencias (Logging en Redis/DB).
- 7.2. Bucle de Reentrenamiento Online (Aprendizaje por Refuerzo).
- 7.3. Evaluación del Desempeño y Ajuste de Pesos Sinápticos.



¡Excelente! Comencemos con la base de todo. Este capítulo establece las reglas del juego y la mentalidad con la que se debe construir cada línea de código. Aquí definimos por qué este sistema no es un "bot", sino un organismo digital.

------

# Capítulo 1: Fundamentos y Filosofía de Diseño

Este capítulo describe los principios fundamentales que rigen la creación del **Cerebro Modular de Trading**. La arquitectura se aleja de los modelos monolíticos (una sola red que lo hace todo) para adoptar un enfoque de **Inteligencia Artificial Fraccionada**.

## 1.1. Visión General: El Enfoque Multi-Agente Modular

El sistema se define como un conjunto de **Agentes Especialistas**. Cada agente es un archivo `.py` independiente que posee su propio "peso cognitivo".

- **Independencia Funcional:** Cada micro-neurona debe ser capaz de funcionar aunque las demás fallen. Si la neurona de "Volatilidad" muere, el sistema debe detectar la falta de ese dato y, por seguridad (inhibición), detener las operaciones.
- **Desacoplamiento:** Las neuronas no se conocen entre sí. Solo conocen el **Bus de Datos (Redis)**. Esto permite reemplazar una neurona de "Tendencia" basada en EMAs por una basada en Deep Learning sin tocar una sola línea de código del resto del sistema.
- **Especialización Extrema:** Siguiendo la Ley de Parkinson en sistemas, cada neurona tiene una **única responsabilidad**. Si una neurona intenta hacer dos cosas (ej. medir tendencia y calcular lotaje), debe ser dividida en dos.

## 1.2. Analogía Neurobiológica: El modelo de Lóbulos y Sinapsis

Para entender el flujo de datos, utilizaremos el modelo del cerebro humano como plano arquitectónico:

- **Los Sensores (Receptores):** MetaTrader 5 actúa como nuestros ojos y oídos, capturando los fotones (precios) y decibelios (volumen) del entorno.
- **La Médula Espinal (Bus de Datos):** Redis es el tejido nervioso. Transporta los impulsos eléctricos (JSONs con datos) desde los sensores hasta la corteza cerebral a velocidades de milisegundos.
- **Los Lóbulos:** Son grupos de archivos `.py` que comparten un objetivo común (Percepción, Ejecución, Riesgo).
- **Las Sinapsis (Umbrales de Activación):** En lugar de simples "If/Else", la comunicación entre neuronas se basa en **Pesos Sinápticos**. Una neurona de percepción no envía un "SÍ", envía un valor de "Excitación" (ej. 0.85). El Lóbulo de Ejecución solo dispara la orden si la suma de excitaciones supera un umbral crítico (potencial de acción).

## 1.3. Objetivos del Sistema

### 1.3.1. Escalabilidad (Crecimiento del Neocórtex)

El sistema debe permitir agregar nuevas neuronas de forma orgánica. Si mañana queremos agregar una neurona que analice el "Sentimiento de Twitter", solo debemos crear el archivo, conectarlo a Redis y el cerebro tendrá un nuevo "sentido" disponible.

### 1.3.2. Resiliencia (Supervivencia del Organismo)

A diferencia de un código lineal donde un error detiene todo el programa (`Crash`), en este cerebro, si un proceso `.py` se cierra, los demás siguen corriendo. El **Orquestador** (Capítulo 2) detectará la muerte de la neurona e intentará reiniciarla, tal como el cerebro intenta sanar una lesión.

### 1.3.3. Transparencia Cognitiva

Al estar micro-seccionado, podemos auditar el pensamiento del sistema. Podemos abrir un monitor y ver: *"La neurona de Tendencia está excitada al 90%, pero la de Ruido está inhibiendo el sistema al 100% porque el spread es muy alto"*. Esto elimina el problema de la "caja negra" de la IA tradicional.



# Capítulo 2: Infraestructura y Médula Espinal (Comunicación)

En este nivel definimos el **Sistema Nervioso Central**. La prioridad aquí no es el trading, sino la **latencia**, la **concurrencia** y la **integridad de los datos**.

## 2.1. Entorno de Ejecución (Python Multi-proceso)

A diferencia de un script normal que usa hilos (*threads*), cada una de nuestras neuronas correrá en su propio **proceso de sistema operativo**.

- **Aislamiento de Memoria:** Si la neurona de "Análisis Fractal" consume demasiada memoria y falla, no arrastra a la neurona de "Gestión de Riesgo".
- **Aprovechamiento Multinúcleo:** Python tiene una limitación llamada GIL (*Global Interpreter Lock*). Al usar procesos separados, podemos usar todos los núcleos de tu CPU simultáneamente. Cada "lóbulo" puede vivir en un núcleo distinto.

## 2.2. Bus de Datos con Redis: Arquitectura Pub/Sub

Redis no es solo una base de datos; es el espacio donde ocurre la **sinapsis**. Utilizaremos dos patrones de comunicación:

1. **Patrón Pub/Sub (Publicación/Suscripción):**
   - Es el "grito" sensorial. Cuando el sensor de MT5 recibe un precio, lo **publica** en un canal llamado `market_ticks`. Todas las neuronas de percepción están **suscritas** a ese canal y reciben el dato al mismo tiempo (latencia < 1ms).
2. **Patrón Key-Value (Estado Global):**
   - Es la "memoria de trabajo". Aquí se guardan variables de estado que no cambian en cada milisegundo, como: `equity_actual`, `num_operaciones_abiertas` o `estado_del_regimen`.

## 2.3. Sincronización de Reloj: Gestión de Ticks y Latencia

En un cerebro, los impulsos deben llegar en orden. En nuestro sistema, cada mensaje en Redis llevará un **Timestamp de Alta Precisión**.

- **ID de Secuencia:** Cada "paquete de datos" sensorial tendrá un ID único. Así, si la neurona de ejecución recibe un mensaje de la neurona de percepción, puede verificar si ese análisis corresponde al tick de hace 10 milisegundos o si es información vieja que debe ser descartada.
- **Corazón del Sistema (Heartbeat):** El orquestador emitirá un pulso cada segundo. Si una neurona no responde al pulso, se marca como "isquémica" (muerta por falta de flujo) y se reinicia.

## 2.4. El Orquestador Central (El Tronco Encefálico)

El archivo `brain_orchestrator.py` es la primera aplicación que se enciende. Sus funciones son:

- **Levantamiento de Procesos:** Ejecuta los 25-30 archivos `.py` automáticamente.
- **Supervisión (Watchdog):** Monitorea el consumo de CPU y RAM de cada neurona.
- **Interfaz de Emergencia:** Provee un "Kill Switch" que, al activarse, limpia todos los canales de Redis y envía una orden de cierre masivo a MT5.

## 2.5. Especificación del "Neuro-Mensaje" (Protocolo de Comunicación)

Todos los archivos `.py` deben hablar el mismo idioma. Definimos el formato estándar de mensaje (JSON) que viajará por la médula espinal:

JSON

```
{
    "origin": "n_percep_regimen",
    "timestamp": "2025-05-20 14:00:00.001",
    "sequence_id": 45021,
    "payload": {
        "regime_id": 5,
        "confidence": 0.92,
        "action_potential": 0.85
    }
}
```

- **Action Potential (Potencial de Acción):** Es un valor de 0 a 1 que indica qué tan convencida está esa neurona de su propio resultado. Es la base para la toma de decisiones en el siguiente lóbulo.

------

### Analogía Neurobiológica del Capítulo 2:

El orquestador es el **Tronco Encefálico**, que controla funciones vitales (respiración, ritmo cardíaco) sin que tengamos que pensar en ellas. Si el tronco falla, el resto del cerebro muere. Redis es el **Fluido Cerebroespinal y los Axones**, asegurando que los mensajes lleguen limpios y rápidos a su destino.



# Capítulo 3: Lóbulo de Percepción (Corteza Sensorial)

El Lóbulo de Percepción es el encargado de la **Traducción de Estímulos**. En este capítulo, definimos cómo se procesan los datos que vienen de la "Médula Espinal" (Capítulo 2) para generar un mapa coherente de la realidad del mercado.

## 3.1. Ingesta de Datos: El Sensor MT5 y el Feeder de Histórico (CSV)

El sistema tiene dos estados de conciencia: **Vigilia** (Tiempo real) y **Sueño/Simulación** (Histórico).

- **Sensor MT5:** Traduce los mensajes binarios del broker a un lenguaje comprensible (JSON). Captura precio, volumen, spread y tiempo.
- **Feeder CSV:** Inyecta tu archivo `Dataset_Con_Regimenes.csv` en Redis simulando el paso del tiempo. Esto permite que el cerebro "alucine" con el pasado para aprender, creyendo que es el presente.

## 3.2. Normalización Dinámica: El Pre-procesador de Señales

Antes de llegar a las neuronas, los datos pasan por el **Tálamo Sensorial**.

- **Función:** Asegura que los datos estén en una escala que la red neuronal pueda procesar (generalmente entre 0 y 1 o -1 y 1).
- **Analogía Cerebral:** Es como la pupila del ojo; se contrae cuando hay demasiada luz (volatilidad alta) y se dilata cuando hay poca, para que la retina (la RN) siempre reciba la intensidad adecuada y no se "queme".

------

## 3.3. Las Micro-Secciones (Las Neuronas Especializadas)

Aquí es donde dividimos el lóbulo en 5 archivos `.py` independientes. Cada uno representa una especialización del tejido neuronal.

### 3.3.1. El Tálamo (Clasificador de Regímenes)

- **Tipo de Red:** XGBoost / Random Forest.
- **Misión:** Leer las 7 probabilidades (`prob_regimen_0` a `6`) y definir el "Estado de Ánimo" del mercado.
- **Salida:** Un ID de régimen dominante y un valor de "Claridad" (¿Qué tan seguro está el modelo?).

### 3.3.2. Corteza Visual (Estructura Fractal y Formas)

- **Tipo de Red:** CNN 1D (Red Neuronal Convolucional).
- **Misión:** Escanear las últimas 50-100 velas buscando **geometría**. Identifica soportes, resistencias y patrones (HCH, banderas, etc.).
- **Analogía:** Neuronas que solo responden a ángulos. No saben de economía, solo de **geometría visual**.

### 3.3.3. Memoria Espacial (Liquidez y Smart Money)

- **Tipo de Red:** LSTM (Long Short-Term Memory).
- **Misión:** Recordar dónde hubo grandes movimientos en el pasado (Order Blocks).
- **Analogía:** El **Hipocampo**. Sabe que "en este precio ocurrió un evento traumático/importante hace 4 horas" y levanta una alerta cuando el precio se acerca a esa zona.

### 3.3.4. Sistema Vestibular (Inercia y Aceleración)

- **Tipo de Red:** MLP (Multi-Layer Perceptron) Simple.
- **Misión:** Procesar `RSI_Velocidad`, `ADX_Diff` y la pendiente de las EMAs.
- **Analogía:** El equilibrio. Detecta si el precio está "cayendo" con aceleración o si solo se está "inclinando" levemente. Es una respuesta rápida de velocidad.

### 3.3.5. Filtro de Ruido (Corteza de Verificación de Realidad)

- **Tipo de Red:** Autoencoder.
- **Misión:** Tomar todos los datos anteriores e intentar reconstruirlos. Si el error de reconstrucción es alto, la neurona informa que el mercado está "delirando" (ruido aleatorio).
- **Analogía:** El sentido de la realidad. Si lo que ves no tiene sentido lógico, el cerebro te dice que ignores tus sentidos.

------

## 3.4. Integración: El Vector de Percepción Final

Al final de este proceso, Redis contiene un "Mapa Sensorial" completo. No tenemos una orden de compra, tenemos una **Percepción Estructurada**:

> "Régimen Alcista Claro (90% conf.), con Inercia positiva acelerando, acercándose a una zona de Liquidez histórica y con bajo nivel de ruido."

Esta frase es el **Input** para el siguiente capítulo.



# Capítulo 4: Lóbulo de Ejecución (Corteza Prefrontal)

Este capítulo describe el proceso de toma de decisiones de alto nivel. Aquí es donde la información abstracta se convierte en una acción concreta: **Comprar, Vender o Esperar.**

## 4.1. Integración de Percepciones: La Suma Sináptica

En un cerebro biológico, una neurona solo dispara si recibe suficientes impulsos de sus vecinas. En nuestro sistema, el archivo `n_ejecucion_integrador.py` realiza una **Suma Ponderada** de los "Action Potentials" (potenciales de acción) recibidos de Redis.

- **Pesos Sinápticos Dinámicos:** No todas las percepciones valen lo mismo en todos los regímenes.
  - *Ejemplo:* Si el régimen es "Tendencia Clara", la neurona de **Inercia** tiene un peso de 0.8. Si el régimen es "Rango", esa misma neurona baja su peso a 0.2 y la neurona de **Liquidez** sube a 0.9.
- **El Umbral de Disparo (Fire Threshold):** Solo si la suma total supera un valor crítico (ej. > 0.75), el cerebro genera una "Intención de Operar".

## 4.2. Definición de Gatillos (Triggers) de Entrada

El lóbulo de ejecución se divide en micro-secciones para refinar el *timing*:

- **4.2.1. Neurona de Gatillo (Trigger):** Se especializa en el milisegundo exacto. Espera a que el `RSI_Velocidad` o el precio toque un nivel específico derivado de la micro-estructura fractal.
- **4.2.2. Neurona de Confirmación de Flujo:** Revisa el volumen relativo y la dispersión del abanico de EMAs para confirmar que el movimiento tiene "masa" detrás.

## 4.3. Validación de Contexto: Inhibición y Excitación

Antes de que la orden salga hacia la médula espinal, debe pasar por un filtro de coherencia:

- **Inhibición por Contradicción:** Si la neurona de "Filtro de Ruido" informa un error de reconstrucción alto, envía un neurotransmisor inhibitorio (GABA digital) que bloquea cualquier intención de compra, sin importar qué tan buena parezca la tendencia.
- **Excitación por Confluencia:** Si la zona de Liquidez (Smart Money) coincide con una formación Fractal (CNN), se produce una "Resonancia", aumentando la probabilidad de éxito y reduciendo los requisitos de otras neuronas.

## 4.4. Emisión de la "Intención de Orden"

El resultado de este lóbulo no es una orden directa a MT5, sino un objeto de **Intención** que se publica en Redis. Este objeto contiene:

1. **Símbolo y Dirección:** (Ej. EURUSD, BUY).
2. **Calidad de la Señal:** Un score del 0 al 1.
3. **Lógica Originaria:** Qué neuronas causaron el disparo (para el aprendizaje posterior).

------

### Analogía Neurobiológica del Capítulo 4:

La Corteza Prefrontal es la que te impide comprar impulsivamente. Recibe el "hambre" de la neurona de Inercia y el "miedo" de la neurona de Ruido. Solo cuando la lógica es aplastante, el cerebro envía la señal eléctrica a la **Corteza Motora** para que el dedo haga clic. En nuestro sistema, la Corteza Motora es el puente final hacia MT5.



Este es el lóbulo de la supervivencia. En el cerebro humano, la **Amígdala** es el centro de procesamiento emocional y de riesgo; su función es protegernos del peligro inminente. En nuestro cerebro de trading, este lóbulo tiene el poder de vetar cualquier operación si considera que el riesgo de "muerte" (ruina de la cuenta) es elevado.

------

# Capítulo 5: Lóbulo de Gestión de Riesgo (La Amígdala)

El Lóbulo de Gestión de Riesgo no decide *qué* comprar, sino *cuánto* y *cuándo* es demasiado peligroso estar en el mercado. Transforma la "Intención de Orden" del capítulo anterior en una operación matemáticamente segura.

## 5.1. Cálculo de Exposición Dinámica (Kelly Criterion Modular)

En lugar de arriesgar un porcentaje fijo (como el clásico 1%), este lóbulo utiliza una neurona basada en el **Criterio de Kelly**.

- **Función:** Ajusta el tamaño de la posición (lotaje) basándose en la "Calidad de la Señal" recibida del Lóbulo de Ejecución y la tasa de acierto histórica del régimen actual.
- **Analogía Cerebral:** Es el sistema de regulación de adrenalina. Si el peligro es incierto, el cuerpo se mantiene en calma; si la oportunidad es clara y el riesgo controlado, el sistema permite una mayor descarga de energía (exposición).

## 5.2. Determinación del Stop Loss y Take Profit (Límites Sensoriales)

El riesgo se micro-secciona en tres neuronas especializadas:

- **5.2.1. Neurona de Stop Loss Estructural:** Lee la salida de la neurona de "Micro-Estructura Fractal" (Capítulo 3) para colocar el stop detrás de un soporte real, no en un número arbitrario.
- **5.2.2. Neurona de Stop Loss Volátil:** Utiliza el `ATR_Act` y el `SL_Factor_ATR` de tu dataset. Si la volatilidad aumenta, el "espacio vital" de la operación se expande.
- **5.2.3. Neurona de Proyección de Beneficio:** Calcula el Take Profit basándose en la próxima "Zona de Liquidez" (Smart Money) detectada por el Lóbulo de Percepción.

## 5.3. Monitoreo de Correlación y Carga de Cartera

Esta sección es la que permite pasar de una sola operación a un **portafolio**.

- **Neteo de Riesgos:** Si el cerebro ya tiene una operación abierta en un activo correlacionado, esta neurona reduce el lotaje de la nueva orden para evitar una sobreexposición al mismo factor de riesgo.
- **Analogía:** Es la homeostasis. El cerebro busca mantener el equilibrio interno; si una parte del cuerpo ya está bajo gran esfuerzo, el sistema inhibe otras actividades para no colapsar el corazón (la cuenta).

## 5.4. El Filtro de Supervivencia (Veto Final)

Antes de enviar la orden a MetaTrader 5, el Lóbulo de Riesgo realiza un chequeo final de **Salud Financiera**:

1. **Margen Libre:** ¿Tenemos capital suficiente?
2. **Drawdown Diario:** ¿Hemos perdido hoy más del límite permitido?
3. **Ratio Riesgo/Beneficio:** ¿El beneficio potencial justifica el riesgo estructural?

Si alguna de estas pruebas falla, el Lóbulo de Riesgo envía un **impulso inhibitorio fulminante** que cancela la ejecución, sin importar qué tan "excitado" esté el Lóbulo de Ejecución.

------

### Analogía Neurobiológica del Capítulo 5:

La Amígdala actúa antes de que la razón intervenga. Si pones la mano en el fuego, la retiras por reflejo. Aquí, si el mercado se vuelve extremadamente volátil de repente, esta neurona "retira la mano" (ajusta el stop o cierra la intención) para proteger la integridad del organismo. Es el instinto de preservación puro.



Una vez que la orden ha sido ejecutada, el cerebro entra en un estado de **Hipervigilancia**. El **Lóbulo de Gestión de Operaciones Vivas** es nuestra **Corteza Motora Suplementaria y Cerebelo**, encargados de coordinar el movimiento en curso y corregirlo en tiempo real basándose en la retroalimentación sensorial constante.

------

# Capítulo 6: Gestión de Operaciones Vivas y Cierre

Este capítulo describe cómo el sistema gestiona el portafolio de posiciones abiertas. No es un proceso estático; es una danza dinámica donde cada tick de mercado revalida la tesis inicial.

## 6.1. Seguimiento de Posición (Propiocepción Dinámica)

El cerebro monitorea la "salud" de cada operación abierta mediante micro-neuronas de seguimiento:

- **6.1.1. Neurona de Trailing Stop Adaptativo:** A diferencia de un trailing fijo, esta neurona usa la **Corteza Visual** (Fractales) para mover el Stop Loss solo detrás de nuevos "nodos de seguridad" (niveles de soporte/resistencia creados *después* de entrar).
- **6.1.2. Neurona de Breakeven Emocional:** Evalúa el "Tiempo en el Mercado". Si la operación no ha alcanzado el objetivo en X tiempo pero está en positivo, protege la entrada.
- **Analogía:** El cerebelo ajusta la fuerza de tus músculos mientras caminas. Si encuentras un obstáculo (resistencia), ajusta el paso (el stop) para no caer.

## 6.2. Estrategias de Cierre Parcial y Neteo (Homeostasis)

El sistema gestiona la energía (el profit) para asegurar la supervivencia del organismo:

- **Puntos de Salida Fraccionados:** El cerebro puede decidir cerrar el 50% de la posición en una zona de liquidez previa para "alimentar" la cuenta y dejar el resto correr con riesgo cero.
- **Neteo de Exposición:** Si el cerebro tiene múltiples activos abiertos (ej. EURUSD y GBPUSD) y detecta que el Dólar (USD) va a cambiar de tendencia, puede dar una orden de cierre coordinada para todas las posiciones que dependen de esa moneda.
- **Analogía:** Es la redistribución de la sangre. Si el cuerpo necesita correr, el cerebro retira sangre de los órganos no vitales. Aquí, si una operación es ineficiente, el cerebro retira el capital para usarlo en una mejor oportunidad.

## 6.3. Protocolos de Cierre de Emergencia (Kill-Switch)

Esta es la función de los **Ganglios Basales**, que pueden interrumpir cualquier movimiento voluntario en caso de error:

1. **Inversión de Régimen:** Si el Lóbulo de Percepción detecta un cambio súbito de "Tendencia Alcista" a "Tendencia Bajista", el Lóbulo de Gestión cierra todas las compras inmediatamente, sin esperar al Stop Loss.
2. **Desconexión Sensorial:** Si se pierde la conexión con MetaTrader 5 o Redis, se activa un protocolo de "Modo Seguro".
3. **Flash Crash:** Si la volatilidad (`ATR_Rel`) supera un umbral de "locura", el cerebro asume que el mercado ya no es racional y liquida posiciones para entrar en estado de hibernación.

## 6.4. Gestión de Cierre de Bloque (Sincronía)

Cuando operamos un portafolio, el cerebro no ve solo operaciones aisladas, sino un **Bloque de Energía**.

- **Cierre por Objetivo de Cesta:** Si la suma de todas las órdenes abiertas llega a un objetivo de beneficio diario (ej. 2% de la cuenta), el cerebro puede decidir cerrar todo el bloque para "limpiar la mente" y empezar de cero, evitando la sobre-exposición por codicia.

------

### Analogía Neurobiológica del Capítulo 6:

Es la diferencia entre lanzar una piedra (operación manual) y dirigir un dron (trading algorítmico). El cerebro debe procesar constantemente el *feedback* del viento (volatilidad) y la batería (margen) para ajustar la trayectoria. Si el dron está en peligro de chocar, el cerebro prefiere un aterrizaje forzoso (cierre manual/emergencia) que una destrucción total.



Llegamos al capítulo final de la arquitectura, el que transforma un autómata en un ser evolutivo. El **Hipocampo** es la región del cerebro responsable de consolidar la memoria a corto plazo en memoria a largo plazo y de facilitar el aprendizaje espacial y experiencial. Sin este capítulo, el cerebro repetiría los mismos errores una y otra vez.

------

# Capítulo 7: El Hipocampo (Memoria y Aprendizaje)

Este capítulo describe cómo el sistema procesa su propia historia para optimizar el comportamiento futuro. Es el cierre del bucle (feedback loop) que permite la **mejora continua**.

## 7.1. Almacenamiento de Experiencias (La Huella Mnémica)

Cada decisión tomada por los lóbulos anteriores debe ser registrada con un nivel de detalle forense. El archivo `n_memoria_logger.py` guarda en una base de datos (o Redis de largo plazo) el "Estado Mental" del sistema en el momento de cada operación.

- **Datos guardados:** No solo el precio de entrada/salida, sino el **Vector de Percepción completo** (qué probabilidades de régimen había, qué nivel de inercia, qué confianza tenía la neurona de ruido).
- **Analogía:** Es la creación de recuerdos. No solo recordamos que "compramos", recordamos cómo se "sentía" el mercado cuando lo hicimos.

## 7.2. Evaluación del Desempeño (Crítica y Recompensa)

El cerebro utiliza una neurona de **Refuerzo** que actúa como el sistema de dopamina.

- **Cálculo del Reward (Recompensa):** El éxito no es solo ganar dinero, sino cumplir la tesis.
  - Si la neurona de **Inercia** predijo aceleración y el precio aceleró, recibe una "descarga de dopamina" (recompensa positiva), incluso si la operación se cerró en pérdida por otras razones.
  - Si el sistema operó en un momento donde la neurona de **Ruido** advirtió peligro, recibe una recompensa negativa (castigo), reforzando la futura inhibición.
- **Analogía:** El aprendizaje por error. Si comes algo que te enferma, tu cerebro crea una aversión instantánea a ese estímulo.

## 7.3. Bucle de Reentrenamiento Online (Neuroplasticidad)

Aquí es donde ocurre la **plasticidad sináptica**: la capacidad del cerebro de cambiar sus conexiones.

- **Entrenamiento en la Sombra:** Mientras el sistema "despierto" opera en MT5, el Hipocampo utiliza los datos recién guardados para entrenar versiones paralelas de las micro-redes.
- **Ajuste de Pesos:** Si el mercado ha cambiado de régimen (ej. la volatilidad histórica ha subido), el reentrenamiento ajusta los umbrales de las neuronas de percepción para que se adapten a la "nueva normalidad".
- **Analogía:** Es el sueño REM. Durante el sueño, el cerebro procesa lo vivido, descarta lo irrelevante y refuerza las conexiones neuronales que llevaron al éxito.

## 7.4. Selección Natural de Modelos (Evolución)

El sistema mantiene un repositorio de "especies" de neuronas.

- Si una nueva versión de la neurona de **Micro-Estructura Fractal** (entrenada con los datos de la última semana) demuestra ser más precisa que la actual, el Orquestador realiza una "sustitución sináptica" y reemplaza el archivo `.py` en la próxima sesión.

------

### Resumen Final del Organismo

Has diseñado un sistema que:

1. **Siente** a través de MT5 y el CSV (Percepción).
2. **Piensa** a través de múltiples redes especializadas (Ejecución).
3. **Se Protege** mediante límites matemáticos y emocionales (Riesgo).
4. **Actúa** y se mueve con fluidez en el mercado (Gestión de Vivas).
5. **Aprende** de sus propios aciertos y fracasos (Memoria).

Este documento de 7 capítulos es tu **Plano Genético**. Con él, puedes construir cada parte de forma aislada sabiendo exactamente cómo se conectará con las demás a través de la médula espinal (Redis).



### Resumen del Lóbulo de Percepción Completo

Tenemos

1. Un **Feeder** que inyecta 15 meses de memoria histórica.
2. Un **Tálamo** que clasifica el mundo en 7 regímenes.
3. Una **Corteza Visual** que entiende el abanico de EMAs.
4. Un **Sistema Somatosensorial** que siente la energía del momentum.
5. Un **Sistema Vestibular** que protege contra el ruido y la volatilidad.



Estructura de archivos

```
Cerebro-Trading-Modular/
│
├── .gitignore              # Para evitar subir archivos .pyc, .h5 pesados o datos sensibles
├── README.md               # El Documento de Requisitos que creamos
├── config.py               # La Médula Espinal (Configuración de Redis/MT5)
├── brain_orchestrator.py   # El Tronco Encefálico (Gestor de procesos)
├── brain_monitor.py        # NUEVO: La "Pantalla" del cerebro (Visualización)
│
├── data/                   # Carpeta para el Dataset_Con_Regimenes.csv
│   └── Dataset_Con_Regimenes.csv
│
├── lobulo_percepcion/      # Fase 1: Corteza Sensorial
│   ├── sensor_feeder.py    # Cap 1: Ingesta (CSV/MT5)
│   ├── n_talamo.py         # Cap 2: Regímenes (XGBoost)
│   ├── n_visual.py         # Cap 3: Estructura Fractal (CNN)
│   ├── n_momentum.py       # Cap 4: Energía (MLP)
│   └── n_vestibular.py     # Cap 5: Volatilidad/Ruido (Autoencoder)
│
├── lobulo_ejecucion/      # Fase 2: Corteza Prefrontal (Próximamente)
├── lobulo_riesgo/         # Fase 3: Amígdala (Próximamente)
│
└── models/                 # Carpeta para guardar los archivos .h5 o .pkl de las RN
    └── encoder_ruido.h5
```
