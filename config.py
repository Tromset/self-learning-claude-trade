import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-6"

# Trading configuration
DEFAULT_SYMBOLS = ["AAPL", "GOOGL", "MSFT", "TSLA", "SPY"]
DEFAULT_INTERVAL = "1d"
DEFAULT_PERIOD = "1y"

# Risk management
MAX_POSITION_SIZE = 0.10       # 10% of portfolio per position
MAX_PORTFOLIO_RISK = 0.02      # 2% portfolio risk per trade
STOP_LOSS_PCT = 0.05           # 5% stop-loss by default

# Self-learning
LEARNING_LOG_PATH = "data/learning_log.json"
TRADE_HISTORY_PATH = "data/trade_history.json"
STRATEGY_WEIGHTS_PATH = "data/strategy_weights.json"

# Backtesting
BACKTEST_INITIAL_CAPITAL = 100_000.0
BACKTEST_COMMISSION = 0.001    # 0.1% per trade

# Claude prompt caching
CACHE_SYSTEM_PROMPT = True
MAX_TOKENS = 4096
