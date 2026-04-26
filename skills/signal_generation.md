# Skill: Signal Generation

## Purpose
Generate trade signals (BUY / SELL / HOLD) for a symbol using one or more strategies
and optionally produce a consensus vote across all active strategies.

## Strategies Available
| Class | Name | Description |
|---|---|---|
| `MACrossoverStrategy` | `ma_crossover` | Golden/death-cross on configurable SMA windows |
| `RSIStrategy` | `rsi` | Oversold/overbought RSI mean-reversion |
| `BollingerBandStrategy` | `bollinger_bands` | Price touches outer Bollinger Bands |

## Usage

### Single strategy
```python
from src.trading_strategy import MACrossoverStrategy
from src import MarketDataFetcher
from src.technical_analysis import TechnicalAnalyzer

fetcher = MarketDataFetcher()
analyzer = TechnicalAnalyzer()
df = analyzer.add_all_indicators(fetcher.fetch("TSLA"))

strategy = MACrossoverStrategy(fast=20, slow=50)
signal = strategy.generate_signal("TSLA", df)
print(signal.signal, signal.confidence, signal.reason)
```

### Consensus across all strategies
```python
from src import StrategyManager, MACrossoverStrategy, RSIStrategy, BollingerBandStrategy

manager = StrategyManager()
manager.add_strategy(MACrossoverStrategy())
manager.add_strategy(RSIStrategy())
manager.add_strategy(BollingerBandStrategy())

consensus = manager.get_consensus("TSLA", df)
print(consensus)
```

## Output (`TradeSignal`)
| Field | Type | Description |
|---|---|---|
| `symbol` | str | Ticker symbol |
| `signal` | Signal | BUY / SELL / HOLD |
| `confidence` | float | 0.0 – 1.0 |
| `price` | float | Price at signal time |
| `reason` | str | Human-readable rationale |
| `stop_loss` | float | Suggested stop-loss price |
| `take_profit` | float | Suggested take-profit price |
