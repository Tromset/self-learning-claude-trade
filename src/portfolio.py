from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .trading_strategy import Signal, TradeSignal
from .risk_management import RiskManager, PositionSizing


@dataclass
class Position:
    symbol: str
    shares: int
    entry_price: float
    entry_date: datetime
    stop_loss: float
    take_profit: Optional[float]
    strategy: str
    current_price: float = 0.0

    @property
    def market_value(self) -> float:
        return self.shares * (self.current_price or self.entry_price)

    @property
    def unrealized_pnl(self) -> float:
        return self.shares * ((self.current_price or self.entry_price) - self.entry_price)

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.entry_price == 0:
            return 0.0
        return (self.current_price - self.entry_price) / self.entry_price


@dataclass
class Trade:
    symbol: str
    signal: str
    entry_price: float
    exit_price: float
    shares: int
    entry_date: datetime
    exit_date: datetime
    strategy: str
    exit_reason: str

    @property
    def pnl(self) -> float:
        return self.shares * (self.exit_price - self.entry_price)

    @property
    def pnl_pct(self) -> float:
        if self.entry_price == 0:
            return 0.0
        return (self.exit_price - self.entry_price) / self.entry_price

    @property
    def hold_days(self) -> int:
        return (self.exit_date - self.entry_date).days


class Portfolio:
    """Tracks open positions, cash, and completed trades."""

    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: dict[str, Position] = {}
        self.trade_history: list[Trade] = []
        self.risk_manager = RiskManager()

    @property
    def market_value(self) -> float:
        return sum(p.market_value for p in self.positions.values())

    @property
    def total_value(self) -> float:
        return self.cash + self.market_value

    @property
    def total_return_pct(self) -> float:
        return (self.total_value - self.initial_capital) / self.initial_capital

    def open_position(self, signal: TradeSignal, sizing: PositionSizing) -> bool:
        cost = sizing.dollar_amount
        if cost > self.cash:
            return False
        self.cash -= cost
        self.positions[signal.symbol] = Position(
            symbol=signal.symbol,
            shares=sizing.shares,
            entry_price=signal.price,
            entry_date=datetime.utcnow(),
            stop_loss=sizing.stop_loss,
            take_profit=sizing.take_profit,
            strategy=signal.strategy_name,
            current_price=signal.price,
        )
        return True

    def close_position(self, symbol: str, exit_price: float, exit_reason: str) -> Optional[Trade]:
        if symbol not in self.positions:
            return None
        pos = self.positions.pop(symbol)
        proceeds = pos.shares * exit_price
        self.cash += proceeds
        trade = Trade(
            symbol=symbol,
            signal="buy",
            entry_price=pos.entry_price,
            exit_price=exit_price,
            shares=pos.shares,
            entry_date=pos.entry_date,
            exit_date=datetime.utcnow(),
            strategy=pos.strategy,
            exit_reason=exit_reason,
        )
        self.trade_history.append(trade)
        return trade

    def update_prices(self, prices: dict[str, float]) -> None:
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].current_price = price

    def check_stops(self, prices: dict[str, float]) -> list[Trade]:
        closed = []
        for symbol, price in prices.items():
            if symbol not in self.positions:
                continue
            pos = self.positions[symbol]
            if price <= pos.stop_loss:
                trade = self.close_position(symbol, price, "stop_loss")
                if trade:
                    closed.append(trade)
            elif pos.take_profit and price >= pos.take_profit:
                trade = self.close_position(symbol, price, "take_profit")
                if trade:
                    closed.append(trade)
        return closed

    def get_performance_summary(self) -> dict:
        if not self.trade_history:
            return {"total_trades": 0, "win_rate": 0.0, "avg_pnl_pct": 0.0, "total_return_pct": self.total_return_pct}

        wins = [t for t in self.trade_history if t.pnl > 0]
        return {
            "total_trades": len(self.trade_history),
            "win_rate": len(wins) / len(self.trade_history),
            "avg_pnl_pct": sum(t.pnl_pct for t in self.trade_history) / len(self.trade_history),
            "total_pnl": sum(t.pnl for t in self.trade_history),
            "total_return_pct": self.total_return_pct,
            "avg_hold_days": sum(t.hold_days for t in self.trade_history) / len(self.trade_history),
        }
