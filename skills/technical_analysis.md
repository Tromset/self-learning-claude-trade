# Skill: Technical Analysis

## Purpose
Compute a comprehensive set of technical indicators on an OHLCV DataFrame and
summarise them into a bullish / bearish / neutral verdict per category.

## Indicator Categories

### Trend
| Indicator | Column(s) | Description |
|---|---|---|
| SMA 20/50/200 | `sma_20`, `sma_50`, `sma_200` | Simple moving averages |
| EMA 12/26 | `ema_12`, `ema_26` | Exponential moving averages |
| MACD | `macd`, `macd_signal`, `macd_diff` | Trend momentum |
| ADX | `adx` | Trend strength (>25 = strong trend) |

### Momentum
| Indicator | Column(s) | Description |
|---|---|---|
| RSI (14) | `rsi` | Overbought >70, oversold <30 |
| Stochastic | `stoch_k`, `stoch_d` | Fast/slow stochastic oscillator |
| CCI | `cci` | Commodity Channel Index |
| Williams %R | `williams_r` | Momentum oscillator |

### Volatility
| Indicator | Column(s) | Description |
|---|---|---|
| Bollinger Bands | `bb_upper`, `bb_middle`, `bb_lower`, `bb_width` | Price envelope |
| ATR | `atr` | Average True Range — raw volatility |

### Volume
| Indicator | Column(s) | Description |
|---|---|---|
| OBV | `obv` | On-Balance Volume |
| VWAP | `vwap` | Volume-Weighted Average Price |
| MFI | `mfi` | Money Flow Index |

## Usage

```python
from src import MarketDataFetcher
from src.technical_analysis import TechnicalAnalyzer

fetcher = MarketDataFetcher()
analyzer = TechnicalAnalyzer()

df = fetcher.fetch("AAPL")
df = analyzer.add_all_indicators(df)   # adds all columns in-place on a copy

# Individual indicator values
print(df[["close", "rsi", "macd", "bb_upper", "bb_lower"]].tail(5))

# High-level signal summary
summary = analyzer.get_signal_summary(df)
# {"trend": "bullish", "momentum": "neutral", "volatility": "bullish",
#  "volume": "bullish", "overall": "bullish"}
print(summary)
```

## Signal Summary Logic
| Category | Bullish condition | Bearish condition |
|---|---|---|
| Trend | Price > SMA20 and SMA50 | Price < SMA20 and SMA50 |
| Momentum | RSI > 60 | RSI < 40 |
| Volatility | BB width ≤ 0.10 | BB width > 0.10 |
| Volume | Latest volume > 1.5× 20-day avg | Latest volume < 0.5× 20-day avg |
