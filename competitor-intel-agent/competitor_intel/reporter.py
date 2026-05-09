from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from .config import Settings
from .models import IntelItem, RunMetrics


class MarkdownReporter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.settings.output_dir.mkdir(parents=True, exist_ok=True)

    def write_report(
        self,
        items: list[IntelItem],
        metrics: RunMetrics,
        period: str,
        errors: list[str] | None = None,
    ) -> Path:
        now = datetime.now()
        filename = f"{now.strftime('%Y-%m-%d')}-{period}-intel-report.md"
        path = self.settings.output_dir / filename
        path.write_text(self._render(items, metrics, period, now, errors or []), encoding="utf-8")
        return path

    def _render(
        self,
        items: list[IntelItem],
        metrics: RunMetrics,
        period: str,
        now: datetime,
        errors: list[str],
    ) -> str:
        high_items = [item for item in items if item.impact == "high"]
        medium_items = [item for item in items if item.impact == "medium"]
        category_counts = Counter(item.category for item in items)
        competitor_counts = Counter(item.competitor for item in items)

        lines = [
            f"# {self.settings.project_name} - {period.title()} Intel Report",
            "",
            f"- Generated at: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- Competitors scanned: {metrics.competitors_scanned}",
            f"- Sources scanned: {metrics.sources_scanned}",
            f"- Raw items seen: {metrics.raw_items_seen}",
            f"- New changes found: {metrics.new_items_found}",
            f"- High-impact changes: {metrics.high_impact_items}",
            "",
            "## Executive Summary",
            "",
            self._executive_summary(items, metrics),
            "",
            "## Category Breakdown",
            "",
        ]

        if category_counts:
            for category, count in category_counts.most_common():
                lines.append(f"- {category}: {count}")
        else:
            lines.append("- No new changes detected.")

        lines.extend(["", "## Competitor Breakdown", ""])
        if competitor_counts:
            for competitor, count in competitor_counts.most_common():
                lines.append(f"- {competitor}: {count}")
        else:
            lines.append("- No new competitor changes detected.")

        lines.extend(["", "## High Priority Signals", ""])
        lines.extend(self._render_items(high_items) or ["No high-priority signals found."])

        lines.extend(["", "## Medium Priority Signals", ""])
        lines.extend(self._render_items(medium_items) or ["No medium-priority signals found."])

        lines.extend(["", "## All New Signals", ""])
        grouped = defaultdict(list)
        for item in items:
            grouped[item.competitor].append(item)

        if not grouped:
            lines.append("No new signals in this run.")
        else:
            for competitor, competitor_items in sorted(grouped.items()):
                lines.extend(["", f"### {competitor}", ""])
                lines.extend(self._render_items(competitor_items))

        lines.extend(
            [
                "",
                "## Suggested Next Actions",
                "",
                "- Review high-impact items and decide whether they change roadmap, messaging, or sales enablement.",
                "- Compare repeated hiring signals against product and market categories to infer strategic focus.",
                "- Add missing competitor sources to config.yaml when analysts manually discover useful pages.",
            ]
        )

        if errors:
            lines.extend(["", "## Fetch Errors", ""])
            for error in errors:
                lines.append(f"- {error}")

        return "\n".join(lines).strip() + "\n"

    def _executive_summary(self, items: list[IntelItem], metrics: RunMetrics) -> str:
        if not items:
            return "No new public competitor changes were detected in this run."

        top_categories = Counter(item.category for item in items).most_common(3)
        top_text = ", ".join(f"{category} ({count})" for category, count in top_categories)
        return (
            f"The agent found {metrics.new_items_found} new changes across "
            f"{metrics.competitors_scanned} competitors. "
            f"Primary signal categories: {top_text}. "
            f"{metrics.high_impact_items} items require priority review."
        )

    def _render_items(self, items: list[IntelItem]) -> list[str]:
        lines: list[str] = []
        for item in items:
            lines.extend(
                [
                    f"- **[{item.impact.upper()}] {item.competitor} / {item.category}**: {item.title}",
                    f"  - Source: [{item.source_name}]({item.url})",
                    f"  - Summary: {item.summary}",
                    f"  - Implication: {item.business_implication}",
                ]
            )
            if item.published_at:
                lines.append(f"  - Published: {item.published_at}")
        return lines
