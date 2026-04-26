# Skill: Portfolio Management

## Purpose
Track open positions, available cash, completed trade history, and enforce
stop-loss / take-profit rules across the entire portfolio.

## Key Classes

### `Position`
Represents a single open holding.

| Field | Description |
|---|---|
| `symbol` | Ticker symbol |
| `shares` | Number of shares held |
| `entry_price` | Price at which position was opened |
| `stop_loss` | Price that triggers automatic exit |
| `take_profit` | Price that triggers profit-taking exit |
| `current_price` | Latest mark-to-market price |
| `unrealized_pnl` | Current profit/loss in dollars |
| `unrealized_pnl_pct` | Current profit/loss as a percentage |

### `Trade`
Immutable record of a completed round-trip trade.

| Field | Description |
|---|---|
| `pnl` | Net dollar profit/loss |
| `pnl_pct` | Percentage gain/loss |
| `hold_days` | How many calendar days the trade was open |

## Usage

```python
from src import Portfolio, RiskManager
from src.trading_strategy import TradeSignal, Signal

portfolio = Portfolio(initial_capital=100_000)

# Open a position (after sizing via RiskManager)
signal = TradeSignal("AAPL", Signal.BUY, 0.8, 185.0, "RSI oversold", "rsi",
                     stop_loss=176.0, take_profit=204.0)
sizing = RiskManager().size_position(signal, 100_000, 185.0)
portfolio.open_position(signal, sizing)

# Update prices and check stops / take-profits each bar
portfolio.update_prices({"AAPL": 205.0})
closed_trades = portfolio.check_stops({"AAPL": 205.0})

# Close manually
trade = portfolio.close_position("AAPL", 205.0, "manual")

# Review performance
summary = portfolio.get_performance_summary()
print(f"Win rate: {summary['win_rate']:.0%}, Total P&L: ${summary['total_pnl']:,.0f}")
```

## Performance Summary Keys
| Key | Description |
|---|---|
| `total_trades` | Number of completed trades |
| `win_rate` | Fraction of winning trades |
| `avg_pnl_pct` | Average percentage gain/loss per trade |
| `total_pnl` | Cumulative dollar P&L |
| `total_return_pct` | Overall return on initial capital |
| `avg_hold_days` | Average trade duration in days |
