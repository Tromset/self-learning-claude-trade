# Skill: Backtesting

## Purpose
Evaluate strategy performance on historical data using an event-driven backtester
that simulates realistic trade execution with commissions, stop-losses, and take-profits.

## Features
- Full OHLCV event loop over historical data
- Automatic position sizing via `RiskManager`
- Stop-loss and take-profit simulation
- Commission deduction per trade (default 0.1%)
- Sharpe ratio and maximum drawdown calculation

## Usage
```python
from src import Backtester, StrategyManager, MACrossoverStrategy, RSIStrategy, MarketDataFetcher

fetcher = MarketDataFetcher(default_period="2y")
backtester = Backtester(initial_capital=100_000)

manager = StrategyManager()
manager.add_strategy(MACrossoverStrategy())
manager.add_strategy(RSIStrategy())

df = fetcher.fetch("SPY")
result = backtester.run("SPY", df, manager)

print(f"Total Return: {result.total_return_pct:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown_pct:.2%}")
print(f"Win Rate: {result.win_rate:.2%} over {result.total_trades} trades")
```

## BacktestResult Fields
| Field | Description |
|---|---|
| `total_return_pct` | Overall return from initial capital |
| `sharpe_ratio` | Annualised Sharpe (252 trading days, 4% risk-free rate) |
| `max_drawdown_pct` | Largest peak-to-trough equity decline |
| `win_rate` | Fraction of trades that were profitable |
| `total_trades` | Number of completed round-trip trades |
| `avg_hold_days` | Average days per trade |
| `trades` | List of individual trade dicts |

## CLI
```bash
python main.py backtest --symbols AAPL MSFT SPY
```
