# Skill: Claude Advisory

## Purpose
Use Claude (via the Anthropic API) to validate or override a raw strategy signal,
provide risk-adjusted reasoning, and return structured JSON with trade parameters.

## How It Works
1. `ClaudeTradeAdvisor.analyze_signal(signal, df, fundamentals, learning_context)` builds a
   detailed prompt including technical indicators, recent price data, fundamental metrics,
   and historical learning context from `SelfLearner`.
2. Claude's system prompt is **ephemeral-cached** to reduce token costs on repeated calls.
3. The response is parsed from JSON; if parsing fails it gracefully falls back to the raw signal.

## Prompt Caching
The large system prompt (trading expertise context) is marked with `cache_control: ephemeral`
so Anthropic's prompt caching keeps it warm across multiple calls in the same session,
significantly reducing latency and cost.

## Output Schema
```json
{
  "action": "buy | sell | hold",
  "confidence": 0,
  "stop_loss": 0.0,
  "take_profit": 0.0,
  "reasoning": ["point 1", "point 2"],
  "risks": ["risk 1", "risk 2"],
  "summary": "One-sentence summary of recommendation"
}
```

## Post-Trade Learning
After a trade closes, call `ClaudeTradeAdvisor.evaluate_trade_outcome(signal, outcome)`
to get Claude's post-mortem analysis. Feed this back into `SelfLearner.record_trade()`.

## Example
```python
from src import ClaudeTradeAdvisor, MarketDataFetcher, SelfLearner
from src.trading_strategy import TradeSignal, Signal

advisor = ClaudeTradeAdvisor()
fetcher = MarketDataFetcher()
learner = SelfLearner()

df = fetcher.fetch("AAPL")
signal = TradeSignal("AAPL", Signal.BUY, 0.72, 185.50, "RSI oversold", "rsi",
                     stop_loss=176.0, take_profit=200.0)

context = learner.get_context_for_advisor("AAPL", "rsi")
analysis = advisor.analyze_signal(signal, df, context=context)
print(analysis)
```
