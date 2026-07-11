"""AI pipeline — OpenRouter / DeepSeek with parallel batches and two-stage filtering."""
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI

from . import config
from .models import Cluster, DailyRecap, ProcessedArticle, ProcessedOutput, RawArticle

log = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MAX_WORKERS = 6


def _client() -> OpenAI:
    return OpenAI(api_key=config.OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)


def _chat(client: OpenAI, prompt: str, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model=config.VEEN_AI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            log.warning("OpenRouter attempt %d failed: %s", attempt + 1, exc)
            if attempt < retries - 1:
                time.sleep(2**attempt)
            else:
                raise


# ── Stage 1: Title-only pre-filter ───────────────────────────────────────────
# Large batches (50) since we only send short titles. Cheap and fast.
# Goal: reject obvious noise without looking at article body at all.

_TITLE_FILTER_PROMPT = """You are pre-screening news article titles for a senior tech professional.

REJECT by title alone if the title is clearly about:
- Sports, entertainment, celebrity, gossip, lifestyle, fashion, food
- A person being appointed, hired, fired, resigning, winning an award
- A person's opinion, statement, speech, or interview ("X says...", "X warns...", "X calls for...")
- Earnings reports or stock prices with no product/tech substance
- Political election results, campaign news, voting
- Clickbait or listicles ("10 reasons why...", "You won't believe...")
- Crime news unrelated to cybersecurity
- Real estate, travel, health/wellness unrelated to tech

KEEP if the title suggests:
- A technical release, tool, model, API, framework, OS, or library
- A security vulnerability, breach, or incident
- A research finding with measurable results
- Infrastructure, cloud, platform, or protocol news
- AI/ML developments
- Vietnam technology, economy, or policy
- Anything that could be substantively technical even if the title is ambiguous

When in doubt, KEEP — the next stage will filter more precisely.

Titles:
{batch}

Return JSON: {{"keep": ["id1", "id2", ...]}}"""


def _title_filter_batch(client: OpenAI, articles: list[RawArticle]) -> list[str]:
    batch = [{"id": a.id, "title": a.title} for a in articles]
    prompt = _TITLE_FILTER_PROMPT.format(batch=json.dumps(batch))
    result = json.loads(_chat(client, prompt))
    return result.get("keep", [])


# ── Stage 2: Body filter ──────────────────────────────────────────────────────
# Smaller batches (25) with title + snippet. More precise, nuanced filtering.

_BODY_FILTER_PROMPT = """You are a ruthless news curator filtering articles for a senior tech professional.

REJECT any article that is primarily about:
- What a person SAID, STATED, ARGUED, CLAIMS, or BELIEVES (quotes, opinions, speeches, interviews)
- What a person IS DOING, WAS APPOINTED, HIRED, FIRED, RESIGNED, PROMOTED, AWARDED
- What a company ANNOUNCED in a press release without technical substance
- Earnings reports, stock prices, funding rounds with no product/tech substance
- Sports, entertainment, celebrity, gossip, lifestyle
- Conference roundups ("X spoke at Y about Z")
- Political commentary or opinion pieces
- Surveys, polls, predictions without hard data
- Clickbait, listicles ("10 reasons why...")
- Duplicate coverage of the same announcement

KEEP any article that is about:
- A concrete technical release: new tool, API, framework, model, OS version, library
- A security vulnerability, exploit, patch, or breach affecting real systems
- A research paper with measurable results or novel findings
- An open source project launch or major version release
- Infrastructure changes that affect how systems work (cloud, protocols, standards)
- AI/ML model releases, benchmarks, or architectural breakthroughs
- A real-world system failure, outage, or incident (impact > 1000 users)
- Regulatory or policy change with direct technical impact
- A geopolitical event with direct, immediate economic or infrastructure impact
- Vietnam-specific economic policy, infrastructure, or tech industry developments

The guiding principle: REJECT person-centric, KEEP thing-centric and impact-centric.

Articles (title + snippet):
{batch}

Return JSON: {{"keep": ["id1", "id2", ...]}}
Be aggressive — when in doubt, reject."""


def _body_filter_batch(client: OpenAI, articles: list[RawArticle]) -> list[str]:
    batch = [{"id": a.id, "title": a.title, "snippet": a.snippet[:200]} for a in articles]
    prompt = _BODY_FILTER_PROMPT.format(batch=json.dumps(batch))
    result = json.loads(_chat(client, prompt))
    return result.get("keep", [])


# ── Score ─────────────────────────────────────────────────────────────────────

def _score_batch(client: OpenAI, articles: list[RawArticle]) -> dict[str, float]:
    batch = [
        {"id": a.id, "title": a.title, "category": a.category, "snippet": a.snippet[:200]}
        for a in articles
    ]
    prompt = f"""Score each article's practical value to a senior DevOps/AI engineer. Score 0.0–1.0.

0.9–1.0: Direct action required or major capability unlocked (critical CVE, major model/tool release,
         breaking infra change, significant regulatory event with immediate impact)
0.7–0.8: High-value: new technique, solid research result, notable open source release, real incident postmortem
0.5–0.6: Moderate: useful background, minor release, incremental update worth knowing
0.3–0.4: Low: mostly noise, hype without substance, redundant coverage
0.0–0.2: Reject-level: should have been filtered (quote, opinion, fluff)

Articles:
{json.dumps(batch)}

Return JSON: {{"scores": {{"id": 0.85, ...}}}}"""

    result = json.loads(_chat(client, prompt))
    return result.get("scores", {})


# ── Cluster ───────────────────────────────────────────────────────────────────

def _cluster_articles(client: OpenAI, articles: list[RawArticle]) -> dict[str, str]:
    if len(articles) < 2:
        return {}
    batch = [{"id": a.id, "title": a.title} for a in articles]
    prompt = f"""Group articles covering the same story into clusters (min 2 articles per cluster).

Articles:
{json.dumps(batch)}

Return JSON: {{"clusters": [{{"cluster_id": "cluster-xyz", "article_ids": ["id1", "id2"]}}]}}"""

    result = json.loads(_chat(client, prompt))
    mapping: dict[str, str] = {}
    for c in result.get("clusters", []):
        cid = c.get("cluster_id", "")
        for aid in c.get("article_ids", []):
            mapping[aid] = cid
    return mapping


def _select_cluster_representatives(
    articles: list[RawArticle], cluster_map: dict[str, str], scores: dict[str, float]
) -> list[RawArticle]:
    """Keep every standalone article and the best article from each story cluster."""
    representatives: dict[str, RawArticle] = {}
    for article in articles:
        cluster_id = cluster_map.get(article.id)
        if not cluster_id:
            continue

        current = representatives.get(cluster_id)
        if current is None or (
            scores.get(article.id, 0.5), article.published_at or "", article.id
        ) > (
            scores.get(current.id, 0.5), current.published_at or "", current.id
        ):
            representatives[cluster_id] = article

    return [
        article
        for article in articles
        if not (cluster_id := cluster_map.get(article.id))
        or representatives[cluster_id].id == article.id
    ]


# ── Summarize ─────────────────────────────────────────────────────────────────

def _summarize_clusters(
    client: OpenAI, clusters_map: dict[str, list[RawArticle]]
) -> dict[str, dict]:
    if not clusters_map:
        return {}
    batch = [
        {
            "cluster_id": cid,
            "articles": [{"title": a.title, "snippet": a.snippet[:150]} for a in arts],
        }
        for cid, arts in clusters_map.items()
    ]
    prompt = f"""For each cluster write:
- topic: concise label (5–10 words, in English)
- summary: 1–2 sentences IN VIETNAMESE capturing the key facts and significance

Clusters:
{json.dumps(batch)}

Return JSON: {{"summaries": {{"cluster_id": {{"topic": "...", "summary": "..."}}}}}}"""

    result = json.loads(_chat(client, prompt))
    return result.get("summaries", {})


def _summarize_standalone(client: OpenAI, articles: list[RawArticle]) -> dict[str, str]:
    if not articles:
        return {}
    batch = [{"id": a.id, "title": a.title, "snippet": a.snippet[:300]} for a in articles]
    prompt = f"""Write a 1–2 sentence summary IN VIETNAMESE for each article.
Capture what happened and why it matters to a senior tech/DevOps professional.
Be concise and direct.

Articles:
{json.dumps(batch)}

Return JSON: {{"summaries": {{"id": "tóm tắt tiếng Việt..."}}}}"""

    result = json.loads(_chat(client, prompt))
    return result.get("summaries", {})


# ── Daily Recap ───────────────────────────────────────────────────────────────

def _generate_daily_recap(client: OpenAI, articles: list[ProcessedArticle]) -> DailyRecap:
    top = sorted(articles, key=lambda a: a.score, reverse=True)[:30]
    batch = [
        {"title": a.title, "category": a.category, "summary": a.summary, "score": a.score}
        for a in top
    ]
    prompt = f"""Bạn là biên tập viên của một bản tin công nghệ tiếng Việt dành cho kỹ sư cao cấp.
Dựa trên các bài báo quan trọng nhất hôm nay, hãy viết phần tổng kết cuối ngày gồm 4 phần:

1. global_analysis: Phân tích 2–3 đoạn về bức tranh công nghệ toàn cầu hôm nay — xu hướng chính, sự kiện nổi bật, và ý nghĩa với ngành AI/DevOps/Security.

2. vietnam_analysis: Phân tích 1–2 đoạn về tin tức Việt Nam — đặt trong bối cảnh khu vực, chỉ ra điểm mạnh/yếu, cơ hội/thách thức.

3. watch_list: 1 đoạn ngắn về xu hướng/kỹ năng đáng đầu tư — lời khuyên cá nhân cho kỹ sư DevOps/AI Việt Nam.

4. full_summary: Đoạn văn tổng hợp 200–300 từ, kể lại toàn bộ ngày như narrative liền mạch — bắt đầu từ sự kiện quan trọng nhất, liên kết các chủ đề, kết thúc bằng nhận định tổng thể.

Bài báo hôm nay:
{json.dumps(batch, ensure_ascii=False)}

Return JSON:
{{
  "global_analysis": "...",
  "vietnam_analysis": "...",
  "watch_list": "...",
  "full_summary": "..."
}}"""

    result = json.loads(_chat(client, prompt))
    return DailyRecap(
        global_analysis=result.get("global_analysis", ""),
        vietnam_analysis=result.get("vietnam_analysis", ""),
        watch_list=result.get("watch_list", ""),
        full_summary=result.get("full_summary", ""),
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_parallel(fn, client: OpenAI, batches: list, label: str) -> list:
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(fn, client, b): i for i, b in enumerate(batches)}
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as exc:
                log.warning("%s batch failed: %s", label, exc)
    return results


# ── Main process ──────────────────────────────────────────────────────────────

def process(raw_articles: list[RawArticle]) -> ProcessedOutput:
    if not raw_articles:
        return ProcessedOutput(articles=[], clusters=[])

    client = _client()
    log.info("Pipeline: %d raw articles, model=%s, workers=%d",
             len(raw_articles), config.VEEN_AI_MODEL, MAX_WORKERS)

    # ── Stage 1: Title filter (parallel, batch=50) ────────────────────────────
    title_batches = [
        raw_articles[i : i + config.TITLE_BATCH_SIZE]
        for i in range(0, len(raw_articles), config.TITLE_BATCH_SIZE)
    ]
    log.info("Stage 1 — title filter: %d articles in %d batches", len(raw_articles), len(title_batches))
    title_keep: set[str] = set()
    for ids in _run_parallel(_title_filter_batch, client, title_batches, "title-filter"):
        title_keep.update(ids)

    after_title = [a for a in raw_articles if a.id in title_keep]
    log.info("After title filter: %d articles (dropped %d)", len(after_title), len(raw_articles) - len(after_title))

    # ── Stage 2: Body filter (parallel, batch=25) ─────────────────────────────
    body_batches = [
        after_title[i : i + config.BATCH_SIZE]
        for i in range(0, len(after_title), config.BATCH_SIZE)
    ]
    log.info("Stage 2 — body filter: %d articles in %d batches", len(after_title), len(body_batches))
    body_keep: set[str] = set()
    for ids in _run_parallel(_body_filter_batch, client, body_batches, "body-filter"):
        body_keep.update(ids)

    filtered = [a for a in after_title if a.id in body_keep]
    log.info("After body filter: %d articles (dropped %d)", len(filtered), len(after_title) - len(filtered))

    # ── Score (parallel, batch=25) ────────────────────────────────────────────
    score_batches = [
        filtered[i : i + config.BATCH_SIZE]
        for i in range(0, len(filtered), config.BATCH_SIZE)
    ]
    log.info("Scoring: %d articles in %d batches", len(filtered), len(score_batches))
    scores: dict[str, float] = {}
    for batch_scores in _run_parallel(_score_batch, client, score_batches, "score"):
        scores.update(batch_scores)

    scored = [a for a in filtered if scores.get(a.id, 0.5) >= config.SCORE_THRESHOLD]
    log.info("After score threshold (≥%.1f): %d articles", config.SCORE_THRESHOLD, len(scored))

    # ── Cluster ───────────────────────────────────────────────────────────────
    cluster_map = _cluster_articles(client, scored)

    clusters_by_id: dict[str, list[RawArticle]] = {}
    for a in scored:
        cid = cluster_map.get(a.id)
        if cid:
            clusters_by_id.setdefault(cid, []).append(a)

    published = _select_cluster_representatives(scored, cluster_map, scores)
    representative_ids = {
        cluster_map[a.id]: a.id
        for a in published
        if cluster_map.get(a.id)
    }
    log.info(
        "After cluster deduplication: %d articles (dropped %d duplicate coverage records)",
        len(published),
        len(scored) - len(published),
    )

    standalone = [a for a in scored if a.id not in cluster_map]

    # ── Summarize clusters + standalone in parallel ───────────────────────────
    standalone_batches = [
        standalone[i : i + 20]
        for i in range(0, min(len(standalone), 60), 20)
    ]

    cluster_summaries: dict[str, dict] = {}
    standalone_summaries: dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=2) as pool:
        fut_clusters = pool.submit(_summarize_clusters, client, clusters_by_id)
        fut_standalone_list = [
            pool.submit(_summarize_standalone, client, batch)
            for batch in standalone_batches
        ]

        try:
            cluster_summaries = fut_clusters.result()
        except Exception as exc:
            log.warning("Cluster summarization failed: %s", exc)

        for fut in as_completed(fut_standalone_list):
            try:
                standalone_summaries.update(fut.result())
            except Exception as exc:
                log.warning("Standalone summarization batch failed: %s", exc)

    # ── Build output ──────────────────────────────────────────────────────────
    processed: list[ProcessedArticle] = []
    for a in published:
        cid = cluster_map.get(a.id)
        summary = (
            cluster_summaries[cid].get("summary", "") if cid and cid in cluster_summaries
            else standalone_summaries.get(a.id, "")
        )
        processed.append(ProcessedArticle(
            id=a.id,
            title=a.title,
            url=a.url,
            source=a.source,
            published_at=a.published_at,
            category=a.category,
            summary=summary,
            score=round(scores.get(a.id, 0.5), 3),
            cluster_id=cid,
        ))

    clusters: list[Cluster] = []
    for cid, arts in clusters_by_id.items():
        info = cluster_summaries.get(cid, {})
        clusters.append(Cluster(
            id=cid,
            topic=info.get("topic", ""),
            summary=info.get("summary", ""),
            article_ids=[a.id for a in arts],
            article_count=len(arts),
            representative_id=representative_ids[cid],
        ))

    # ── Daily Recap ───────────────────────────────────────────────────────────
    daily_recap = None
    if processed:
        try:
            daily_recap = _generate_daily_recap(client, processed)
            log.info("Daily recap generated")
        except Exception as exc:
            log.warning("Failed to generate daily recap: %s", exc)

    log.info("Pipeline complete: %d articles, %d clusters", len(processed), len(clusters))
    return ProcessedOutput(articles=processed, clusters=clusters, daily_recap=daily_recap)
