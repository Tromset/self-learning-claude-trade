from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from config import MAX_POSITION_SIZE, MAX_PORTFOLIO_RISK, STOP_LOSS_PCT
from .trading_strategy import TradeSignal, Signal


@dataclass
class PositionSizing:
    symbol: str
    shares: int
    dollar_amount: float
    position_pct: float
    stop_loss: float
    take_profit: Optional[float]
    risk_amount: float
    risk_reward_ratio: Optional[float]


class RiskManager:
    """Calculates position sizes and validates trade risk parameters."""

    def __init__(
        self,
        max_position_size: float = MAX_POSITION_SIZE,
        max_portfolio_risk: float = MAX_PORTFOLIO_RISK,
        stop_loss_pct: float = STOP_LOSS_PCT,
    ):
        self.max_position_size = max_position_size
        self.max_portfolio_risk = max_portfolio_risk
        self.stop_loss_pct = stop_loss_pct

    def size_position(
        self,
        signal: TradeSignal,
        portfolio_value: float,
        current_price: float,
    ) -> Optional[PositionSizing]:
        if signal.signal == Signal.HOLD:
            return None

        stop_loss = signal.stop_loss or (current_price * (1 - self.stop_loss_pct))
        risk_per_share = abs(current_price - stop_loss)

        if risk_per_share == 0:
            return None

        max_risk_dollars = portfolio_value * self.max_portfolio_risk
        shares_by_risk = int(max_risk_dollars / risk_per_share)

        max_position_dollars = portfolio_value * self.max_position_size
        shares_by_size = int(max_position_dollars / current_price)

        shares = min(shares_by_risk, shares_by_size)
        if shares <= 0:
            return None

        dollar_amount = shares * current_price
        risk_amount = shares * risk_per_share

        risk_reward = None
        if signal.take_profit:
            reward_per_share = abs(signal.take_profit - current_price)
            risk_reward = reward_per_share / risk_per_share if risk_per_share else None

        return PositionSizing(
            symbol=signal.symbol,
            shares=shares,
            dollar_amount=dollar_amount,
            position_pct=dollar_amount / portfolio_value,
            stop_loss=stop_loss,
            take_profit=signal.take_profit,
            risk_amount=risk_amount,
            risk_reward_ratio=risk_reward,
        )

    def is_trade_acceptable(self, sizing: PositionSizing) -> tuple[bool, str]:
        if sizing.position_pct > self.max_position_size:
            return False, f"Position {sizing.position_pct:.1%} exceeds max {self.max_position_size:.1%}"
        if sizing.risk_reward_ratio is not None and sizing.risk_reward_ratio < 1.5:
            return False, f"Risk/reward {sizing.risk_reward_ratio:.2f} below minimum 1.5"
        return True, "Trade passes risk checks"

    def calculate_portfolio_heat(self, open_positions: list[dict]) -> float:
        return sum(p.get("risk_pct", 0) for p in open_positions)
