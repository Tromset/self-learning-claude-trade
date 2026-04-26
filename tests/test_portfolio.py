from __future__ import annotations

import pytest
from src.portfolio import Portfolio
from src.risk_management import RiskManager, PositionSizing
from src.trading_strategy import TradeSignal, Signal


def _signal(price: float = 100.0) -> TradeSignal:
    return TradeSignal("AAPL", Signal.BUY, 0.8, price, "test", "test", stop_loss=95.0, take_profit=115.0)


def _sizing(shares: int = 10, price: float = 100.0) -> PositionSizing:
    return PositionSizing(
        symbol="AAPL",
        shares=shares,
        dollar_amount=shares * price,
        position_pct=(shares * price) / 100_000,
        stop_loss=95.0,
        take_profit=115.0,
        risk_amount=shares * 5,
        risk_reward_ratio=3.0,
    )


def test_open_and_close_position():
    portfolio = Portfolio(100_000)
    sig = _signal()
    size = _sizing()
    opened = portfolio.open_position(sig, size)
    assert opened
    assert "AAPL" in portfolio.positions
    trade = portfolio.close_position("AAPL", 110.0, "take_profit")
    assert trade is not None
    assert trade.pnl == pytest.approx(100.0)


def test_portfolio_value_after_open():
    portfolio = Portfolio(100_000)
    portfolio.open_position(_signal(), _sizing())
    assert portfolio.total_value == pytest.approx(100_000)


def test_stop_loss_triggers():
    portfolio = Portfolio(100_000)
    portfolio.open_position(_signal(), _sizing())
    closed = portfolio.check_stops({"AAPL": 94.0})
    assert len(closed) == 1
    assert closed[0].exit_reason == "stop_loss"


def test_take_profit_triggers():
    portfolio = Portfolio(100_000)
    portfolio.open_position(_signal(), _sizing())
    closed = portfolio.check_stops({"AAPL": 116.0})
    assert len(closed) == 1
    assert closed[0].exit_reason == "take_profit"


def test_insufficient_cash():
    portfolio = Portfolio(500)
    opened = portfolio.open_position(_signal(), _sizing(10, 100))
    assert not opened


def test_performance_summary_empty():
    portfolio = Portfolio(100_000)
    summary = portfolio.get_performance_summary()
    assert summary["total_trades"] == 0
