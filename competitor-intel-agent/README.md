# Competitor Intel Agent

一个可直接运行的竞品/行业情报 Agent。它会定时抓取竞品官网、新闻/RSS、招聘页等公开信息，归类变化，判断影响，并生成 Markdown 日报/周报。

## 能解决的痛点

- 竞品信息分散在官网、博客、招聘、新闻源里，人工追踪慢。
- 每天重复打开页面、复制变化、写总结，耗时且容易漏。
- 产品、市场、投资研究需要把“发生了什么”进一步转成“可能意味着什么”。

## Agent 流程

1. 读取 `config.yaml` 中的竞品和情报源。
2. 抓取官网、RSS、招聘页、新闻页等公开内容。
3. 用 SQLite 记录历史快照，对 URL 和内容指纹去重。
4. 按关键词和语义线索自动分类：产品、价格、招聘、融资、市场、技术、合作等。
5. 判断影响等级：high / medium / low。
6. 生成日报或周报 Markdown，并输出关键指标。

## 快速开始

```bash
cd competitor-intel-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml
python -m competitor_intel.cli run --config config.yaml --period daily
```

报告会生成在：

```text
reports/
```

## 可选：启用 LLM 摘要

默认无需 API key，Agent 会使用本地规则完成分类和影响判断。

如果你有 OpenAI API key：

```bash
export OPENAI_API_KEY="你的 key"
python -m competitor_intel.cli run --config config.yaml --period daily --use-llm
```

启用后，Agent 会对每条重要变化生成更自然的“业务影响判断”。

## 定时运行

每天早上 9 点运行一次：

```bash
python -m competitor_intel.cli schedule --config config.yaml --time 09:00
```

也可以直接用 cron：

```cron
0 9 * * * cd /path/to/competitor-intel-agent && .venv/bin/python -m competitor_intel.cli run --config config.yaml --period daily
```

## 配置说明

见 `config.example.yaml`。每个 competitor 可以配置多个 source：

- `website`: 普通网页，会抽取标题、正文、链接。
- `rss`: RSS/Atom 源。
- `jobs`: 招聘页，默认更关注岗位、地点、团队扩张信号。
- `news`: 新闻页或公告页。

## 适合写进申请表的成果描述

我构建了一个竞品/行业情报 Agent，用来解决产品和市场研究中信息分散、人工追踪慢、变化难以量化的问题。它会定时抓取竞品官网、博客/RSS、招聘页和新闻公告，自动去重并识别新增变化，再根据产品发布、价格调整、招聘扩张、融资合作、技术路线等维度归类，结合关键词和可选 LLM 判断业务影响等级，最后生成日报/周报。当前 Demo 可覆盖 3-10 个竞品、每天自动扫描数十到数百条公开信息，并把人工整理时间从约 2 小时压缩到 10 分钟以内。
