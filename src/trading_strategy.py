from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import pandas as pd


class Signal(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class TradeSignal:
    symbol: str
    signal: Signal
    confidence: float          # 0.0 – 1.0
    price: float
    reason: str
    strategy_name: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class Strategy(ABC):
    """Base class for all trading strategies."""

    name: str = "base"
    weight: float = 1.0

    @abstractmethod
    def generate_signal(self, symbol: str, df: pd.DataFrame) -> TradeSignal:
        ...


class MACrossoverStrategy(Strategy):
    """Classic golden/death-cross moving-average strategy."""

    name = "ma_crossover"

    def __init__(self, fast: int = 20, slow: int = 50):
        self.fast = fast
        self.slow = slow

    def generate_signal(self, symbol: str, df: pd.DataFrame) -> TradeSignal:
        fast_col = f"sma_{self.fast}"
        slow_col = f"sma_{self.slow}"
        if fast_col not in df.columns or slow_col not in df.columns:
            raise ValueError(f"Indicators {fast_col}/{slow_col} missing. Run TechnicalAnalyzer first.")

        latest = df.iloc[-1]
        prev = df.iloc[-2]
        price = float(latest["close"])

        golden_cross = prev[fast_col] < prev[slow_col] and latest[fast_col] >= latest[slow_col]
        death_cross = prev[fast_col] > prev[slow_col] and latest[fast_col] <= latest[slow_col]

        if golden_cross:
            return TradeSignal(symbol, Signal.BUY, 0.75, price, "Golden cross detected", self.name,
                               stop_loss=price * 0.95, take_profit=price * 1.10)
        if death_cross:
            return TradeSignal(symbol, Signal.SELL, 0.75, price, "Death cross detected", self.name)
        return TradeSignal(symbol, Signal.HOLD, 0.5, price, "No crossover", self.name)


class RSIStrategy(Strategy):
    """Overbought/oversold RSI mean-reversion strategy."""

    name = "rsi"

    def __init__(self, oversold: float = 30, overbought: float = 70):
        self.oversold = oversold
        self.overbought = overbought

    def generate_signal(self, symbol: str, df: pd.DataFrame) -> TradeSignal:
        if "rsi" not in df.columns:
            raise ValueError("RSI indicator missing. Run TechnicalAnalyzer first.")

        latest = df.iloc[-1]
        price = float(latest["close"])
        rsi = float(latest["rsi"])

        if rsi < self.oversold:
            confidence = min(1.0, (self.oversold - rsi) / self.oversold)
            return TradeSignal(symbol, Signal.BUY, confidence, price,
                               f"RSI oversold at {rsi:.1f}", self.name,
                               stop_loss=price * 0.95, take_profit=price * 1.08)
        if rsi > self.overbought:
            confidence = min(1.0, (rsi - self.overbought) / (100 - self.overbought))
            return TradeSignal(symbol, Signal.SELL, confidence, price,
                               f"RSI overbought at {rsi:.1f}", self.name)
        return TradeSignal(symbol, Signal.HOLD, 0.5, price, f"RSI neutral at {rsi:.1f}", self.name)


class BollingerBandStrategy(Strategy):
    """Mean-reversion using Bollinger Band touches."""

    name = "bollinger_bands"

    def generate_signal(self, symbol: str, df: pd.DataFrame) -> TradeSignal:
        for col in ("bb_upper", "bb_lower", "bb_middle"):
            if col not in df.columns:
                raise ValueError(f"{col} missing. Run TechnicalAnalyzer first.")

        latest = df.iloc[-1]
        price = float(latest["close"])

        if price <= float(latest["bb_lower"]):
            return TradeSignal(symbol, Signal.BUY, 0.70, price,
                               "Price touched lower Bollinger Band", self.name,
                               stop_loss=price * 0.97, take_profit=float(latest["bb_middle"]))
        if price >= float(latest["bb_upper"]):
            return TradeSignal(symbol, Signal.SELL, 0.70, price,
                               "Price touched upper Bollinger Band", self.name)
        return TradeSignal(symbol, Signal.HOLD, 0.5, price, "Price within bands", self.name)


class StrategyManager:
    """Aggregates multiple strategies and produces a consensus signal."""

    def __init__(self):
        self.strategies: list[Strategy] = []

    def add_strategy(self, strategy: Strategy) -> None:
        self.strategies.append(strategy)

    def get_consensus(self, symbol: str, df: pd.DataFrame) -> TradeSignal:
        if not self.strategies:
            raise RuntimeError("No strategies registered.")

        signals = [s.generate_signal(symbol, df) for s in self.strategies]
        buy_score = sum(sig.confidence * sig.strategy_name and sig.signal == Signal.BUY and sig.confidence or 0
                        for sig in signals)
        sell_score = sum(sig.confidence if sig.signal == Signal.SELL else 0 for sig in signals)
        buy_score = sum(sig.confidence if sig.signal == Signal.BUY else 0 for sig in signals)

        price = float(df["close"].iloc[-1])
        reasons = [s.reason for s in signals]

        if buy_score > sell_score and buy_score > len(self.strategies) * 0.3:
            return TradeSignal(symbol, Signal.BUY, buy_score / len(self.strategies), price,
                               " | ".join(reasons), "consensus")
        if sell_score > buy_score and sell_score > len(self.strategies) * 0.3:
            return TradeSignal(symbol, Signal.SELL, sell_score / len(self.strategies), price,
                               " | ".join(reasons), "consensus")
        return TradeSignal(symbol, Signal.HOLD, 0.5, price, " | ".join(reasons), "consensus")
