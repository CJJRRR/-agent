from __future__ import annotations

from dataclasses import dataclass

from requests import RequestException

from .analyzer import Analyzer
from .config import Settings
from .fetchers import Fetcher
from .models import IntelItem, RunMetrics
from .reporter import MarkdownReporter
from .storage import IntelStore


@dataclass
class AgentResult:
    report_path: str
    metrics: RunMetrics
    new_items: list[IntelItem]
    errors: list[str]


class CompetitorIntelAgent:
    def __init__(self, settings: Settings, use_llm: bool = False):
        self.settings = settings
        self.fetcher = Fetcher(settings.request_timeout_seconds, settings.user_agent)
        self.analyzer = Analyzer(settings, use_llm=use_llm)
        self.reporter = MarkdownReporter(settings)

    def run(self, period: str = "daily") -> AgentResult:
        store = IntelStore(self.settings.database_path)
        metrics = RunMetrics(competitors_scanned=len(self.settings.competitors))
        new_items: list[IntelItem] = []
        errors: list[str] = []

        try:
            for competitor in self.settings.competitors:
                for source in competitor.sources:
                    metrics.sources_scanned += 1
                    try:
                        raw_items = self.fetcher.fetch(
                            competitor.name,
                            source,
                            self.settings.max_items_per_source,
                        )
                    except RequestException as exc:
                        errors.append(f"{competitor.name} / {source.name}: {exc}")
                        continue
                    except Exception as exc:
                        errors.append(f"{competitor.name} / {source.name}: {type(exc).__name__}: {exc}")
                        continue

                    metrics.raw_items_seen += len(raw_items)

                    for raw in raw_items:
                        item = self.analyzer.analyze(raw)
                        if store.has_seen(item.content_hash):
                            continue
                        store.save_item(item)
                        new_items.append(item)

            metrics.new_items_found = len(new_items)
            metrics.high_impact_items = sum(1 for item in new_items if item.impact == "high")
            report_path = self.reporter.write_report(new_items, metrics, period, errors)
            return AgentResult(
                report_path=str(report_path),
                metrics=metrics,
                new_items=new_items,
                errors=errors,
            )
        finally:
            store.close()
