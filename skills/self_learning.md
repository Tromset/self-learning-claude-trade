# Skill: Self-Learning

## Purpose
Continuously improve strategy weights and trading decisions by recording trade outcomes,
updating strategy weights via performance feedback, and generating Claude-powered insights
from recent trade history.

## How It Works

### 1. Record Trade Outcomes
After each closed trade, record the result so the system can learn:
```python
from src import SelfLearner
from src.trading_strategy import TradeSignal, Signal

learner = SelfLearner()
signal = TradeSignal("AAPL", Signal.BUY, 0.75, 185.0, "RSI oversold", "rsi")
outcome = {"exit_price": 192.0, "pnl_pct": 0.038, "hold_days": 12, "exit_reason": "take_profit"}
learner.record_trade(signal, outcome)
```

### 2. Update Strategy Weights
Weights are adjusted based on each strategy's rolling win-rate and average P&L.
Strategies that outperform receive higher weights; underperformers are downweighted.
```python
updated_weights = learner.update_strategy_weights()
print(updated_weights)
# {"ma_crossover": 1.24, "rsi": 0.87, "bollinger_bands": 1.05, "consensus": 1.0}
```

### 3. Generate Learning Insights
Ask Claude to synthesise patterns from the last 20 trades:
```python
insight = learner.generate_learning_insight()
print(insight)
```

### 4. Provide Context to Claude Advisor
Pass historical context for a specific symbol/strategy pair to the advisory skill:
```python
context = learner.get_context_for_advisor("AAPL", "rsi")
# "Historical context for AAPL/rsi: 8 recent trades, 6/8 wins, avg P&L 2.10%, ..."
```

## Persistent Storage
All data is stored as JSON in the `data/` directory:
- `data/trade_history.json` — raw trade records
- `data/strategy_weights.json` — current strategy weights
- `data/learning_log.json` — Claude learning insights log

## CLI
```bash
python main.py learn
```
