@echo off
title ORQUESTADOR CEREBRO ALPHA - DEMOCRACIA HFT
echo ============================================================
echo      SISTEMA DE INTELIGENCIA COLECTIVA ALPHA V3
echo ============================================================

echo [1/3] Iniciando Medula Espinal (Redis)...
:: Lanzamos Redis en segundo plano
start "REDIS SERVER" /min redis-server

timeout /t 3

echo [2/3] Lanzando Monitor de Democracia...
:: El monitor ahora nos mostrara los votos y los pesos
start "MONITOR_VISUAL" cmd /k "python brain_monitor.py"

timeout /t 2

echo [3/3] Activando Organismo (Orquestador)...
:: El orquestador se encarga de lanzar CORE y EXPERTOS (incluyendo el sensor)
:: Usamos -u para que los prints salgan en tiempo real sin buffer
start "CEREBRO_LOGICA" cmd /k "python -u brain_orchestrator.py"

echo.
echo ============================================================
echo ✅ SISTEMA EN MARCHA - Monitorea la consola del MONITOR
echo ============================================================
pause