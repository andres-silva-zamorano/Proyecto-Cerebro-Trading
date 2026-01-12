import MetaTrader5 as mt5
import polars as pl
import redis
import json
import time
import sys
import os
import numpy as np
from datetime import datetime, timezone

# Asegurar que reconozca la raíz para importar la configuración global
sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA

class MT5FeederAlpha:
    def __init__(self, symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M1):
        """
        Sensor de alta fidelidad para Bitcoin. 
        Genera los 19 indicadores requeridos por el Tálamo H5 y la Corteza Visual.
        """
        self.symbol = symbol
        self.timeframe = timeframe
        
        try:
            # Conexión a la Médula Espinal
            self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
            print(f"✅ Feeder conectado a Redis")
        except Exception as e:
            print(f"❌ Error Redis: {e}")
            sys.exit(1)

        # Inicialización de la API de MetaTrader 5
        if not mt5.initialize():
            print(f"❌ Error al inicializar MT5: {mt5.last_error()}")
            sys.exit(1)
            
        if not mt5.symbol_select(self.symbol, True):
            print(f"❌ Error: El símbolo {self.symbol} no está disponible en este Broker.")
            sys.exit(1)
            
        print(f"⚡ Sensor Alpha BTC Activo | Sincronizando 19 Dimensiones...")

    def obtener_datos(self, n=800):
        """Solicita suficientes velas para estabilizar indicadores de largo plazo (EMA 320)."""
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, n)
        if rates is None or len(rates) == 0:
            return None
        return pl.DataFrame(rates)

    def calcular_indicadores(self, df: pl.DataFrame):
        """
        Calcula la matriz exacta de 19 indicadores definida en el entrenamiento.
        """
        # 1-6. Estructura de EMAs (10, 20, 40, 80, 160, 320)
        for s in [10, 20, 40, 80, 160, 320]:
            df = df.with_columns([pl.col("close").ewm_mean(span=s).alias(f"EMA_{s}")])

        # 7-8. EMA Principal y su Pendiente (EMA_Princ_Slope)
        df = df.with_columns([pl.col("close").ewm_mean(span=20).alias("EMA_Princ")])
        df = df.with_columns([(pl.col("EMA_Princ") - pl.col("EMA_Princ").shift(1)).alias("EMA_Princ_Slope")])

        # 9-10. RSI y su Velocidad de Cambio (RSI_Velocidad)
        delta = pl.col("close").diff()
        gain = pl.when(delta > 0).then(delta).otherwise(0)
        loss = pl.when(delta < 0).then(-delta).otherwise(0)
        avg_gain = gain.ewm_mean(span=14, adjust=False)
        avg_loss = loss.ewm_mean(span=14, adjust=False)
        rs = avg_gain / (avg_loss + 1e-9)
        df = df.with_columns([(100 - (100 / (1 + rs))).alias("RSI_Val")])
        df = df.with_columns([(pl.col("RSI_Val") - pl.col("RSI_Val").shift(1)).alias("RSI_Velocidad")])

        # 11. MACD (Diferencia de EMAs estándar)
        df = df.with_columns([(pl.col("close").ewm_mean(span=12) - pl.col("close").ewm_mean(span=26)).alias("MACD_Val")])

        # 12-15. ADX / DMI y su Diferencial (ADX_Diff para Aceleración)
        n_adx = 14
        tr = pl.max_horizontal(
            pl.col("high") - pl.col("low"),
            (pl.col("high") - pl.col("close").shift(1)).abs(),
            (pl.col("low") - pl.col("close").shift(1)).abs()
        )
        atr_act = tr.ewm_mean(span=n_adx, adjust=False)
        
        diff_h = pl.col("high") - pl.col("high").shift(1)
        diff_l = pl.col("low").shift(1) - pl.col("low")
        p_dm = pl.when((diff_h > diff_l) & (diff_h > 0)).then(diff_h).otherwise(0)
        m_dm = pl.when((diff_l > diff_h) & (diff_l > 0)).then(diff_l).otherwise(0)
        
        p_di = 100 * (p_dm.ewm_mean(span=n_adx, adjust=False) / (atr_act + 1e-9))
        m_di = 100 * (m_dm.ewm_mean(span=n_adx, adjust=False) / (atr_act + 1e-9))
        dx = 100 * (p_di - m_di).abs() / (p_di + m_di + 1e-9)
        adx_val = dx.ewm_mean(span=n_adx, adjust=False)

        df = df.with_columns([
            p_di.alias("DI_Plus"),
            m_di.alias("DI_Minus"),
            adx_val.alias("ADX_Val"),
            (adx_val - adx_val.shift(1)).alias("ADX_Diff"),
            atr_act.alias("ATR_Act"),
            (atr_act / pl.col("close")).alias("ATR_Rel") # 16-17: ATR Absoluto y Relativo
        ])

        # 18. Volumen Relativo (Tick Volume actual vs Promedio de 20 periodos)
        df = df.with_columns([
            (pl.col("tick_volume") / pl.col("tick_volume").rolling_mean(window_size=20)).alias("Volumen_Relativo")
        ])

        # El índice 19 es el Close_Price, que se extrae en el bucle principal.
        return df

    def stream(self):
        """Bucle de transmisión síncrona de datos procesados."""
        ultima_vela = None
        print(f"📡 Transmitiendo 19 señales a la Médula Espinal...")
        
        try:
            while True:
                df = self.obtener_datos()
                if df is not None:
                    df = self.calcular_indicadores(df)
                    # Tomamos la última fila calculada
                    last_row = df.tail(1).to_dicts()[0]
                    unix_ts = int(last_row.get('time', 0))
                    # Timestamp legible en UTC
                    ts_legible = datetime.fromtimestamp(unix_ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    
                    if ts_legible != ultima_vela:
                        # Estructuración final para Redis
                        data = {k: (float(v) if isinstance(v, (float, int, np.float32, np.float64)) else str(v)) 
                                for k, v in last_row.items()}
                        
                        # 19. Close Price (Estandarización de nombre de columna)
                        data["Close_Price"] = data.pop("close")
                        data["Timestamp"] = ts_legible
                        
                        # Publicación en el canal de flujo sensorial
                        self.r.publish(CH_MARKET_DATA, json.dumps(data))
                        ultima_vela = ts_legible
                        
                # Pausa controlada para no saturar el bus
                time.sleep(0.5) 
        except Exception as e:
            print(f"❌ Error crítico en Feeder Alpha: {e}")
        finally:
            mt5.shutdown()

if __name__ == "__main__":
    # Inicialización del sensor para BTCUSD
    MT5FeederAlpha(symbol="BTCUSD").stream()