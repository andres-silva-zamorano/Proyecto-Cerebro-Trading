import MetaTrader5 as mt5
import redis
import json
import time
import sys
import os

# Asegurar importación de configuración global desde la raíz del proyecto
sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_DECISION, CH_RESULTS

class MT5GatewayAlpha:
    def __init__(self, symbol="BTCUSD", magic_number=123456, lot_size=0.01):
        """
        Brazo Ejecutor Alpha v3.8.4.
        Misión: Traducción de señales neuronales en operaciones físicas en MT5.
        Corregido: Constantes de Filling Mode y blindaje contra respuestas nulas.
        """
        self.symbol = symbol
        self.magic = int(magic_number)
        self.lot = lot_size
        
        try:
            # Conexión a la Médula Espinal (Redis)
            self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
            print(f"✅ Gateway Alpha v3.8.4 conectado a Redis")
        except Exception as e:
            print(f"❌ Error de conexión Redis en Gateway: {e}")
            sys.exit(1)

        # Inicialización del terminal MetaTrader 5
        if not mt5.initialize():
            print(f"❌ Error al inicializar MT5: {mt5.last_error()}")
            sys.exit(1)

        self.verificar_cuenta()

    def verificar_cuenta(self):
        """Protocolo de seguridad: Vision Global opera solo en Demo para esta fase."""
        account_info = mt5.account_info()
        if account_info is None:
            print("❌ No se pudo obtener información de la cuenta.")
            mt5.shutdown()
            sys.exit(1)
            
        if account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_REAL:
            print("⚠️ SEGURIDAD: Operación en cuenta REAL detectada. Abortando por seguridad.")
            mt5.shutdown()
            sys.exit(1)
            
        print(f"🚀 Gateway BTC Activo | Pepperstone: {account_info.login} | Magic ID: {self.magic}")

    def obtener_filling_mode(self):
        """
        Detecta dinámicamente el modo de ejecución permitido por el broker.
        Resuelve el error de constantes SYMBOL_FILLING_FOK.
        """
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            return mt5.ORDER_FILLING_IOC
        
        # El filling_mode de symbol_info es un bitmask
        # 1 = FOK (Fill or Kill), 2 = IOC (Immediate or Cancel)
        filling_attr = symbol_info.filling_mode
        
        if filling_attr == 1:
            return mt5.ORDER_FILLING_FOK
        elif filling_attr == 2:
            return mt5.ORDER_FILLING_IOC
        else:
            return mt5.ORDER_FILLING_IOC # Fallback estándar para la mayoría de brokers ECN

    def cerrar_todo_real(self, reason="N/A"):
        """
        Liquida físicamente todas las posiciones del bot con sistema de reintentos.
        Blindado contra errores de tipo None en la respuesta del terminal.
        """
        print(f"📡 Iniciando Liquidación Física: {reason}")
        positions = mt5.positions_get(symbol=self.symbol, magic=self.magic)
        
        if not positions:
            print(f"ℹ️ No hay posiciones abiertas con Magic {self.magic}.")
            self.r.publish(CH_RESULTS, json.dumps({"status": "closed", "final_pnl": 0.0, "razon": "SIN_POSICIONES"}))
            return

        filling = self.obtener_filling_mode()
        posiciones_cerradas_con_exito = 0
        pnl_final_acumulado = 0.0

        for p in positions:
            # Sistema de 3 reintentos por ticket para garantizar el cierre
            for intento in range(3):
                tick = mt5.symbol_info_tick(self.symbol)
                if tick is None:
                    time.sleep(0.1)
                    continue

                tipo_cierre = mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
                precio_cierre = tick.bid if p.type == mt5.ORDER_TYPE_BUY else tick.ask
                
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": self.symbol,
                    "position": p.ticket,
                    "volume": p.volume,
                    "type": tipo_cierre,
                    "price": precio_cierre,
                    "deviation": 20,
                    "magic": self.magic,
                    "comment": f"Alpha v3.8.4 Close",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": filling,
                }
                
                res = mt5.order_send(request)
                
                # --- BLINDAJE CONTRA NoneType ---
                if res is None:
                    print(f"❌ ERROR: MT5 devolvió None en ticket #{p.ticket}. Intento {intento+1}/3")
                    time.sleep(0.2)
                    continue
                    
                if res.retcode == mt5.TRADE_RETCODE_DONE:
                    pnl_final_acumulado += p.profit
                    posiciones_cerradas_con_exito += 1
                    print(f"🛑 MT5 CERRADO: Ticket #{p.ticket} ejecutado con éxito.")
                    break
                else:
                    print(f"⚠️ Fallo intento {intento+1} para #{p.ticket}: {res.comment}")
                    time.sleep(0.1)

        # Solo informamos el cierre exitoso si logramos cerrar posiciones
        if posiciones_cerradas_con_exito > 0:
            self.r.publish(CH_RESULTS, json.dumps({
                "status": "closed",
                "final_pnl": round(pnl_final_acumulado, 2),
                "razon": reason,
                "timestamp": time.time()
            }))
        else:
            print("❌ FALLO TOTAL DE CIERRE: Las posiciones siguen abiertas en MT5.")
            self.r.publish(CH_RESULTS, json.dumps({"status": "error_cierre", "razon": "FALLO_MT5"}))

    def ejecutar_orden_mercado(self, accion, consenso):
        """
        Ejecuta una apertura de posición inmediata.
        """
        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None:
            print("❌ Error: No se pudo obtener el tick para abrir posición.")
            return

        order_type = mt5.ORDER_TYPE_BUY if accion == "BUY" else mt5.ORDER_TYPE_SELL
        price = tick.ask if accion == "BUY" else tick.bid
        filling = self.obtener_filling_mode()
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": self.lot,
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": self.magic,
            "comment": f"Alpha Conf:{consenso}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling,
        }

        result = mt5.order_send(request)
        
        if result is None:
            print(f"❌ ERROR CRÍTICO: order_send (Open) devolvió None.")
            return

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✅ MT5 OPEN: {accion} @ {result.price} (Ticket: #{result.order})")
            # Notificamos a Homeostasis para que registre la orden en su cúmulo
            self.r.publish(CH_RESULTS, json.dumps({
                "ticket": result.order,
                "action": accion,
                "price": result.price,
                "volume": self.lot,
                "status": "executed",
                "timestamp": time.time()
            }))
        else:
            print(f"❌ FALLO APERTURA MT5: {result.comment} (Código: {result.retcode})")

    def escuchar(self):
        """Escucha permanente de órdenes provenientes del Ejecutor o Homeostasis."""
        pubsub = self.r.pubsub()
        pubsub.subscribe(CH_DECISION)
        print(f"🎧 Gateway v3.8.4 escuchando órdenes de ejecución en BTCUSD...")
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                accion = data.get('action')
                
                if accion == "CLOSE_ALL":
                    self.cerrar_todo_real(data.get('reason', 'Brain Trigger'))
                elif accion in ["BUY", "SELL"]:
                    self.ejecutar_orden_mercado(accion, data.get('consenso', 0.0))

if __name__ == "__main__":
    gateway = MT5GatewayAlpha()
    try:
        gateway.escuchar()
    except KeyboardInterrupt:
        print("\n🛑 Apagando Gateway por interrupción del usuario.")
    finally:
        mt5.shutdown()