from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawItem:
    competitor: str
    source_name: str
    source_type: str
    source_url: str
    title: str
    url: str
    content: str
    published_at: str | None = None
    fetched_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class IntelItem(RawItem):
    content_hash: str = ""
    category: str = "other"
    impact: str = "low"
    summary: str = ""
    business_implication: str = ""
    is_new: bool = True


@dataclass
class RunMetrics:
    competitors_scanned: int = 0
    sources_scanned: int = 0
    raw_items_seen: int = 0
    new_items_found: int = 0
    high_impact_items: int = 0
