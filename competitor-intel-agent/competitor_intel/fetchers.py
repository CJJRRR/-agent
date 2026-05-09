from __future__ import annotations

import re
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup

from .config import Source
from .models import RawItem


class FetchError(RuntimeError):
    pass


class Fetcher:
    def __init__(self, timeout_seconds: int, user_agent: str):
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def fetch(self, competitor_name: str, source: Source, max_items: int) -> list[RawItem]:
        if source.type == "rss":
            return self._fetch_rss(competitor_name, source, max_items)
        return self._fetch_page(competitor_name, source, max_items)

    def _fetch_rss(self, competitor_name: str, source: Source, max_items: int) -> list[RawItem]:
        response = self.session.get(source.url, timeout=self.timeout_seconds)
        response.raise_for_status()
        feed = feedparser.parse(response.text)
        items: list[RawItem] = []

        for entry in feed.entries[:max_items]:
            title = _clean_text(entry.get("title", "Untitled"))
            link = entry.get("link", source.url)
            summary = _clean_html(entry.get("summary", ""))
            published_at = entry.get("published", None)
            items.append(
                RawItem(
                    competitor=competitor_name,
                    source_name=source.name,
                    source_type=source.type,
                    source_url=source.url,
                    title=title,
                    url=link,
                    content=summary or title,
                    published_at=published_at,
                )
            )
        return items

    def _fetch_page(self, competitor_name: str, source: Source, max_items: int) -> list[RawItem]:
        response = self.session.get(source.url, timeout=self.timeout_seconds)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()

        title = _clean_text(soup.title.get_text(" ")) if soup.title else source.name
        body_text = _clean_text(soup.get_text(" "))
        links = _extract_relevant_links(soup, source.url, source.type, max_items)

        items = [
            RawItem(
                competitor=competitor_name,
                source_name=source.name,
                source_type=source.type,
                source_url=source.url,
                title=title,
                url=source.url,
                content=body_text[:6000],
            )
        ]

        for link_title, link_url in links:
            items.append(
                RawItem(
                    competitor=competitor_name,
                    source_name=source.name,
                    source_type=source.type,
                    source_url=source.url,
                    title=link_title,
                    url=link_url,
                    content=link_title,
                )
            )

        return items[:max_items]


def _extract_relevant_links(
    soup: BeautifulSoup,
    base_url: str,
    source_type: str,
    max_items: int,
) -> list[tuple[str, str]]:
    common_keywords = (
        "blog", "news", "release", "product", "pricing", "case", "customer",
        "press", "公告", "新闻", "价格", "产品",
    )
    job_keywords = ("career", "job", "role", "opening", "招聘", "岗位")
    keywords = job_keywords if source_type == "jobs" else common_keywords + job_keywords
    ignored_text = {
        "skip to main content",
        "skip to footer",
        "main content",
        "footer",
        "privacy policy",
        "terms of service",
    }
    seen: set[str] = set()
    links: list[tuple[str, str]] = []

    for anchor in soup.find_all("a", href=True):
        text = _clean_text(anchor.get_text(" "))
        href = urljoin(base_url, anchor["href"])
        if not text or text.lower() in ignored_text or href.endswith("#main-content") or href.endswith("#footer"):
            continue
        candidate = f"{text} {href}".lower()
        if href in seen:
            continue
        if any(keyword in candidate for keyword in keywords):
            seen.add(href)
            links.append((text[:180], href))
        if len(links) >= max_items - 1:
            break

    return links


def _clean_html(value: str) -> str:
    soup = BeautifulSoup(value or "", "html.parser")
    return _clean_text(soup.get_text(" "))


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()
