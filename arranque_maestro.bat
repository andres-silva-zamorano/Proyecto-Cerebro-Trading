@echo off
title ORQUESTADOR CEREBRO ALPHA - HFT
echo Iniciando Medula Espinal (Redis)...
start "REDIS SERVER" /min redis-server

timeout /t 3

:: Cambiamos la forma de llamar a los scripts para que siempre vean la raiz
echo Lanzando Monitor...
start "MONITOR" cmd /k "python brain_monitor.py"

echo Lanzando Alimentador de Sensores...
:: IMPORTANTE: Ejecutarlo como modulo o llamarlo directamente desde la raiz
start "SENSORES" cmd /k "python lobulo_percepcion/sensor_feeder.py"

echo Lanzando Orquestador...
start "CEREBRO" cmd /k "python brain_orchestrator.py"

echo --- SISTEMA EN MARCHA ---
pause