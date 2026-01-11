import MetaTrader5 as mt5
import redis
import json
import time
import sys
import os

# Asegurar que reconozca la raíz para importar la configuración
sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_DECISION, CH_RESULTS

class MT5Gateway:
    def __init__(self, symbol="EURUSD", magic_number=123456, lot_size=0.1):
        """
        Inicializa el brazo ejecutor del Cerebro Alpha.
        """
        self.symbol = symbol
        self.magic = magic_number
        self.lot = lot_size
        
        # 1. Conexión a Redis
        try:
            self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
            print(f"✅ Gateway conectado a Redis en {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            print(f"❌ Error conectando a Redis: {e}")
            sys.exit(1)

        # 2. Inicializar MetaTrader 5
        if not mt5.initialize():
            print(f"❌ Error al inicializar MT5: {mt5.last_error()}")
            sys.exit(1)

        self.verificar_cuenta()

    def verificar_cuenta(self):
        """Verifica que estemos en una cuenta Demo y que el trading esté permitido."""
        account_info = mt5.account_info()
        if account_info is None:
            print("❌ No se pudo obtener información de la cuenta. ¿Está abierto MT5?")
            mt5.shutdown()
            sys.exit(1)
        
        if account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_REAL:
            print("⚠️ ADVERTENCIA: ¡ESTÁS EN UNA CUENTA REAL! El Gateway se cerrará por seguridad.")
            mt5.shutdown()
            sys.exit(1)
            
        print(f"🚀 Gateway MT5 Activo | Cuenta: {account_info.login} | Broker: {account_info.company}")
        print(f"📊 Símbolo: {self.symbol} | Lotes: {self.lot} | Magic: {self.magic}")

    def ejecutar_orden(self, accion_cerebro, consenso):
        """Traduce la decisión del cerebro en una solicitud de trading real."""
        symbol_info = mt5.symbol_info(self.symbol)
        if not symbol_info:
            print(f"❌ {self.symbol} no encontrado.")
            return

        if not symbol_info.visible:
            mt5.symbol_select(self.symbol, True)

        # Determinar tipo de orden y precio
        order_type = mt5.ORDER_TYPE_BUY if accion_cerebro == "BUY" else mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(self.symbol).ask if accion_cerebro == "BUY" else mt5.symbol_info_tick(self.symbol).bid
        
        # Estructura de la petición MT5
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": self.lot,
            "type": order_type,
            "price": price,
            "deviation": 10, # Slippage máximo permitido en puntos
            "magic": self.magic,
            "comment": f"Alpha v3.0 | Consenso: {consenso}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC, # Immediate or Cancel para HFT
        }

        # Enviar a mercado
        print(f"📡 Enviando {accion_cerebro} a MT5... (Precio: {price})")
        result = mt5.order_send(request)

        # Analizar respuesta del Broker
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ ERROR EN EJECUCIÓN: Código {result.retcode} | {self.get_error_desc(result.retcode)}")
        else:
            print(f"✅ ORDEN EJECUTADA: Ticket #{result.order} | Precio: {result.price}")
            
            # Notificar al sistema de reputación (n_ejecutor / n_homeostasis)
            reporte = {
                "ticket": result.order,
                "action": accion_cerebro,
                "price": result.price,
                "consenso": consenso,
                "status": "executed",
                "timestamp": time.time()
            }
            self.r.publish(CH_RESULTS, json.dumps(reporte))

    def get_error_desc(self, code):
        """Mapeo de errores comunes de MT5."""
        errors = {
            10004: "Requote (Precio cambiado)",
            10006: "Orden rechazada",
            10013: "Invalid Request",
            10018: "Market Closed",
            10019: "No money (Margen insuficiente)",
            10021: "No prices (Falta de liquidez)"
        }
        return errors.get(code, "Error desconocido")

    def escuchar_decisiones(self):
        """Bucle principal de escucha de Redis."""
        pubsub = self.r.pubsub()
        pubsub.subscribe(CH_DECISION)
        
        print(f"🎧 Gateway escuchando decisiones en el canal: {CH_DECISION}...")
        
        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    data = json.loads(message['data'])
                    
                    # Validar parámetros de Optuna antes de tocar MT5
                    # Umbral de disparo: 0.75
                    if abs(data.get('consenso', 0)) >= 0.75:
                        self.ejecutar_orden(data['action'], data['consenso'])
                    else:
                        print(f"⚠️ Orden ignorada: Consenso insuficiente ({data.get('consenso')})")
                        
        except KeyboardInterrupt:
            print("🛑 Apagando Gateway...")
        finally:
            mt5.shutdown()

if __name__ == "__main__":
    # Configuración por defecto. Puedes inyectar el símbolo por argumentos si deseas.
    gateway = MT5Gateway(symbol="EURUSD", lot_size=0.1)
    gateway.escuchar_decisiones()