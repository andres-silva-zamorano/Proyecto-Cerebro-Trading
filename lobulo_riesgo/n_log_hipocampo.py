import redis
import json
import os
import datetime
import sys

# Asegurar que el path reconozca la raíz para importar la configuración global
sys.path.append(os.getcwd())
from config import *

# Configuración de almacenamiento de la bitácora
LOG_DIR = "bitacora_trading"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def main():
    """
    Lóbulo de Memoria (Hipocampo): Registra cada evento sensorial, neuronal y operativo.
    Optimizado para evitar errores de formato y sincronizado con el Consenso Dual v3.8.
    """
    try:
        # 1. Conexión a la Médula Espinal (Redis)
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        pubsub = r.pubsub()
        
        # Suscripción integral para auditoría completa:
        # CH_BRAIN_STATE: Cambios de régimen y niveles de consenso.
        # CH_DECISION: Intenciones de disparo o liquidación.
        # CH_HOMEOSTASIS: Estado del PnL flotante y órdenes abiertas.
        # CH_RESULTS: Confirmaciones reales de ejecución desde el Gateway.
        pubsub.subscribe(CH_BRAIN_STATE, CH_DECISION, CH_HOMEOSTASIS, CH_RESULTS)
        
        # 2. Preparación del archivo de sesión único
        # Usamos un nombre descriptivo para identificar la versión v3.8
        session_id = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(LOG_DIR, f"bitacora_alpha_v38_{session_id}.csv")
        
        # Encabezados del Dataset para análisis posterior en Vision Global
        headers = "Timestamp_Mercado,Regimen,Evento,Detalle,PnL_Flotante,PnL_Total_Historico\n"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(headers)

        print(f"🧠 Hipocampo ALPHA v3.8 activo. Grabando memoria en: {filename}")
    except Exception as e:
        print(f"❌ Error crítico inicializando Hipocampo: {e}")
        return

    # Estado persistente de corto plazo (caché interna)
    estado_actual = {
        "regime": "0",
        "pnl_f": 0.0,
        "pnl_t": 0.0
    }

    # Bucle infinito de escucha de eventos
    for message in pubsub.listen():
        if message['type'] != 'message':
            continue

        try:
            canal = message['channel'].decode('utf-8')
            data = json.loads(message['data'])
            
            # Timestamp del mercado o del sistema como fallback
            ts_m = data.get("Timestamp", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            evento, detalle = "", ""

            # --- A. LATIDO DE CONTEXTO (Tálamo / Ejecutor) ---
            if canal == CH_BRAIN_STATE:
                estado_actual["regime"] = str(data.get("regime_id", "0"))
                # Registramos si hay un cambio drástico de consenso que merezca auditoría
                consenso = data.get("consenso_actual", 0.0)
                if abs(consenso) > 0.5:
                    evento = "ESTADO_CONSENSO"
                    detalle = f"Fuerza: {consenso:.2f} | Pos: {data.get('posicion_en_vuelo', 'None')}"

            # --- B. CONFIRMACIONES REALES DEL BROKER (Gateway) ---
            elif canal == CH_RESULTS:
                status = data.get('status')
                
                if status == 'closed':
                    evento = "CIERRE_CONFIRMADO"
                    pnl_val = data.get('final_pnl')
                    
                    # PROTECCIÓN CONTRA TYPEERROR:
                    # Validamos si final_pnl es None antes de formatear para evitar caídas del lóbulo.
                    pnl_fomateado = f"{float(pnl_val):.2f}" if pnl_val is not None else "0.00"
                    
                    detalle = f"PnL_Real: ${pnl_fomateado} | Motivo: {data.get('razon', 'Consensus')}"
                
                elif status == 'executed':
                    evento = "APERTURA_CONFIRMADA"
                    # Registramos el ticket real de MT5 para trazabilidad
                    detalle = f"Ticket: {data.get('ticket')} | {data.get('action')} @ {data.get('price')}"

            # --- C. INTENCIONES DE MANDO (Ejecutor / Homeostasis) ---
            elif canal == CH_DECISION:
                accion = data.get('action')
                if accion == "CLOSE_ALL":
                    evento = "ORDEN_LIQUIDACION"
                    detalle = f"Motivo: {data.get('reason', 'Duda IA')}"
                else:
                    evento = "ORDEN_DISPARO"
                    detalle = f"Acción: {accion} | Consenso: {data.get('consenso', 0.0)}"

            # --- D. SALUD FINANCIERA (Homeostasis) ---
            elif canal == CH_HOMEOSTASIS:
                estado_actual["pnl_f"] = data.get("floating_pnl", 0.0)
                estado_actual["pnl_t"] = data.get("daily_pnl", 0.0)
                
                # Snapshot de auditoría si hay posiciones abiertas
                if data.get("open_orders", 0) > 0:
                    evento = "LATIDO_OPERATIVO"
                    detalle = f"Órdenes: {data.get('open_orders')} | Flotante: {estado_actual['pnl_f']}"

            # --- ESCRITURA EN DISCO (Persistencia) ---
            if evento:
                # Usamos comillas para el campo detalle por si contiene comas internas
                linea = (
                    f"{ts_m},"
                    f"{estado_actual['regime']},"
                    f"{evento},"
                    f"\"{detalle}\"," 
                    f"{estado_actual['pnl_f']},"
                    f"{estado_actual['pnl_t']}\n"
                )
                with open(filename, "a", encoding="utf-8") as f:
                    f.write(linea)

        except Exception as e:
            # En caso de error en un mensaje específico, lo ignoramos para mantener la bitácora viva
            # pero notificamos en la terminal de logs para depuración.
            print(f"⚠️ Error procesando mensaje en Hipocampo: {e}")
            continue

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[bold red]🛑 Hipocampo detenido por el usuario.[/bold red]")