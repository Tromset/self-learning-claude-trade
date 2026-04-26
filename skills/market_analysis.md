# Skill: Market Analysis

## Purpose
Fetch market data and compute technical indicators for a given symbol, then produce
a structured analysis summary suitable for trading decisions.

## Inputs
- `symbol` (str): Ticker symbol, e.g. `"AAPL"`
- `period` (str, optional): Data period, default `"1y"`
- `interval` (str, optional): Bar interval, default `"1d"`

## Steps
1. Use `MarketDataFetcher.fetch(symbol, period, interval)` to retrieve OHLCV data.
2. Pass the DataFrame to `TechnicalAnalyzer.add_all_indicators(df)`.
3. Call `TechnicalAnalyzer.get_signal_summary(df)` to get a bullish/bearish/neutral
   verdict per indicator category.
4. Optionally call `MarketDataFetcher.get_fundamentals(symbol)` for P/E, margins, etc.

## Output
Returns a dict with keys: `trend`, `momentum`, `volatility`, `volume`, `overall`,
plus a `fundamentals` sub-dict when requested.

## Example
```python
from src import MarketDataFetcher, TechnicalAnalyzer

fetcher = MarketDataFetcher()
analyzer = TechnicalAnalyzer()

df = fetcher.fetch("AAPL")
df = analyzer.add_all_indicators(df)
summary = analyzer.get_signal_summary(df)
print(summary)
```
