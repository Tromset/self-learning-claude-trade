from __future__ import annotations

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


class MarketDataFetcher:
    """Fetches OHLCV market data for given symbols."""

    def __init__(self, default_period: str = "1y", default_interval: str = "1d"):
        self.default_period = default_period
        self.default_interval = default_interval
        self._cache: dict[str, pd.DataFrame] = {}

    def fetch(
        self,
        symbol: str,
        period: Optional[str] = None,
        interval: Optional[str] = None,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        period = period or self.default_period
        interval = interval or self.default_interval
        cache_key = f"{symbol}:{period}:{interval}"

        if not force_refresh and cache_key in self._cache:
            return self._cache[cache_key]

        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        df.index = pd.to_datetime(df.index)
        df.columns = [c.lower() for c in df.columns]
        self._cache[cache_key] = df
        return df

    def fetch_multiple(
        self,
        symbols: list[str],
        period: Optional[str] = None,
        interval: Optional[str] = None,
    ) -> dict[str, pd.DataFrame]:
        return {s: self.fetch(s, period, interval) for s in symbols}

    def get_latest_price(self, symbol: str) -> float:
        df = self.fetch(symbol, period="5d")
        return float(df["close"].iloc[-1])

    def get_fundamentals(self, symbol: str) -> dict:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "pe_ratio": info.get("trailingPE"),
            "market_cap": info.get("marketCap"),
            "revenue_growth": info.get("revenueGrowth"),
            "profit_margins": info.get("profitMargins"),
            "debt_to_equity": info.get("debtToEquity"),
            "forward_eps": info.get("forwardEps"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
        }
