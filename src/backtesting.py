from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import pandas as pd
import numpy as np

from config import BACKTEST_INITIAL_CAPITAL, BACKTEST_COMMISSION
from .technical_analysis import TechnicalAnalyzer
from .trading_strategy import StrategyManager, Signal
from .risk_management import RiskManager
from .portfolio import Portfolio


@dataclass
class BacktestResult:
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate: float
    total_trades: int
    avg_hold_days: float
    trades: list[dict] = field(default_factory=list)


class Backtester:
    """Event-driven backtester for strategy evaluation."""

    def __init__(
        self,
        initial_capital: float = BACKTEST_INITIAL_CAPITAL,
        commission: float = BACKTEST_COMMISSION,
    ):
        self.initial_capital = initial_capital
        self.commission = commission
        self.analyzer = TechnicalAnalyzer()
        self.risk_manager = RiskManager()

    def run(
        self,
        symbol: str,
        df: pd.DataFrame,
        strategy_manager: StrategyManager,
        min_lookback: int = 200,
    ) -> BacktestResult:
        df = self.analyzer.add_all_indicators(df.copy())
        df = df.dropna()

        capital = self.initial_capital
        position: Optional[dict] = None
        trades: list[dict] = []
        equity_curve: list[float] = [capital]

        for i in range(min_lookback, len(df)):
            window = df.iloc[: i + 1]
            current_price = float(window["close"].iloc[-1])
            current_date = window.index[-1]

            if position:
                if current_price <= position["stop_loss"]:
                    pnl = (current_price - position["entry_price"]) * position["shares"]
                    pnl -= position["shares"] * current_price * self.commission
                    capital += position["shares"] * current_price - position["shares"] * current_price * self.commission
                    trades.append({**position, "exit_price": current_price, "exit_date": current_date,
                                   "exit_reason": "stop_loss", "pnl": pnl})
                    position = None
                elif position.get("take_profit") and current_price >= position["take_profit"]:
                    pnl = (current_price - position["entry_price"]) * position["shares"]
                    capital += position["shares"] * current_price * (1 - self.commission)
                    trades.append({**position, "exit_price": current_price, "exit_date": current_date,
                                   "exit_reason": "take_profit", "pnl": pnl})
                    position = None

            if not position:
                try:
                    signal = strategy_manager.get_consensus(symbol, window)
                except Exception:
                    equity_curve.append(capital)
                    continue

                if signal.signal == Signal.BUY:
                    sizing = self.risk_manager.size_position(signal, capital, current_price)
                    if sizing and sizing.shares > 0:
                        cost = sizing.shares * current_price * (1 + self.commission)
                        if cost <= capital:
                            capital -= cost
                            position = {
                                "entry_price": current_price,
                                "entry_date": current_date,
                                "shares": sizing.shares,
                                "stop_loss": sizing.stop_loss,
                                "take_profit": sizing.take_profit,
                                "strategy": signal.strategy_name,
                            }

            position_value = (position["shares"] * current_price) if position else 0
            equity_curve.append(capital + position_value)

        if position:
            final_price = float(df["close"].iloc[-1])
            capital += position["shares"] * final_price * (1 - self.commission)
            trades.append({**position, "exit_price": final_price,
                           "exit_date": df.index[-1], "exit_reason": "end_of_data",
                           "pnl": (final_price - position["entry_price"]) * position["shares"]})

        equity_series = pd.Series(equity_curve)
        return BacktestResult(
            symbol=symbol,
            start_date=df.index[min_lookback],
            end_date=df.index[-1],
            initial_capital=self.initial_capital,
            final_capital=capital,
            total_return_pct=(capital - self.initial_capital) / self.initial_capital,
            sharpe_ratio=self._sharpe(equity_series),
            max_drawdown_pct=self._max_drawdown(equity_series),
            win_rate=sum(1 for t in trades if t["pnl"] > 0) / len(trades) if trades else 0.0,
            total_trades=len(trades),
            avg_hold_days=np.mean([(t["exit_date"] - t["entry_date"]).days for t in trades]) if trades else 0.0,
            trades=trades,
        )

    def _sharpe(self, equity: pd.Series, risk_free: float = 0.04, periods: int = 252) -> float:
        returns = equity.pct_change().dropna()
        if returns.std() == 0:
            return 0.0
        excess = returns.mean() * periods - risk_free
        return float(excess / (returns.std() * np.sqrt(periods)))

    def _max_drawdown(self, equity: pd.Series) -> float:
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max
        return float(drawdown.min())
