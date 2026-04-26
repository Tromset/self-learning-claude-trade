# Skill: Risk Management

## Purpose
Calculate safe position sizes and validate that every proposed trade meets minimum
risk/reward and portfolio-exposure criteria before execution.

## Key Rules (defaults)
| Parameter | Default | Description |
|---|---|---|
| `max_position_size` | 10% | Maximum portfolio allocation per position |
| `max_portfolio_risk` | 2% | Maximum capital at risk per trade |
| `stop_loss_pct` | 5% | Default stop-loss if signal doesn't specify one |
| Minimum risk/reward | 1.5× | Trades with R/R below this are rejected |

## Usage

### Size a position
```python
from src import RiskManager
from src.trading_strategy import TradeSignal, Signal

rm = RiskManager()
signal = TradeSignal("AAPL", Signal.BUY, 0.8, 185.0, "RSI oversold", "rsi",
                     stop_loss=176.0, take_profit=204.0)

sizing = rm.size_position(signal, portfolio_value=100_000, current_price=185.0)
print(f"Buy {sizing.shares} shares (${sizing.dollar_amount:,.0f}), "
      f"risk ${sizing.risk_amount:,.0f}, R/R {sizing.risk_reward_ratio:.1f}x")
```

### Validate before execution
```python
ok, message = rm.is_trade_acceptable(sizing)
if not ok:
    print(f"Trade rejected: {message}")
```

### Monitor portfolio heat
```python
open_positions = [{"risk_pct": 0.015}, {"risk_pct": 0.018}]
heat = rm.calculate_portfolio_heat(open_positions)
print(f"Portfolio heat: {heat:.1%}")  # should stay below ~6%
```

## PositionSizing Fields
| Field | Description |
|---|---|
| `shares` | Number of shares to buy |
| `dollar_amount` | Total cost |
| `position_pct` | Fraction of portfolio |
| `stop_loss` | Stop-loss price |
| `take_profit` | Take-profit price |
| `risk_amount` | Dollar risk if stop hit |
| `risk_reward_ratio` | Reward / Risk ratio |
