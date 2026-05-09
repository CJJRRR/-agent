from __future__ import annotations

import hashlib
import os
from dataclasses import replace

from .config import Settings
from .models import IntelItem, RawItem


class Analyzer:
    def __init__(self, settings: Settings, use_llm: bool = False):
        self.settings = settings
        self.use_llm = use_llm and bool(os.getenv("OPENAI_API_KEY"))

    def analyze(self, raw: RawItem) -> IntelItem:
        content_hash = _hash_item(raw)
        category = self._classify(raw)
        impact = self._impact(raw)
        summary = self._summary(raw)
        implication = self._business_implication(raw, category, impact)

        item = IntelItem(
            **raw.__dict__,
            content_hash=content_hash,
            category=category,
            impact=impact,
            summary=summary,
            business_implication=implication,
        )

        if self.use_llm and impact in {"high", "medium"}:
            return self._with_llm_implication(item)
        return item

    def _classify(self, raw: RawItem) -> str:
        text = _item_text(raw)
        scores: dict[str, int] = {}
        for category, keywords in self.settings.categories.items():
            scores[category] = sum(1 for keyword in keywords if keyword.lower() in text)
        best_category, best_score = max(scores.items(), key=lambda item: item[1], default=("other", 0))
        return best_category if best_score > 0 else "other"

    def _impact(self, raw: RawItem) -> str:
        text = _item_text(raw)
        high_score = sum(1 for keyword in self.settings.high_keywords if keyword.lower() in text)
        medium_score = sum(1 for keyword in self.settings.medium_keywords if keyword.lower() in text)

        if high_score >= 1:
            return "high"
        if medium_score >= 1:
            return "medium"
        if raw.source_type in {"jobs", "news"}:
            return "medium"
        return "low"

    def _summary(self, raw: RawItem) -> str:
        content = raw.content.strip() or raw.title
        if len(content) <= 220:
            return content
        return content[:217].rstrip() + "..."

    def _business_implication(self, raw: RawItem, category: str, impact: str) -> str:
        if category == "pricing":
            return "可能影响产品包装、销售话术和价格对标，需要关注客户迁移风险。"
        if category == "hiring":
            return "招聘变化可能暗示团队扩张方向，可结合岗位职能判断其战略重点。"
        if category == "product":
            return "产品变化可能改变用户预期或竞品比较维度，建议评估功能差距。"
        if category == "funding":
            return "融资或估值变化可能增强其市场投入能力，需要关注获客和品牌声量。"
        if category == "partnership":
            return "合作生态变化可能带来渠道或集成优势，建议评估共同客户影响。"
        if category == "technical":
            return "技术信号可能影响性能、安全或平台能力对比，建议进一步验证细节。"
        if category == "market":
            return "市场动向可能说明其重点客群或区域变化，可纳入 GTM 判断。"
        if impact == "high":
            return "该变化含高影响关键词，建议人工复核并纳入本周竞品会议。"
        return "暂未识别到强业务信号，可作为背景信息留档。"

    def _with_llm_implication(self, item: IntelItem) -> IntelItem:
        try:
            from openai import OpenAI

            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是产品和市场研究分析师。请用中文输出简洁、可执行的竞品情报摘要。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"竞品：{item.competitor}\n"
                            f"标题：{item.title}\n"
                            f"类别：{item.category}\n"
                            f"影响等级：{item.impact}\n"
                            f"内容：{item.content[:1800]}\n\n"
                            "请输出一句摘要和一句业务影响判断，用 JSON："
                            '{"summary":"...","business_implication":"..."}'
                        ),
                    },
                ],
                temperature=0.2,
            )
            text = response.choices[0].message.content or ""
            summary = _extract_json_value(text, "summary") or item.summary
            implication = _extract_json_value(text, "business_implication") or item.business_implication
            return replace(item, summary=summary, business_implication=implication)
        except Exception:
            return item


def _hash_item(raw: RawItem) -> str:
    normalized = f"{raw.competitor}|{raw.url}|{raw.title}|{raw.content[:1000]}".lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _item_text(raw: RawItem) -> str:
    return f"{raw.title} {raw.url} {raw.content}".lower()


def _extract_json_value(text: str, key: str) -> str | None:
    marker = f'"{key}"'
    start = text.find(marker)
    if start == -1:
        return None
    colon = text.find(":", start)
    if colon == -1:
        return None
    first_quote = text.find('"', colon + 1)
    second_quote = text.find('"', first_quote + 1)
    if first_quote == -1 or second_quote == -1:
        return None
    return text[first_quote + 1 : second_quote].strip()
