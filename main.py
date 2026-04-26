#!/usr/bin/env python3
"""Entry point for the self-learning Claude trade system."""

from __future__ import annotations

import argparse
from rich.console import Console
from rich.table import Table

from config import DEFAULT_SYMBOLS, DEFAULT_PERIOD, DEFAULT_INTERVAL, BACKTEST_INITIAL_CAPITAL
from src import (
    MarketDataFetcher,
    TechnicalAnalyzer,
    ClaudeTradeAdvisor,
    StrategyManager,
    MACrossoverStrategy,
    RSIStrategy,
    BollingerBandStrategy,
    Portfolio,
    RiskManager,
    Backtester,
    SelfLearner,
)

console = Console()


def build_strategy_manager(learner: SelfLearner) -> StrategyManager:
    manager = StrategyManager()
    weights = learner.strategy_weights
    strategies = [MACrossoverStrategy(), RSIStrategy(), BollingerBandStrategy()]
    for s in strategies:
        s.weight = weights.get(s.name, 1.0)
        manager.add_strategy(s)
    return manager


def run_analysis(symbols: list[str]) -> None:
    fetcher = MarketDataFetcher(default_period=DEFAULT_PERIOD, default_interval=DEFAULT_INTERVAL)
    advisor = ClaudeTradeAdvisor()
    learner = SelfLearner()
    strategy_manager = build_strategy_manager(learner)

    table = Table(title="Trade Signal Analysis")
    table.add_column("Symbol", style="cyan")
    table.add_column("Signal", style="bold")
    table.add_column("Confidence", justify="right")
    table.add_column("Claude Action", style="green")
    table.add_column("Claude Confidence", justify="right")
    table.add_column("Summary")

    for symbol in symbols:
        console.print(f"Analyzing [cyan]{symbol}[/cyan]...")
        try:
            df = fetcher.fetch(symbol)
            signal = strategy_manager.get_consensus(symbol, df)
            fundamentals = fetcher.get_fundamentals(symbol)
            context = learner.get_context_for_advisor(symbol, signal.strategy_name)
            claude_analysis = advisor.analyze_signal(signal, df, fundamentals, context)

            table.add_row(
                symbol,
                signal.signal.value.upper(),
                f"{signal.confidence:.0%}",
                claude_analysis.get("action", "N/A").upper(),
                f"{claude_analysis.get('confidence', 0)}%",
                claude_analysis.get("summary", "")[:80],
            )
        except Exception as exc:
            table.add_row(symbol, "ERROR", "-", "-", "-", str(exc)[:80])

    console.print(table)


def run_backtest(symbols: list[str]) -> None:
    fetcher = MarketDataFetcher(default_period="2y", default_interval=DEFAULT_INTERVAL)
    learner = SelfLearner()
    backtester = Backtester(initial_capital=BACKTEST_INITIAL_CAPITAL)

    table = Table(title="Backtest Results")
    table.add_column("Symbol", style="cyan")
    table.add_column("Return", justify="right")
    table.add_column("Sharpe", justify="right")
    table.add_column("Max DD", justify="right")
    table.add_column("Win Rate", justify="right")
    table.add_column("Trades", justify="right")

    for symbol in symbols:
        console.print(f"Backtesting [cyan]{symbol}[/cyan]...")
        try:
            df = fetcher.fetch(symbol)
            strategy_manager = build_strategy_manager(learner)
            result = backtester.run(symbol, df, strategy_manager)
            table.add_row(
                symbol,
                f"{result.total_return_pct:.2%}",
                f"{result.sharpe_ratio:.2f}",
                f"{result.max_drawdown_pct:.2%}",
                f"{result.win_rate:.2%}",
                str(result.total_trades),
            )
        except Exception as exc:
            table.add_row(symbol, "ERROR", "-", "-", "-", str(exc)[:60])

    console.print(table)


def run_learn() -> None:
    learner = SelfLearner()
    learner.update_strategy_weights()
    insight = learner.generate_learning_insight()
    console.print("[bold green]Learning Insight:[/bold green]")
    console.print(insight)
    console.print("\n[bold]Updated Strategy Weights:[/bold]", learner.strategy_weights)


def main() -> None:
    parser = argparse.ArgumentParser(description="Self-Learning Claude Trade System")
    parser.add_argument("command", choices=["analyze", "backtest", "learn"],
                        help="Command to run")
    parser.add_argument("--symbols", nargs="+", default=DEFAULT_SYMBOLS,
                        help="Ticker symbols to process")
    args = parser.parse_args()

    if args.command == "analyze":
        run_analysis(args.symbols)
    elif args.command == "backtest":
        run_backtest(args.symbols)
    elif args.command == "learn":
        run_learn()


if __name__ == "__main__":
    main()
