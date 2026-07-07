from __future__ import annotations

from pathlib import Path
import argparse
import json
import re


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_KB_DIR = SKILL_DIR / "kb" / "articles"

KNOWN_TERMS = [
    "理赔",
    "报销",
    "材料",
    "保单",
    "保险",
    "等待期",
    "既往症",
    "账单",
    "发票",
    "费用",
    "付款",
    "检查",
    "化验",
    "处方",
    "营养",
    "处方粮",
    "中毒",
    "毒物",
    "急诊",
]


def parse_article(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    metadata: dict[str, str] = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            _prefix, frontmatter, body = parts
            for raw_line in frontmatter.splitlines():
                if ":" not in raw_line:
                    continue
                key, value = raw_line.split(":", 1)
                metadata[key.strip()] = value.strip().strip('"')
    article_id = metadata.get("article_id") or path.stem
    title = metadata.get("title") or article_id
    return {
        "article_id": article_id,
        "title": title,
        "topic": metadata.get("topic", "general"),
        "jurisdiction": metadata.get("jurisdiction", "general"),
        "risk_level": metadata.get("risk_level", "medium"),
        "source_url": metadata.get("source_url", ""),
        "updated_at": metadata.get("updated_at", ""),
        "path": str(path),
        "body": body.strip(),
    }


def load_articles(kb_dir: Path) -> list[dict]:
    if not kb_dir.exists():
        return []
    return [parse_article(path) for path in sorted(kb_dir.glob("*.md"))]


def query_terms(query: str) -> list[str]:
    terms = [term.lower() for term in re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]{1,}", query)]
    terms.extend(term for term in KNOWN_TERMS if term in query)
    seen = []
    for term in terms:
        if term and term not in seen:
            seen.append(term)
    return seen or [query.lower()]


def score_article(article: dict, terms: list[str]) -> int:
    haystack = f"{article['title']}\n{article['topic']}\n{article['body']}".lower()
    score = 0
    for term in terms:
        score += haystack.count(term.lower()) * 3
        if term.lower() in article["title"].lower():
            score += 4
        if term.lower() == article["topic"].lower():
            score += 2
    return score


def snippet_for(article: dict, terms: list[str], max_chars: int = 180) -> str:
    body = article["body"].replace("\n", " ")
    lower_body = body.lower()
    positions = [lower_body.find(term.lower()) for term in terms if lower_body.find(term.lower()) >= 0]
    start = max(min(positions) - 40, 0) if positions else 0
    snippet = body[start : start + max_chars].strip()
    return snippet + ("..." if start + max_chars < len(body) else "")


def search(query: str, kb_dir: Path, limit: int) -> dict:
    terms = query_terms(query)
    ranked = []
    for article in load_articles(kb_dir):
        score = score_article(article, terms)
        if score <= 0:
            continue
        result = {key: value for key, value in article.items() if key != "body"}
        result["score"] = score
        result["snippet"] = snippet_for(article, terms)
        ranked.append(result)
    ranked.sort(key=lambda item: (-item["score"], item["article_id"]))
    return {
        "query": query,
        "terms": terms,
        "matches": ranked[:limit],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Search the local PetVault knowledge base.")
    parser.add_argument("query")
    parser.add_argument("--kb", type=Path, default=DEFAULT_KB_DIR)
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(search(args.query, args.kb, args.limit), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
