from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional
import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, LEARNING_LOG_PATH, TRADE_HISTORY_PATH, STRATEGY_WEIGHTS_PATH
from .trading_strategy import TradeSignal


class SelfLearner:
    """Continuously improves strategy weights based on past trade outcomes."""

    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(api_key=api_key or ANTHROPIC_API_KEY)
        self.learning_log: list[dict] = self._load_json(LEARNING_LOG_PATH)
        self.trade_history: list[dict] = self._load_json(TRADE_HISTORY_PATH)
        self.strategy_weights: dict[str, float] = self._load_json(STRATEGY_WEIGHTS_PATH) or {
            "ma_crossover": 1.0,
            "rsi": 1.0,
            "bollinger_bands": 1.0,
            "consensus": 1.0,
        }

    def record_trade(self, signal: TradeSignal, outcome: dict) -> None:
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": signal.symbol,
            "signal": signal.signal.value,
            "confidence": signal.confidence,
            "price": signal.price,
            "strategy": signal.strategy_name,
            "reason": signal.reason,
            "outcome": outcome,
        }
        self.trade_history.append(record)
        self._save_json(TRADE_HISTORY_PATH, self.trade_history)

    def update_strategy_weights(self) -> dict[str, float]:
        if len(self.trade_history) < 5:
            return self.strategy_weights

        performance_by_strategy: dict[str, list[float]] = {}
        for trade in self.trade_history[-100:]:
            strategy = trade.get("strategy", "unknown")
            pnl_pct = trade.get("outcome", {}).get("pnl_pct", 0)
            performance_by_strategy.setdefault(strategy, []).append(pnl_pct)

        for strategy, pnls in performance_by_strategy.items():
            if not pnls:
                continue
            avg_pnl = sum(pnls) / len(pnls)
            win_rate = sum(1 for p in pnls if p > 0) / len(pnls)
            current_weight = self.strategy_weights.get(strategy, 1.0)
            # Adjust weight: better win_rate and avg_pnl → higher weight
            adjustment = (win_rate - 0.5) * 0.2 + avg_pnl * 2
            new_weight = max(0.1, min(3.0, current_weight + adjustment))
            self.strategy_weights[strategy] = round(new_weight, 3)

        self._save_json(STRATEGY_WEIGHTS_PATH, self.strategy_weights)
        return self.strategy_weights

    def generate_learning_insight(self) -> str:
        if len(self.trade_history) < 3:
            return "Not enough trade history for learning insights yet."

        recent_trades = self.trade_history[-20:]
        history_str = json.dumps(recent_trades, indent=2)

        prompt = f"""Analyze the following recent trade history and provide actionable learning insights
to improve future trading decisions. Focus on:
1. Patterns in winning vs losing trades
2. Strategy performance differences
3. Market conditions that worked well or poorly
4. Specific improvements to confidence thresholds or entry criteria

Trade History:
{history_str}

Current Strategy Weights:
{json.dumps(self.strategy_weights, indent=2)}

Provide 3-5 concise, actionable insights."""

        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        insight = response.content[0].text
        self.learning_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "insight": insight,
            "trade_count": len(self.trade_history),
        })
        self._save_json(LEARNING_LOG_PATH, self.learning_log)
        return insight

    def get_context_for_advisor(self, symbol: str, strategy: str) -> Optional[str]:
        relevant = [
            t for t in self.trade_history
            if t.get("symbol") == symbol or t.get("strategy") == strategy
        ][-10:]
        if not relevant:
            return None
        wins = sum(1 for t in relevant if t.get("outcome", {}).get("pnl_pct", 0) > 0)
        avg_pnl = sum(t.get("outcome", {}).get("pnl_pct", 0) for t in relevant) / len(relevant)
        weight = self.strategy_weights.get(strategy, 1.0)
        return (
            f"Historical context for {symbol}/{strategy}: "
            f"{len(relevant)} recent trades, {wins}/{len(relevant)} wins, "
            f"avg P&L {avg_pnl:.2%}, current strategy weight {weight:.2f}."
        )

    @staticmethod
    def _load_json(path: str) -> list | dict:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return []

    @staticmethod
    def _save_json(path: str, data) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
