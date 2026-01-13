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
    def __init__(self, symbol="BTCUSD"):
        """
        Sensor v3.7: Proporciona flujos síncronos para M1 y M15.
        Garantiza que el Tálamo Fractal reciba datos en la resolución correcta.
        """
        self.symbol = symbol
        try:
            self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
            print(f"✅ Feeder v3.7 conectado a Redis")
        except Exception as e:
            print(f"❌ Error Redis: {e}"); sys.exit(1)

        if not mt5.initialize():
            print(f"❌ Error al inicializar MT5: {mt5.last_error()}"); sys.exit(1)
            
        print(f"⚡ Sensor Alpha BTC Activo | Sincronizando M1 y M15...")

    def obtener_datos(self, timeframe, n=400):
        rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, n)
        if rates is None or len(rates) == 0: return None
        return pl.DataFrame(rates)

    def calcular_indicadores(self, df: pl.DataFrame):
        """
        Calcula la matriz de 19 indicadores. 
        Se usa la misma lógica para ambos timeframes para mantener la coherencia.
        """
        # 1-6. Estructura de EMAs
        for s in [10, 20, 40, 80, 160, 320]:
            df = df.with_columns([pl.col("close").ewm_mean(span=s).alias(f"EMA_{s}")])

        # 7-8. EMA Principal y Pendiente
        df = df.with_columns([pl.col("close").ewm_mean(span=20).alias("EMA_Princ")])
        df = df.with_columns([(pl.col("EMA_Princ") - pl.col("EMA_Princ").shift(1)).alias("EMA_Princ_Slope")])

        # 9-10. RSI y Velocidad
        delta = pl.col("close").diff()
        gain = pl.when(delta > 0).then(delta).otherwise(0).ewm_mean(span=14)
        loss = pl.when(delta < 0).then(-delta).otherwise(0).ewm_mean(span=14)
        df = df.with_columns([(100 - (100 / (1 + (gain / (loss + 1e-9))))).alias("RSI_Val")])
        df = df.with_columns([(pl.col("RSI_Val") - pl.col("RSI_Val").shift(1)).alias("RSI_Velocidad")])

        # 11. MACD
        df = df.with_columns([(pl.col("close").ewm_mean(span=12) - pl.col("close").ewm_mean(span=26)).alias("MACD_Val")])

        # 12-15. ADX / DMI / ATR
        n_adx = 14
        tr = pl.max_horizontal(pl.col("high")-pl.col("low"), (pl.col("high")-pl.col("close").shift(1)).abs(), (pl.col("low")-pl.col("close").shift(1)).abs())
        atr = tr.ewm_mean(span=n_adx)
        
        diff_h = pl.col("high") - pl.col("high").shift(1)
        diff_l = pl.col("low").shift(1) - pl.col("low")
        p_dm = pl.when((diff_h > diff_l) & (diff_h > 0)).then(diff_h).otherwise(0).ewm_mean(span=n_adx)
        m_dm = pl.when((diff_l > diff_h) & (diff_l > 0)).then(diff_l).otherwise(0).ewm_mean(span=n_adx)
        
        p_di = 100 * (p_dm / (atr + 1e-9))
        m_di = 100 * (m_dm / (atr + 1e-9))
        dx = 100 * (p_di - m_di).abs() / (p_di + m_di + 1e-9)
        adx_val = dx.ewm_mean(span=n_adx)

        df = df.with_columns([
            p_di.alias("DI_Plus"), m_di.alias("DI_Minus"), adx_val.alias("ADX_Val"),
            (adx_val - adx_val.shift(1)).alias("ADX_Diff"),
            atr.alias("ATR_Act"), (atr / pl.col("close")).alias("ATR_Rel")
        ])

        # 18. Volumen Relativo
        df = df.with_columns([(pl.col("tick_volume") / pl.col("tick_volume").rolling_mean(window_size=20)).alias("Volumen_Relativo")])

        return df

    def stream(self):
        print(f"📡 Transmitiendo 19 señales fractales a la Médula Espinal...")
        ultima_vela_m1 = None
        
        while True:
            # 1. FLUJO HTF (M15)
            df_m15 = self.obtener_datos(mt5.TIMEFRAME_M15, 400)
            if df_m15 is not None:
                df_m15 = self.calcular_indicadores(df_m15)
                row_htf = df_m15.tail(1).to_dicts()[0]
                row_htf["Close_Price"] = row_htf.pop("close")
                # Publicamos en un canal específico para HTF
                self.r.set("htf_context_data", json.dumps(row_htf))

            # 2. FLUJO OPERATIVO (M1)
            df_m1 = self.obtener_datos(mt5.TIMEFRAME_M1, 400)
            if df_m1 is not None:
                df_m1 = self.calcular_indicadores(df_m1)
                last_m1 = df_m1.tail(1).to_dicts()[0]
                ts = datetime.fromtimestamp(int(last_m1['time']), tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                
                if ts != ultima_vela_m1:
                    data = {k: (float(v) if isinstance(v, (float, int)) else str(v)) for k, v in last_m1.items()}
                    data["Close_Price"] = data.pop("close")
                    data["Timestamp"] = ts
                    self.r.publish(CH_MARKET_DATA, json.dumps(data))
                    ultima_vela_m1 = ts
            
            time.sleep(0.5)

if __name__ == "__main__":
    MT5FeederAlpha().stream()