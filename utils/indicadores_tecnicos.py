# utils/indicadores_tecnicos.py
import pandas as pd
import numpy as np # Para np.nan si es necesario

# --- Constantes para periodos por defecto ---
SMA_DEFAULT_PERIODS = [20, 50] # Periodos comunes para SMA
RSI_DEFAULT_PERIOD = 14
MACD_DEFAULT_FAST = 12
MACD_DEFAULT_SLOW = 26
MACD_DEFAULT_SIGNAL = 9
BBANDS_DEFAULT_PERIOD = 20
BBANDS_DEFAULT_STD_DEV = 2

def calcular_sma(series: pd.Series, periodo: int) -> float | None:
    """
    Calcula la Media Móvil Simple (SMA) para un período dado.
    Devuelve el último valor de la SMA.
    """
    if not isinstance(series, pd.Series):
        print("Error en calcular_sma: la entrada 'series' debe ser un pd.Series.")
        return None
    if series.empty or len(series) < periodo:
        return None
    try:
        sma = series.rolling(window=periodo).mean().iloc[-1]
        return float(sma) if pd.notna(sma) else None
    except Exception as e:
        print(f"Error calculando SMA({periodo}): {e}")
        return None

def calcular_rsi(series: pd.Series, periodo: int = RSI_DEFAULT_PERIOD) -> float | None:
    """
    Calcula el Índice de Fuerza Relativa (RSI) para un período dado.
    Devuelve el último valor del RSI.
    """
    if not isinstance(series, pd.Series):
        print("Error en calcular_rsi: la entrada 'series' debe ser un pd.Series.")
        return None
    if series.empty or len(series) < periodo + 1: # RSI necesita al menos periodo+1 puntos para el primer cálculo de delta
        return None
    try:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periodo).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periodo).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        last_rsi = rsi.iloc[-1]
        return float(last_rsi) if pd.notna(last_rsi) else None
    except ZeroDivisionError: # Puede ocurrir si loss es 0 consistentemente
        # Si solo hay ganancias, RSI es 100. Si solo pérdidas, RSI es 0 (aunque la fórmula da NaN/inf).
        # Un manejo más robusto es necesario aquí si esto es frecuente.
        # Por ahora, devolvemos None o un valor extremo si se puede determinar.
        delta = series.diff()
        gain_sum = (delta.where(delta > 0, 0)).sum()
        loss_sum = (-delta.where(delta < 0, 0)).sum()
        if loss_sum == 0 and gain_sum > 0: return 100.0
        if gain_sum == 0 and loss_sum > 0: return 0.0
        return None # O un valor que indique error/situación extrema
    except Exception as e:
        print(f"Error calculando RSI({periodo}): {e}")
        return None

def calcular_macd(series: pd.Series, 
                  periodo_corto: int = MACD_DEFAULT_FAST, 
                  periodo_largo: int = MACD_DEFAULT_SLOW, 
                  periodo_señal: int = MACD_DEFAULT_SIGNAL) -> dict | None:
    """
    Calcula la Convergencia/Divergencia de Medias Móviles (MACD).
    Devuelve un diccionario con 'macd', 'señal', 'histograma' (últimos valores).
    """
    if not isinstance(series, pd.Series):
        print("Error en calcular_macd: la entrada 'series' debe ser un pd.Series.")
        return None
    if series.empty or len(series) < periodo_largo + periodo_señal:
        return None
    try:
        ema_corto = series.ewm(span=periodo_corto, adjust=False).mean()
        ema_largo = series.ewm(span=periodo_largo, adjust=False).mean()
        
        macd_line = ema_corto - ema_largo
        señal_line = macd_line.ewm(span=periodo_señal, adjust=False).mean()
        histograma = macd_line - señal_line
        
        last_macd = macd_line.iloc[-1]
        last_señal = señal_line.iloc[-1]
        last_hist = histograma.iloc[-1]

        return {
            "macd": float(last_macd) if pd.notna(last_macd) else None,
            "señal": float(last_señal) if pd.notna(last_señal) else None,
            "histograma": float(last_hist) if pd.notna(last_hist) else None,
        }
    except Exception as e:
        print(f"Error calculando MACD: {e}")
        return None

def calcular_bandas_bollinger(series: pd.Series, 
                              periodo: int = BBANDS_DEFAULT_PERIOD, 
                              num_std_dev: int = BBANDS_DEFAULT_STD_DEV) -> dict | None:
    """
    Calcula las Bandas de Bollinger.
    Devuelve un diccionario con 'media', 'superior', 'inferior' (últimos valores).
    """
    if not isinstance(series, pd.Series):
        print("Error en calcular_bandas_bollinger: la entrada 'series' debe ser un pd.Series.")
        return None
    if series.empty or len(series) < periodo:
        return None
    try:
        sma = series.rolling(window=periodo).mean()
        std_dev = series.rolling(window=periodo).std()
        
        banda_superior = sma + (std_dev * num_std_dev)
        banda_inferior = sma - (std_dev * num_std_dev)
        
        last_media = sma.iloc[-1]
        last_superior = banda_superior.iloc[-1]
        last_inferior = banda_inferior.iloc[-1]

        return {
            "media": float(last_media) if pd.notna(last_media) else None,
            "superior": float(last_superior) if pd.notna(last_superior) else None,
            "inferior": float(last_inferior) if pd.notna(last_inferior) else None,
        }
    except Exception as e:
        print(f"Error calculando Bandas de Bollinger: {e}")
        return None

# --- Funciones de ayuda para obtener datos históricos (simuladas o de API real) ---
def obtener_datos_historicos_simulados(simbolo_par: str, periodo_tiempo: str, limite: int) -> pd.DataFrame | None:
    """
    Simula la obtención de datos históricos OHLCV.
    En un sistema real, esto se conectaría a una API (Binance, CoinGecko, etc.).
    Devuelve un DataFrame de Pandas con columnas ['timestamp', 'open', 'high', 'low', 'close', 'volume'].
    'timestamp' debe ser un índice de tipo DatetimeIndex.
    """
    print(f"Simulando obtención de datos históricos para {simbolo_par}, periodo {periodo_tiempo}, limite {limite}")
    end_date = pd.Timestamp.now(tz='UTC')
    if periodo_tiempo == '1d':
        start_date = end_date - pd.Timedelta(days=limite -1)
        dates = pd.date_range(start=start_date, end=end_date, freq='D', tz='UTC')
    elif periodo_tiempo == '1h':
        start_date = end_date - pd.Timedelta(hours=limite -1)
        dates = pd.date_range(start=start_date, end=end_date, freq='H', tz='UTC')
    else:
        start_date = end_date - pd.Timedelta(days=limite-1)
        dates = pd.date_range(start=start_date, end=end_date, freq='D', tz='UTC')

    if len(dates) == 0: return None

    data = {
        'open': np.random.uniform(low=2.5, high=4.5, size=len(dates)),
        'high': np.random.uniform(low=2.6, high=4.8, size=len(dates)), # Asegurar high >= open
        'low': np.random.uniform(low=2.2, high=4.3, size=len(dates)),   # Asegurar low <= open
        'close': np.random.uniform(low=2.4, high=4.6, size=len(dates)),
        'volume': np.random.uniform(low=100000, high=5000000, size=len(dates))
    }
    df = pd.DataFrame(data, index=pd.DatetimeIndex(dates, name="timestamp"))
    
    # Asegurar que high sea el más alto y low el más bajo del día
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
    
    # Simular alguna tendencia para que los indicadores no sean totalmente aleatorios
    trend_factor = np.linspace(0.9, 1.1, len(df)) # Ligera tendencia alcista
    noise = np.random.normal(0, 0.1, len(df)) # Ruido
    base_price = 3.5
    
    df['open'] = base_price * trend_factor * (1 + noise * 0.2)
    df['close'] = df['open'] * (1 + np.random.normal(0, 0.02, len(df))) # Cierre cerca de apertura
    df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.random.uniform(0, 0.03, len(df)))
    df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.random.uniform(0, 0.03, len(df)))
    
    # Re-asegurar consistencia OHLC
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
    df.loc[df['open'] > df['high'], 'open'] = df['high']
    df.loc[df['open'] < df['low'], 'open'] = df['low']
    df.loc[df['close'] > df['high'], 'close'] = df['high']
    df.loc[df['close'] < df['low'], 'close'] = df['low']

    return df.sort_index()


# Bloque de prueba
if __name__ == '__main__':
    print("Probando funciones de indicadores técnicos...")

    # Crear datos de ejemplo (más realistas que aleatorios puros)
    np.random.seed(42)
    fechas_ejemplo = pd.date_range(start='2024-01-01', periods=100, freq='D')
    datos_cierre_ejemplo = pd.Series(
        np.random.normal(loc=50, scale=5, size=100).cumsum() + 100, # Simula un precio con tendencia
        index=fechas_ejemplo
    )
    datos_cierre_ejemplo.iloc[0] = 100 # Asegurar un punto de partida

    # Asegurar que no haya NaNs en la serie de cierre de prueba
    if datos_cierre_ejemplo.isnull().any():
        print("Advertencia: La serie de cierre de prueba contiene NaNs. Rellenando...")
        datos_cierre_ejemplo = datos_cierre_ejemplo.fillna(method='ffill').fillna(method='bfill')


    print(f"\nÚltimos 5 precios de cierre de ejemplo:\n{datos_cierre_ejemplo.tail()}")

    # SMA
    sma_20 = calcular_sma(datos_cierre_ejemplo, 20)
    sma_50 = calcular_sma(datos_cierre_ejemplo, 50)
    print(f"\nSMA(20): {sma_20:.2f}" if sma_20 is not None else "SMA(20): N/A")
    print(f"SMA(50): {sma_50:.2f}" if sma_50 is not None else "SMA(50): N/A")

    # RSI
    rsi_14 = calcular_rsi(datos_cierre_ejemplo, 14)
    print(f"\nRSI(14): {rsi_14:.2f}" if rsi_14 is not None else "RSI(14): N/A")

    # MACD
    macd_data = calcular_macd(datos_cierre_ejemplo)
    if macd_data:
        print(f"\nMACD: Línea={macd_data['macd']:.2f}, Señal={macd_data['señal']:.2f}, Histograma={macd_data['histograma']:.2f}")
    else:
        print("\nMACD: N/A")

    # Bandas de Bollinger
    bb_data = calcular_bandas_bollinger(datos_cierre_ejemplo)
    if bb_data:
        print(f"\nBandas de Bollinger: Media={bb_data['media']:.2f}, Superior={bb_data['superior']:.2f}, Inferior={bb_data['inferior']:.2f}")
    else:
        print("\nBandas de Bollinger: N/A")
        
    print("\n--- Prueba con datos insuficientes ---")
    datos_cortos = datos_cierre_ejemplo.tail(10)
    sma_corto = calcular_sma(datos_cortos, 20) # Debería ser None
    print(f"SMA(20) con 10 datos: {sma_corto}")
    rsi_corto = calcular_rsi(datos_cortos, 14) # Debería ser None
    print(f"RSI(14) con 10 datos: {rsi_corto}")


    print("\n--- Prueba de obtención de datos históricos simulados ---")
    datos_ohlcv = obtener_datos_historicos_simulados("WLD/USDT", "1d", 60)
    if datos_ohlcv is not None:
        print(f"Datos OHLCV obtenidos para WLD/USDT (últimos 5 días):\n{datos_ohlcv.tail()}")
        # Probar un indicador con estos datos
        if not datos_ohlcv['close'].empty:
            sma20_ohlcv = calcular_sma(datos_ohlcv['close'], 20)
            print(f"SMA(20) de datos OHLCV simulados: {sma20_ohlcv}")
        else:
            print("Columna 'close' vacía en datos OHLCV simulados.")
    else:
        print("No se pudieron obtener datos OHLCV simulados.")

    print("\nPruebas de indicadores completadas.")
