# self-learning-claude-trade

A self-improving trading system powered by Claude AI. Combines technical analysis strategies with Claude-powered signal validation and a feedback loop that continuously updates strategy weights based on past trade performance.

## Architecture

```
self-learning-claude-trade/
├── src/
│   ├── market_data.py        # OHLCV data fetching via yfinance
│   ├── technical_analysis.py # 15+ technical indicators (RSI, MACD, BB, ...)
│   ├── trading_strategy.py   # Strategy classes + consensus manager
│   ├── claude_advisor.py     # Claude AI signal validation (with prompt caching)
│   ├── risk_management.py    # Position sizing and risk checks
│   ├── portfolio.py          # Portfolio state, stop/TP management
│   ├── backtesting.py        # Event-driven historical backtester
│   └── self_learning.py      # Outcome recording + weight adaptation
├── skills/                   # Skill documentation for each module
├── tests/                    # Pytest test suite
├── main.py                   # CLI entry point
├── config.py                 # Configuration constants
└── requirements.txt
```

## Skills

| Skill | File | Description |
|---|---|---|
| Market Analysis | `skills/market_analysis.md` | Fetch data and compute indicators |
| Signal Generation | `skills/signal_generation.md` | Generate BUY/SELL/HOLD signals |
| Claude Advisory | `skills/claude_advisory.md` | AI-powered signal validation |
| Risk Management | `skills/risk_management.md` | Position sizing and risk checks |
| Backtesting | `skills/backtesting.md` | Historical strategy evaluation |
| Self Learning | `skills/self_learning.md` | Adaptive strategy weight updates |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Analyze signals for default symbols
python main.py analyze

# Run backtest
python main.py backtest --symbols AAPL MSFT SPY

# Run self-learning update
python main.py learn

# Run tests
pytest tests/
```

## Strategies

- **MA Crossover** — Golden/death-cross on 20/50-day SMAs
- **RSI** — Mean-reversion on overbought/oversold RSI levels
- **Bollinger Bands** — Price touches on upper/lower bands

Each strategy contributes to a weighted consensus. The `SelfLearner` adjusts weights automatically
based on each strategy's rolling win rate and average P&L over the last 100 trades.

## Claude Integration

`ClaudeTradeAdvisor` uses the Anthropic SDK with:
- **Ephemeral prompt caching** on the large system prompt to reduce API costs
- Structured JSON responses for reliable parsing
- Post-trade analysis for learning feedback

## Risk Management

- Max 10% portfolio allocation per position
- Max 2% capital at risk per trade
- Minimum 1.5× risk/reward ratio required
- Automatic stop-loss and take-profit tracking

## Disclaimer

This project is for educational purposes only. It is not financial advice.
Always conduct your own research before making any investment decisions.
