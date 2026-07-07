from __future__ import annotations

from pathlib import Path
import argparse
import json
import re
import sqlite3


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_ARTICLES_DIR = SKILL_DIR / "kb" / "articles"
DEFAULT_INDEX = SKILL_DIR / "kb" / "index" / "kb.sqlite"

KNOWN_TERMS = [
    "理赔", "报销", "材料", "保单", "保险", "等待期", "既往症",
    "账单", "发票", "费用", "付款", "折扣", "退款", "检查", "化验",
    "处方", "营养", "处方粮", "中毒", "毒物", "急诊", "百合", "巧克力",
]


def parse_scalar(value: str):
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("\"'") for item in inner.split(",")]
    return value.strip("\"'")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) != 3:
        return {}, text
    metadata: dict[str, object] = {}
    current_key: str | None = None
    for raw_line in parts[1].splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith("- ") and current_key:
            metadata.setdefault(current_key, [])
            if isinstance(metadata[current_key], list):
                metadata[current_key].append(parse_scalar(line.lstrip()[2:]))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        current_key = key.strip()
        metadata[current_key] = parse_scalar(value)
    return metadata, parts[2].strip()


def parse_article(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(text)
    article_id = metadata.get("id") or metadata.get("article_id") or path.stem
    domain = metadata.get("domain") or metadata.get("topic") or "general"
    sources = metadata.get("sources") or metadata.get("source_url") or []
    if isinstance(sources, str):
        sources = [sources] if sources else []
    return {
        "article_id": str(article_id),
        "id": str(article_id),
        "title": str(metadata.get("title") or article_id),
        "domain": str(domain),
        "topic": str(domain),
        "jurisdiction": str(metadata.get("jurisdiction") or "global"),
        "language": str(metadata.get("language") or "zh"),
        "risk_level": str(metadata.get("risk_level") or "medium"),
        "source_ids": sources,
        "source_url": str(metadata.get("source_url") or ""),
        "updated_at": str(metadata.get("updated_at") or metadata.get("last_reviewed") or ""),
        "path": str(path),
        "body": body,
    }


def load_articles(kb_dir: Path) -> list[dict]:
    if not kb_dir.exists():
        return []
    return [parse_article(path) for path in sorted(kb_dir.rglob("*.md"))]


def query_terms(query: str) -> list[str]:
    terms = [term.lower() for term in re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]{1,}", query)]
    terms.extend(term for term in KNOWN_TERMS if term in query)
    seen = []
    for term in terms:
        if term and term not in seen:
            seen.append(term)
    return seen or [query.lower()]


def score_article(article: dict, terms: list[str]) -> int:
    haystack = f"{article['title']}\n{article['domain']}\n{article['body']}".lower()
    score = 0
    for term in terms:
        score += haystack.count(term.lower()) * 3
        if term.lower() in article["title"].lower():
            score += 4
        if term.lower() == article["domain"].lower():
            score += 2
    return score


def snippet_for(article: dict, terms: list[str], max_chars: int = 180) -> str:
    body = article["body"].replace("\n", " ")
    lower_body = body.lower()
    positions = [lower_body.find(term.lower()) for term in terms if lower_body.find(term.lower()) >= 0]
    start = max(min(positions) - 40, 0) if positions else 0
    snippet = body[start : start + max_chars].strip()
    return snippet + ("..." if start + max_chars < len(body) else "")


def article_matches_filters(article: dict, domain: str | None, jurisdiction: str | None, language: str | None) -> bool:
    if domain and article["domain"] != domain:
        return False
    if jurisdiction and article["jurisdiction"] not in {jurisdiction, "global"}:
        return False
    if language and article["language"] != language:
        return False
    return True


def search_markdown(query: str, kb_dir: Path, limit: int, domain=None, jurisdiction=None, language=None) -> dict:
    terms = query_terms(query)
    ranked = []
    for article in load_articles(kb_dir):
        if not article_matches_filters(article, domain, jurisdiction, language):
            continue
        score = score_article(article, terms)
        if score <= 0:
            continue
        result = {key: value for key, value in article.items() if key != "body"}
        result["score"] = score
        result["snippet"] = snippet_for(article, terms)
        ranked.append(result)
    ranked.sort(key=lambda item: (-item["score"], item["article_id"]))
    return {"query": query, "terms": terms, "matches": ranked[:limit]}


def search_sqlite(index_path: Path, query: str, limit: int, domain=None, jurisdiction=None, language=None) -> dict | None:
    if not index_path.exists():
        return None
    where = ["kb_fts MATCH ?"]
    params: list[object] = [query]
    if domain:
        where.append("domain = ?")
        params.append(domain)
    if jurisdiction:
        where.append("(jurisdiction = ? OR jurisdiction = 'global')")
        params.append(jurisdiction)
    if language:
        where.append("language = ?")
        params.append(language)
    params.append(limit)
    sql = f"""
        SELECT id, title, domain, jurisdiction, language, sources,
               snippet(kb_fts, 5, '', '', '...', 24) AS snippet
        FROM kb_fts
        WHERE {' AND '.join(where)}
        LIMIT ?
    """
    try:
        with sqlite3.connect(index_path) as conn:
            rows = conn.execute(sql, params).fetchall()
    except sqlite3.Error:
        return None
    return {
        "query": query,
        "terms": query_terms(query),
        "matches": [
            {
                "article_id": row[0],
                "id": row[0],
                "title": row[1],
                "domain": row[2],
                "jurisdiction": row[3],
                "language": row[4],
                "source_ids": json.loads(row[5] or "[]"),
                "snippet": row[6],
            }
            for row in rows
        ],
    }


def search(query: str, kb_dir: Path, limit: int, domain=None, jurisdiction=None, language=None, index_path: Path | None = None) -> dict:
    if index_path:
        indexed = search_sqlite(index_path, query, limit, domain, jurisdiction, language)
        if indexed is not None and indexed["matches"]:
            return indexed
    return search_markdown(query, kb_dir, limit, domain, jurisdiction, language)


def print_text(payload: dict) -> None:
    if not payload["matches"]:
        print(f"No local KB matches for: {payload['query']}")
        return
    for match in payload["matches"]:
        print(f"id: {match['id']}")
        print(f"title: {match['title']}")
        print(f"domain: {match['domain']}")
        print(f"jurisdiction: {match['jurisdiction']}")
        print(f"language: {match['language']}")
        print(f"source ids: {', '.join(match.get('source_ids') or [])}")
        print(f"snippet: {match.get('snippet', '')}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Search the local PetVault knowledge hub.")
    parser.add_argument("query")
    parser.add_argument("--kb", type=Path, default=DEFAULT_ARTICLES_DIR)
    parser.add_argument("--index", type=Path, default=None)
    parser.add_argument("--domain")
    parser.add_argument("--jurisdiction")
    parser.add_argument("--language")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()
    index_path = args.index if args.index is not None else (DEFAULT_INDEX if DEFAULT_INDEX.exists() else None)
    payload = search(args.query, args.kb, args.limit, args.domain, args.jurisdiction, args.language, index_path)
    if args.format == "text":
        print_text(payload)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
