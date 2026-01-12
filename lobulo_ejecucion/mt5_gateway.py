import MetaTrader5 as mt5
import redis
import json
import time
import sys
import os

# Asegurar que reconozca la raíz para importar la configuración
sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_DECISION, CH_RESULTS

class MT5GatewayBTC:
    def __init__(self, symbol="BTCUSD", magic_number=123456, lot_size=0.01):
        """
        Ejecutor de órdenes optimizado para Bitcoin (BTCUSD).
        """
        self.symbol = symbol
        self.magic = magic_number
        self.lot = lot_size
        
        # 1. Conexión a la Médula Espinal (Redis)
        try:
            self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
            print(f"✅ Gateway conectado a Redis")
        except Exception as e:
            print(f"❌ Error conectando a Redis: {e}")
            sys.exit(1)

        # 2. Inicializar MetaTrader 5
        if not mt5.initialize():
            print(f"❌ Error al inicializar MT5: {mt5.last_error()}")
            sys.exit(1)

        self.verificar_cuenta()

    def verificar_cuenta(self):
        """Protocolo de seguridad: Solo permite operar en cuentas Demo."""
        account_info = mt5.account_info()
        if account_info is None:
            print("❌ No se pudo obtener información de la cuenta. ¿Está abierto MT5?")
            mt5.shutdown()
            sys.exit(1)
        
        if account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_REAL:
            print("⚠️ SEGURIDAD CRÍTICA: Cuenta REAL detectada. El Gateway se cerrará para proteger fondos.")
            mt5.shutdown()
            sys.exit(1)
            
        print(f"🚀 Gateway BTC Activo | Cuenta: {account_info.login} | Broker: {account_info.company}")
        print(f"📊 Activo: {self.symbol} | Lote Base: {self.lot} | Magic ID: {self.magic}")

    def ejecutar_orden(self, accion, consenso):
        """Envía la solicitud de trading al servidor de MetaTrader."""
        symbol_info = mt5.symbol_info(self.symbol)
        if not symbol_info:
            print(f"❌ Error: {self.symbol} no encontrado en Market Watch.")
            return

        # Obtener precios actuales
        tick = mt5.symbol_info_tick(self.symbol)
        order_type = mt5.ORDER_TYPE_BUY if accion == "BUY" else mt5.ORDER_TYPE_SELL
        price = tick.ask if accion == "BUY" else tick.bid
        
        # Configuración de la petición (BTC requiere más desviación/slippage)
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": self.lot,
            "type": order_type,
            "price": price,
            "deviation": 50, # 50 puntos de tolerancia para Bitcoin
            "magic": self.magic,
            "comment": f"Alpha BTC | Cons: {consenso}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC, # Llenado inmediato o cancelación
        }

        print(f"📡 Enviando {accion} BTCUSD a mercado... (Precio: {price})")
        result = mt5.order_send(request)

        # Procesar respuesta del servidor
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ FALLO EN EJECUCIÓN: {result.retcode} | {result.comment}")
        else:
            print(f"✅ BTC EJECUTADO: Ticket #{result.order} | {accion} @ {result.price}")
            
            # Publicar resultado para Homeostasis e Hipocampo
            reporte = {
                "ticket": result.order,
                "action": accion,
                "price": result.price,
                "consenso": consenso,
                "status": "executed",
                "timestamp": time.time()
            }
            self.r.publish(CH_RESULTS, json.dumps(reporte))

    def escuchar_decisiones(self):
        """Bucle de escucha infinita de decisiones neuronales."""
        pubsub = self.r.pubsub()
        pubsub.subscribe(CH_DECISION)
        
        print(f"🎧 Escuchando canal {CH_DECISION} para operar BTCUSD...")
        
        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    data = json.loads(message['data'])
                    
                    # Validación de seguridad: Umbral de consenso Optuna (0.75)
                    if abs(data.get('consenso', 0)) >= 0.75:
                        self.ejecutar_orden(data['action'], data['consenso'])
                    else:
                        print(f"⚠️ Señal ignorada: Consenso {data.get('consenso')} debajo del umbral.")
                        
        except KeyboardInterrupt:
            print("🛑 Deteniendo Gateway por el usuario.")
        except Exception as e:
            print(f"❌ Error crítico en Gateway: {e}")
        finally:
            mt5.shutdown()

if __name__ == "__main__":
    # Inicialización del Gateway
    # Nota: lot_size 0.01 es el estándar mínimo para BTC en muchos brokers
    gateway = MT5GatewayBTC(symbol="BTCUSD", lot_size=0.01)
    gateway.escuchar_decisiones()