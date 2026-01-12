import MetaTrader5 as mt5
import polars as pl
import redis
import json
import time
import sys
import os
import numpy as np
from datetime import datetime, timezone

# Configuración de rutas para importes locales
sys.path.append(os.getcwd())
from config import REDIS_HOST, REDIS_PORT, CH_MARKET_DATA

class MT5FeederPolars:
    def __init__(self, symbol="BTCUSD", timeframe=mt5.TIMEFRAME_M1):
        """
        Sensor de mercado optimizado para BTCUSD.
        """
        self.symbol = symbol
        self.timeframe = timeframe
        
        try:
            self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
            print(f"✅ Feeder (Polars) conectado a Redis")
        except Exception as e:
            print(f"❌ Error Redis: {e}")
            sys.exit(1)

        if not mt5.initialize():
            print(f"❌ Error al inicializar MT5: {mt5.last_error()}")
            sys.exit(1)
            
        # Asegurarse de que BTCUSD sea visible en el Market Watch
        if not mt5.symbol_select(self.symbol, True):
            print(f"❌ Error: El símbolo {self.symbol} no está disponible en este Broker.")
            sys.exit(1)
            
        print(f"⚡ Sensor Alpha BTC Activo | Simbolo: {self.symbol}")

    def obtener_datos(self, n=600):
        rates = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, n)
        if rates is None or len(rates) == 0:
            return None
        return pl.DataFrame(rates)

    def calcular_indicadores(self, df: pl.DataFrame):
        # 1. EMAs
        df = df.with_columns([
            pl.col("close").ewm_mean(span=s).alias(f"EMA_{s}") 
            for s in [10, 20, 40, 80, 160, 320]
        ])

        # 2. RSI (Wilder)
        delta = pl.col("close").diff()
        gain = pl.when(delta > 0).then(delta).otherwise(0)
        loss = pl.when(delta < 0).then(-delta).otherwise(0)
        rs = gain.ewm_mean(span=27, adjust=False) / (loss.ewm_mean(span=27, adjust=False) + 1e-9)
        df = df.with_columns([(100 - (100 / (1 + rs))).alias("RSI_Val")])

        # 3. MACD
        df = df.with_columns([
            (pl.col("close").ewm_mean(span=12) - pl.col("close").ewm_mean(span=26)).alias("MACD_Val")
        ])

        # 4. ADX / DMI
        n_adx = 14
        w_span = 2 * n_adx - 1
        tr = pl.max_horizontal(
            pl.col("high") - pl.col("low"),
            (pl.col("high") - pl.col("close").shift(1)).abs(),
            (pl.col("low") - pl.col("close").shift(1)).abs()
        )
        diff_h = pl.col("high") - pl.col("high").shift(1)
        diff_l = pl.col("low").shift(1) - pl.col("low")
        p_dm = pl.when((diff_h > diff_l) & (diff_h > 0)).then(diff_h).otherwise(0)
        m_dm = pl.when((diff_l > diff_h) & (diff_l > 0)).then(diff_l).otherwise(0)
        atr = tr.ewm_mean(span=w_span, adjust=False)
        p_di = 100 * (p_dm.ewm_mean(span=w_span, adjust=False) / (atr + 1e-9))
        m_di = 100 * (m_dm.ewm_mean(span=w_span, adjust=False) / (atr + 1e-9))
        dx = 100 * (p_di - m_di).abs() / (p_di + m_di + 1e-9)
        
        df = df.with_columns([
            p_di.alias("DI_Plus"),
            m_di.alias("DI_Minus"),
            dx.ewm_mean(span=w_span, adjust=False).alias("ADX_Val"),
            (atr / pl.col("close")).alias("ATR_Rel")
        ])
        return df

    def stream(self):
        ultima_vela = None
        print(f"📡 Stream BTCUSD M1 (Broker Server Time)...")
        
        try:
            while True:
                df = self.obtener_datos()
                if df is not None:
                    df = self.calcular_indicadores(df)
                    last_row = df.tail(1).to_dicts()[0]
                    unix_ts = int(last_row.get('time', 0))
                    ts_legible = datetime.fromtimestamp(unix_ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                    
                    if ts_legible != ultima_vela:
                        data = {k: (float(v) if isinstance(v, (float, int, np.float32, np.float64)) else str(v)) 
                                for k, v in last_row.items()}
                        data["Close_Price"] = data.pop("close")
                        data["Timestamp"] = ts_legible
                        
                        self.r.publish(CH_MARKET_DATA, json.dumps(data))
                        print(f"📤 [BTC-SENSOR] {ts_legible} | P: {data['Close_Price']:.2f} | ADX: {data['ADX_Val']:.2f}", flush=True)
                        ultima_vela = ts_legible
                        
                time.sleep(0.5) 
        except Exception as e:
            print(f"❌ Error en Feeder BTC: {e}")
        finally:
            mt5.shutdown()

if __name__ == "__main__":
    MT5FeederPolars(symbol="BTCUSD").stream()