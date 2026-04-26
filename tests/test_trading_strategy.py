from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.trading_strategy import (
    MACrossoverStrategy,
    RSIStrategy,
    BollingerBandStrategy,
    StrategyManager,
    Signal,
)
from src.technical_analysis import TechnicalAnalyzer


def _make_df(n: int = 300, trend: str = "up") -> pd.DataFrame:
    np.random.seed(42)
    prices = [100.0]
    for _ in range(n - 1):
        change = np.random.normal(0.001 if trend == "up" else -0.001, 0.015)
        prices.append(max(1.0, prices[-1] * (1 + change)))
    idx = pd.date_range("2023-01-01", periods=n, freq="B")
    df = pd.DataFrame({
        "open": prices,
        "high": [p * 1.005 for p in prices],
        "low": [p * 0.995 for p in prices],
        "close": prices,
        "volume": np.random.randint(1_000_000, 5_000_000, n),
    }, index=idx)
    return df


@pytest.fixture
def uptrend_df():
    analyzer = TechnicalAnalyzer()
    return analyzer.add_all_indicators(_make_df(300, "up"))


@pytest.fixture
def downtrend_df():
    analyzer = TechnicalAnalyzer()
    return analyzer.add_all_indicators(_make_df(300, "down"))


def test_ma_crossover_returns_signal(uptrend_df):
    strategy = MACrossoverStrategy()
    result = strategy.generate_signal("TEST", uptrend_df)
    assert result.signal in Signal.__members__.values()
    assert 0.0 <= result.confidence <= 1.0


def test_rsi_strategy_oversold(downtrend_df):
    strategy = RSIStrategy(oversold=35, overbought=65)
    result = strategy.generate_signal("TEST", downtrend_df)
    assert result.symbol == "TEST"
    assert result.signal in (Signal.BUY, Signal.HOLD)


def test_bollinger_band_strategy(uptrend_df):
    strategy = BollingerBandStrategy()
    result = strategy.generate_signal("TEST", uptrend_df)
    assert result.strategy_name == "bollinger_bands"


def test_strategy_manager_consensus(uptrend_df):
    manager = StrategyManager()
    manager.add_strategy(MACrossoverStrategy())
    manager.add_strategy(RSIStrategy())
    manager.add_strategy(BollingerBandStrategy())
    result = manager.get_consensus("TEST", uptrend_df)
    assert result.signal in Signal.__members__.values()
    assert result.strategy_name == "consensus"


def test_strategy_manager_no_strategies_raises():
    manager = StrategyManager()
    df = _make_df(300)
    with pytest.raises(RuntimeError, match="No strategies registered"):
        manager.get_consensus("TEST", df)
