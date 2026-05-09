from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Source:
    type: str
    name: str
    url: str


@dataclass(frozen=True)
class Competitor:
    name: str
    description: str
    sources: list[Source]


@dataclass(frozen=True)
class Settings:
    project_name: str
    timezone: str
    output_dir: Path
    database_path: Path
    max_items_per_source: int
    request_timeout_seconds: int
    user_agent: str
    categories: dict[str, list[str]]
    high_keywords: list[str]
    medium_keywords: list[str]
    competitors: list[Competitor]


def load_config(path: str | Path) -> Settings:
    config_path = Path(path)
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    base_dir = config_path.parent

    project = raw.get("project", {})
    run = raw.get("run", {})
    classification = raw.get("classification", {})
    impact = raw.get("impact", {})

    competitors = [
        Competitor(
            name=item["name"],
            description=item.get("description", ""),
            sources=[
                Source(type=source["type"], name=source["name"], url=source["url"])
                for source in item.get("sources", [])
            ],
        )
        for item in raw.get("competitors", [])
    ]

    output_dir = _resolve_path(base_dir, project.get("output_dir", "reports"))
    database_path = _resolve_path(base_dir, project.get("database_path", "data/intel.db"))

    return Settings(
        project_name=project.get("name", "Competitor Intel Agent"),
        timezone=project.get("timezone", "UTC"),
        output_dir=output_dir,
        database_path=database_path,
        max_items_per_source=int(run.get("max_items_per_source", 20)),
        request_timeout_seconds=int(run.get("request_timeout_seconds", 20)),
        user_agent=run.get("user_agent", "CompetitorIntelAgent/1.0"),
        categories=classification.get("categories", {}),
        high_keywords=impact.get("high_keywords", []),
        medium_keywords=impact.get("medium_keywords", []),
        competitors=competitors,
    )


def _resolve_path(base_dir: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base_dir / path
