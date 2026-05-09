from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

import schedule

from .agent import CompetitorIntelAgent
from .config import load_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="competitor-intel",
        description="Competitor and industry intelligence Agent",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run one intelligence scan")
    run_parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    run_parser.add_argument("--period", default="daily", choices=["daily", "weekly"])
    run_parser.add_argument("--use-llm", action="store_true", help="Use OpenAI for richer analysis")

    init_parser = subparsers.add_parser("init-config", help="Create config.yaml from example")
    init_parser.add_argument("--target", default="config.yaml", help="Target config file")

    schedule_parser = subparsers.add_parser("schedule", help="Run every day at a fixed time")
    schedule_parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    schedule_parser.add_argument("--time", default="09:00", help="Daily time, for example 09:00")
    schedule_parser.add_argument("--use-llm", action="store_true", help="Use OpenAI for richer analysis")

    args = parser.parse_args(argv)

    if args.command == "init-config":
        return _init_config(args.target)
    if args.command == "run":
        return _run_once(args.config, args.period, args.use_llm)
    if args.command == "schedule":
        return _schedule(args.config, args.time, args.use_llm)

    return 1


def _init_config(target: str) -> int:
    target_path = Path(target)
    example_path = Path(__file__).resolve().parents[1] / "config.example.yaml"
    if target_path.exists():
        print(f"Config already exists: {target_path}")
        return 0
    shutil.copyfile(example_path, target_path)
    print(f"Created config: {target_path}")
    return 0


def _run_once(config_path: str, period: str, use_llm: bool) -> int:
    settings = load_config(config_path)
    agent = CompetitorIntelAgent(settings, use_llm=use_llm)
    result = agent.run(period=period)

    print(f"Report: {result.report_path}")
    print(f"Competitors scanned: {result.metrics.competitors_scanned}")
    print(f"Sources scanned: {result.metrics.sources_scanned}")
    print(f"Raw items seen: {result.metrics.raw_items_seen}")
    print(f"New changes found: {result.metrics.new_items_found}")
    print(f"High-impact changes: {result.metrics.high_impact_items}")

    if result.errors:
        print("\nFetch errors:")
        for error in result.errors:
            print(f"- {error}")

    return 0


def _schedule(config_path: str, run_time: str, use_llm: bool) -> int:
    def job() -> None:
        _run_once(config_path, "daily", use_llm)

    schedule.every().day.at(run_time).do(job)
    print(f"Scheduled daily run at {run_time}. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    sys.exit(main())
