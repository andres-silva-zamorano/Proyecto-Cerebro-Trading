@echo off
title CEREBRO ALPHA v3.0 - LIVE MT5/BTCUSD
color 0A
echo ============================================================
echo      SISTEMA DE TRADING HFT - MODO LIVE DESPIERTO
echo ============================================================

echo [1/4] Iniciando Medula Espinal (Redis)...
:: Lanzamos Redis en segundo plano
start "REDIS_SERVER" /min redis-server

:: Esperamos a que el servidor este listo
timeout /t 3 /nobreak > nul

echo [2/4] Ejecutando Limpieza de Memoria (Reset Live)...
:: Limpiamos Redis para que el PnL Diario y los bloques empiecen en cero
echo     -^> Vaciando base de datos Redis...
redis-cli flushall

:: Reseteamos la Matriz de Reputacion
:: Nota: Se eliminaron los parentesis internos para evitar errores de sintaxis en Batch
if exist "modelos\matriz_reputacion.json" (
    echo     -^> Limpiando Matriz de Reputacion - Reset de Aprendizaje...
    del /f /q "modelos\matriz_reputacion.json"
)

echo ✅ Memoria Limpia. Sincronizacion lista.
echo.

echo [3/4] Lanzando Monitor Visual Alpha...
:: Abrimos el monitor en una ventana dedicada
start "MONITOR_ALPHA_LIVE" cmd /k "python brain_monitor.py"

timeout /t 2 /nobreak > nul

echo [4/4] Despertando Organismo Digital (Orquestador)...
echo ATENCION: Asegurate que MT5 este abierto con Algo-Trading activo.
echo.
:: Lanzamos el orquestador con -u para log en tiempo real
start "LOGICA_CEREBRO_ALPHA" cmd /k "python -u brain_orchestrator.py"

echo ============================================================
echo 🚀 ALPHA ESTA OPERANDO - Sincronizado con Servidor MT5
echo ============================================================
echo Puedes minimizar esta ventana. No cierres las otras.
pause