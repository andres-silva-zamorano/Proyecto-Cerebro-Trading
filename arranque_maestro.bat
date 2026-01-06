@echo off
title ORQUESTADOR CEREBRO ALPHA - DEMOCRACIA HFT
color 0B
echo ============================================================
echo      SISTEMA DE INTELIGENCIA COLECTIVA ALPHA V3
echo ============================================================

echo [1/4] Iniciando Medula Espinal (Redis)...
:: Lanzamos Redis en segundo plano (minimizando la ventana)
start "REDIS SERVER" /min redis-server

:: Esperamos 3 segundos a que el servidor levante
timeout /t 3 /nobreak > nul

echo [2/4] Ejecutando Limpieza de Memoria (Reset Total)...
:: Borramos todos los datos de Redis (PnL negativo, bloqueos, ordenes viejas)
echo    -^> Limpiando base de datos Redis...
redis-cli flushall

:: Borramos la Matriz de Reputación para que los expertos empiecen con peso 1.0
if exist "modelos\matriz_reputacion.json" (
    echo    -^> Borrando Matriz de Reputacion vieja...
    del /f /q "modelos\matriz_reputacion.json"
) else (
    echo    -^> No se encontro matriz previa. Nada que borrar.
)

echo ✅ Memoria limpia. Iniciando desde cero.
echo.

timeout /t 2 /nobreak > nul

echo [3/4] Lanzando Monitor de Democracia...
:: Lanzamos el monitor en una ventana separada
start "MONITOR_VISUAL" cmd /k "python brain_monitor.py"

timeout /t 2 /nobreak > nul

echo [4/4] Activando Organismo (Orquestador)...
:: El orquestador lanza los expertos y el feeder. 
:: Usamos -u para que el log sea en tiempo real (unbuffered)
start "CEREBRO_LOGICA" cmd /k "python -u brain_orchestrator.py"

echo.
echo ============================================================
echo ✅ SISTEMA EN MARCHA - Pizarra limpia y lista para ganar
echo ============================================================
echo Puedes cerrar esta ventana si lo deseas, los procesos siguen en las otras.
pause