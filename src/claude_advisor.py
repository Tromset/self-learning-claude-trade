from __future__ import annotations

import json
from typing import Optional
import anthropic
import pandas as pd

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TOKENS, CACHE_SYSTEM_PROMPT
from .trading_strategy import TradeSignal, Signal
from .technical_analysis import TechnicalAnalyzer


SYSTEM_PROMPT = """You are an expert quantitative trading advisor with deep knowledge of:
- Technical analysis (moving averages, RSI, MACD, Bollinger Bands, volume analysis)
- Fundamental analysis (P/E ratios, revenue growth, profit margins, debt levels)
- Risk management (position sizing, stop-loss placement, portfolio diversification)
- Market microstructure and behavioral finance

Your role is to provide clear, actionable trading recommendations with rigorous reasoning.
Always quantify confidence levels and risk/reward ratios. Never provide financial advice
without appropriate caveats about market risk.

When analyzing trade signals, consider:
1. Confluence of multiple technical indicators
2. Overall market context and sector trends
3. Risk/reward ratio (minimum 1:2 recommended)
4. Position sizing relative to portfolio risk
5. Historical performance of similar setups"""


class ClaudeTradeAdvisor:
    """Uses Claude to provide AI-powered trading analysis and recommendations."""

    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=api_key or ANTHROPIC_API_KEY)
        self.analyzer = TechnicalAnalyzer()

    def analyze_signal(
        self,
        signal: TradeSignal,
        df: pd.DataFrame,
        fundamentals: Optional[dict] = None,
        learning_context: Optional[str] = None,
    ) -> dict:
        df_with_indicators = self.analyzer.add_all_indicators(df)
        indicator_summary = self.analyzer.get_signal_summary(df_with_indicators)
        recent_data = self._format_recent_data(df_with_indicators)

        user_message = self._build_analysis_prompt(
            signal, recent_data, indicator_summary, fundamentals, learning_context
        )

        messages = [{"role": "user", "content": user_message}]

        system_content: list[dict] = [{"type": "text", "text": SYSTEM_PROMPT}]
        if CACHE_SYSTEM_PROMPT:
            system_content[0]["cache_control"] = {"type": "ephemeral"}

        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=system_content,
            messages=messages,
        )

        return self._parse_response(response.content[0].text, signal)

    def evaluate_trade_outcome(self, signal: TradeSignal, outcome: dict) -> str:
        prompt = f"""A trade was executed based on this signal:
Symbol: {signal.symbol}
Signal: {signal.signal.value}
Confidence: {signal.confidence:.0%}
Entry Price: ${signal.price:.2f}
Reason: {signal.reason}
Strategy: {signal.strategy_name}

Outcome:
Exit Price: ${outcome.get('exit_price', 0):.2f}
P&L: {outcome.get('pnl_pct', 0):.2%}
Hold Duration: {outcome.get('hold_days', 0)} days
Exit Reason: {outcome.get('exit_reason', 'unknown')}

Provide a brief post-trade analysis (3-5 sentences):
1. Was the trade thesis correct?
2. What worked well or poorly?
3. What should be learned for future similar setups?
Return your analysis as plain text."""

        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _build_analysis_prompt(
        self,
        signal: TradeSignal,
        recent_data: str,
        indicator_summary: dict,
        fundamentals: Optional[dict],
        learning_context: Optional[str],
    ) -> str:
        parts = [
            f"**Trade Signal to Analyze**",
            f"Symbol: {signal.symbol}",
            f"Proposed Action: {signal.signal.value.upper()}",
            f"Strategy Confidence: {signal.confidence:.0%}",
            f"Current Price: ${signal.price:.2f}",
            f"Signal Reason: {signal.reason}",
            f"Strategy: {signal.strategy_name}",
            "",
            f"**Technical Indicator Summary**",
            json.dumps(indicator_summary, indent=2),
            "",
            f"**Recent Price/Volume Data (last 10 sessions)**",
            recent_data,
        ]

        if fundamentals:
            parts += ["", "**Fundamental Data**", json.dumps(fundamentals, indent=2)]

        if learning_context:
            parts += ["", "**Historical Learning Context**", learning_context]

        parts += [
            "",
            "**Your Task**",
            "1. Validate or override the proposed signal (BUY/SELL/HOLD)",
            "2. Assign your own confidence score (0-100)",
            "3. Suggest stop-loss and take-profit levels if action is BUY/SELL",
            "4. Provide 3-5 key reasoning points",
            "5. Identify the top 2 risks to this trade",
            "",
            "Respond in JSON with keys: action, confidence, stop_loss, take_profit, reasoning (list), risks (list), summary (string)",
        ]
        return "\n".join(parts)

    def _format_recent_data(self, df: pd.DataFrame) -> str:
        cols = ["close", "volume", "rsi", "macd", "sma_20", "sma_50"]
        available = [c for c in cols if c in df.columns]
        return df[available].tail(10).round(2).to_string()

    def _parse_response(self, text: str, signal: TradeSignal) -> dict:
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
        return {
            "action": signal.signal.value,
            "confidence": int(signal.confidence * 100),
            "reasoning": [signal.reason],
            "risks": ["Parse error – defaulting to original signal"],
            "summary": text[:300],
        }
