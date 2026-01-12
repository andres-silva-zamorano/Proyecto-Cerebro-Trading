# 🗳️ Mapa del Comité de Decisión: Cerebro Alpha v3.8

En la arquitectura **v3.8**, el sistema ha evolucionado de una dictadura de contexto a una **Democracia Ponderada**. El **Tálamo H5** ya no solo observa, sino que participa activamente, permitiendo que el consenso refleje tanto la señal técnica como la claridad del entorno.

## 👥 Los 4 Votantes del Comité

### 1. IA Visual Alpha (`ia_visual_alpha_v1`)

- **Misión**: Estratega de Patrones.
- **Lógica**: Procesa una "foto" de 45 velas mediante el modelo `cerebro_hft_alpha.h5`.
- **Peso**: Aporta dirección (BUY/SELL) con una confianza derivada de la función Softmax del modelo. Es el votante con mayor capacidad de detección estructural.

### 2. Experto de Momentum (`momentum_v1`)

- **Misión**: Validador de Energía.
- **Lógica**: Verifica que el movimiento tenga fuerza real (ADX > 25) y que no esté en sobrecompra/sobreventa extrema.
- **Peso**: Actúa como un filtro de confirmación. Si no hay momentum, su voto es neutral (0), lo que suele frenar disparos impulsivos.

### 3. Tálamo Votante (`talamo_v1`) **[NUEVO v3.8]**

- **Misión**: Juez de Contexto y Tendencia.
- **Lógica**: Clasifica el mercado en 7 regímenes y emite un voto basado en la **Jerarquía de Intensidad**.
- **Jerarquía de Prioridad (Confianza)**:
  - **R0 (Lateral)**: Voto Neutral (0) | Confianza: 0%.
  - **Alcistas**:
    - R1 (Baja Vol): BUY | Confianza: 33%.
    - R3 (Alta Vol): BUY | Confianza: 66%.
    - R5 (Tendencia Fuerte): BUY | Confianza: 100%.
  - **Bajistas**:
    - R2 (Baja Vol): SELL | Confianza: 33%.
    - R4 (Alta Vol): SELL | Confianza: 66%.
    - R6 (Tendencia Fuerte): SELL | Confianza: 100%.

### 4. Guardián Vestibular (`guardian_vestibular_v1`)

- **Misión**: Filtro de Equilibrio y Ruido.
- **Lógica**: Monitorea el ATR relativo frente a los umbrales de tolerancia de cada régimen.
- **Función**: No vota dirección, sino **Potencial de Acción**. Si detecta "Ruido Alto", multiplica el consenso total por **0.1**, inhibiendo casi cualquier disparo por seguridad.

## ⚖️ Ecuación del Consenso Colectivo

El **Ejecutor Maestro** calcula la fuerza final ($C$) mediante la suma sináptica de los expertos activos, escalada por sus reputaciones y confidencias locales:

$$C = (\sum (Voto_{i} \cdot Reputación_{i} \cdot Confianza_{i})) \cdot Potencial\_Vestibular$$

### Umbrales de Mando:

1. **Entrada (Gatillo Optuna)**: Se requiere un $|C| \ge 0.75$ para abrir fuego en Pepperstone.
2. **Salida (Duda Neuronal)**: Si una posición está abierta y el $|C|$ cae por debajo de **0.2837**, el comité ordena una liquidación inmediata por pérdida de convicción colectiva.

## 🛡️ Capa de Supervivencia (Homeostasis)

Independientemente del comité, la **Homeostasis v5.8** mantiene autoridad absoluta para cerrar posiciones si:

- Se alcanza el **Take Profit Objetivo** ($236.11 USD).
- Se activa el **Trailing Stop** (Protección del 79.8% tras ganar > $100 USD).

**Nota para Vision Global**: Esta estructura descentralizada asegura que el bot sea agresivo en tendencias claras (donde el Tálamo vota con 100%) y extremadamente cauteloso en rangos laterales (donde el Tálamo se abstiene).