from __future__ import annotations

import pytest
from src.risk_management import RiskManager
from src.trading_strategy import TradeSignal, Signal


def _buy_signal(price: float = 100.0, stop: float = 95.0, tp: float = 110.0) -> TradeSignal:
    return TradeSignal(
        symbol="TEST",
        signal=Signal.BUY,
        confidence=0.75,
        price=price,
        reason="test",
        strategy_name="test_strategy",
        stop_loss=stop,
        take_profit=tp,
    )


def test_size_position_basic():
    rm = RiskManager(max_position_size=0.10, max_portfolio_risk=0.02, stop_loss_pct=0.05)
    sizing = rm.size_position(_buy_signal(100, 95, 110), portfolio_value=100_000, current_price=100.0)
    assert sizing is not None
    assert sizing.shares > 0
    assert sizing.dollar_amount <= 100_000 * 0.10


def test_size_position_hold_returns_none():
    rm = RiskManager()
    signal = TradeSignal("TEST", Signal.HOLD, 0.5, 100.0, "no signal", "test")
    result = rm.size_position(signal, 100_000, 100.0)
    assert result is None


def test_risk_reward_ratio():
    rm = RiskManager()
    sizing = rm.size_position(_buy_signal(100, 95, 110), 100_000, 100.0)
    assert sizing is not None
    assert sizing.risk_reward_ratio == pytest.approx(2.0, rel=0.05)


def test_is_trade_acceptable_passes():
    rm = RiskManager()
    sizing = rm.size_position(_buy_signal(100, 95, 115), 100_000, 100.0)
    assert sizing is not None
    ok, msg = rm.is_trade_acceptable(sizing)
    assert ok, msg


def test_portfolio_heat():
    rm = RiskManager()
    positions = [{"risk_pct": 0.01}, {"risk_pct": 0.015}]
    heat = rm.calculate_portfolio_heat(positions)
    assert heat == pytest.approx(0.025)
