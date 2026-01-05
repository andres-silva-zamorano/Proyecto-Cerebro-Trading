## 🏛️ Estado Actual de la Arquitectura

El sistema ha evolucionado de un bot de trading simple a una estructura de **Sistemas Distribuidos** que imita un cerebro biológico.

### 🧠 1. El Núcleo de Decisión (Lóbulos)

- **Lóbulo de Percepción (`sensor_feeder`, `talamo`, `vestibular`):** Operativo. Detecta regímenes de mercado y niveles de ruido.
- **Lóbulo de Ejecución (`n_ejecutor`):** **EN REPARACIÓN.** Es el "Comandante". Se ha rediseñado para permitir que cada experto abra su propia orden, gestionando así un **cúmulo (cluster)** de operaciones en lugar de una sola.
- **Lóbulo de Riesgo (`n_homeostasis`):** Operativo. Actúa como el liquidador. Su función es sumar el PnL de todas las órdenes abiertas y aplicar la "Eutanasia" si se alcanza el **Stop Loss Máximo por conjunto/día**.
- **Memoria (`hipocampo` y `matriz_reputacion.json`):** Operativo. Registra el éxito de cada experto para ajustar su peso en futuras decisiones.

### 🛡️ 2. Filtros de Seguridad

- **Guardián Vestibular:** Muy activo. Está emitiendo **Vetos por Ruido Alto** constantemente, lo cual es correcto pero muy restrictivo en las configuraciones actuales.
- **Bloqueo de Refractariedad:** Implementado para evitar que el bot entre en bucles de operaciones infinitas tras un cierre.

------

## ⚠️ Bloqueos Críticos Detectados

### 1. El Error del "Gatillo" (AttributeError)

El registro muestra que el proceso `n_ejecutor.py` se detiene con el error: `AttributeError: 'EjecutorMaestro' object has no attribute 'decidir'`.

- **Impacto:** El bot lee los datos, pero cuando llega el momento de decidir, el código "muere". Por esto has corrido 13 meses de datos con **0 órdenes**. El sistema está procesando información, pero nadie tiene la capacidad de ejecutar.

### 2. Infobesidad y Seguimiento Visual

El **Orquestador** actual en PowerShell/Anaconda genera una catarata de texto difícil de leer.

- **Problema:** No puedes detectar cuándo una neurona se cae o por qué no está operando. Los colores no funcionan en tu terminal actual, eliminando la capacidad de análisis rápido.

### 3. Entorno de Windows Server 2019

Intentar instalar la nueva **Windows Terminal** ha fallado debido a dependencias de sistema (UWP) que los servidores no traen por defecto.

- **Estado:** Necesitamos una alternativa de visualización que no rompa el servidor (como **Cmder** o **Git Bash**).

------

## 📉 Resumen de la Operativa (Simulación de 13 meses)

- **Órdenes abiertas:** 0.
- **Motivo principal:** El Ejecutor está colapsado por un error de nombre de función (`decidir`).
- **Motivo secundario:** Umbrales de reputación muy altos y vetos constantes del Guardián por volatilidad/ruido.