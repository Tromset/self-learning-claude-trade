from __future__ import annotations

import pandas as pd
import numpy as np
import ta


class TechnicalAnalyzer:
    """Computes technical indicators on OHLCV DataFrames."""

    def add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = self._add_trend_indicators(df)
        df = self._add_momentum_indicators(df)
        df = self._add_volatility_indicators(df)
        df = self._add_volume_indicators(df)
        return df

    def _add_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["sma_20"] = ta.trend.sma_indicator(df["close"], window=20)
        df["sma_50"] = ta.trend.sma_indicator(df["close"], window=50)
        df["sma_200"] = ta.trend.sma_indicator(df["close"], window=200)
        df["ema_12"] = ta.trend.ema_indicator(df["close"], window=12)
        df["ema_26"] = ta.trend.ema_indicator(df["close"], window=26)
        macd = ta.trend.MACD(df["close"])
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["macd_diff"] = macd.macd_diff()
        df["adx"] = ta.trend.adx(df["high"], df["low"], df["close"])
        return df

    def _add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["rsi"] = ta.momentum.rsi(df["close"], window=14)
        stoch = ta.momentum.StochasticOscillator(df["high"], df["low"], df["close"])
        df["stoch_k"] = stoch.stoch()
        df["stoch_d"] = stoch.stoch_signal()
        df["cci"] = ta.trend.cci(df["high"], df["low"], df["close"])
        df["williams_r"] = ta.momentum.williams_r(df["high"], df["low"], df["close"])
        return df

    def _add_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        bb = ta.volatility.BollingerBands(df["close"])
        df["bb_upper"] = bb.bollinger_hband()
        df["bb_middle"] = bb.bollinger_mavg()
        df["bb_lower"] = bb.bollinger_lband()
        df["bb_width"] = bb.bollinger_wband()
        df["atr"] = ta.volatility.average_true_range(df["high"], df["low"], df["close"])
        return df

    def _add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["obv"] = ta.volume.on_balance_volume(df["close"], df["volume"])
        df["vwap"] = (df["volume"] * (df["high"] + df["low"] + df["close"]) / 3).cumsum() / df["volume"].cumsum()
        df["mfi"] = ta.volume.money_flow_index(df["high"], df["low"], df["close"], df["volume"])
        return df

    def get_signal_summary(self, df: pd.DataFrame) -> dict:
        latest = df.iloc[-1]
        signals = {
            "trend": self._assess_trend(df),
            "momentum": self._assess_momentum(latest),
            "volatility": self._assess_volatility(latest),
            "volume": self._assess_volume(df),
        }
        bullish = sum(1 for v in signals.values() if v == "bullish")
        bearish = sum(1 for v in signals.values() if v == "bearish")
        signals["overall"] = "bullish" if bullish > bearish else ("bearish" if bearish > bullish else "neutral")
        return signals

    def _assess_trend(self, df: pd.DataFrame) -> str:
        latest = df.iloc[-1]
        price = latest["close"]
        if price > latest.get("sma_20", price) and price > latest.get("sma_50", price):
            return "bullish"
        if price < latest.get("sma_20", price) and price < latest.get("sma_50", price):
            return "bearish"
        return "neutral"

    def _assess_momentum(self, row: pd.Series) -> str:
        rsi = row.get("rsi", 50)
        if rsi > 60:
            return "bullish"
        if rsi < 40:
            return "bearish"
        return "neutral"

    def _assess_volatility(self, row: pd.Series) -> str:
        bb_width = row.get("bb_width", 0)
        if bb_width > 0.1:
            return "bearish"  # high volatility is risky
        return "bullish"

    def _assess_volume(self, df: pd.DataFrame) -> str:
        avg_vol = df["volume"].rolling(20).mean().iloc[-1]
        latest_vol = df["volume"].iloc[-1]
        if latest_vol > avg_vol * 1.5:
            return "bullish"
        if latest_vol < avg_vol * 0.5:
            return "bearish"
        return "neutral"
