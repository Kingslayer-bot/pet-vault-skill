from __future__ import annotations

from pathlib import Path
import argparse
import json
import sqlite3
import sys

from query_knowledge_base import load_articles


REQUIRED_FIELDS = {"id", "title", "domain", "jurisdiction", "language"}


def skill_dir_from_arg(path: Path) -> Path:
    path = path.resolve()
    if (path / "kb").exists() and (path / "scripts").exists():
        return path
    nested = path / "pet-vault-skill"
    if (nested / "kb").exists() and (nested / "scripts").exists():
        return nested
    raise SystemExit(f"Cannot find skill directory from {path}")


def build_index(skill_dir: Path) -> Path:
    articles_dir = skill_dir / "kb" / "articles"
    index_dir = skill_dir / "kb" / "index"
    index_dir.mkdir(parents=True, exist_ok=True)
    index_path = index_dir / "kb.sqlite"
    articles = load_articles(articles_dir)
    errors = []
    for article in articles:
        missing = [field for field in REQUIRED_FIELDS if not article.get(field)]
        if missing:
            errors.append(f"{article.get('path')}: missing {', '.join(missing)}")
    if errors:
        raise SystemExit("\n".join(errors))
    with sqlite3.connect(index_path) as conn:
        conn.execute("DROP TABLE IF EXISTS kb_fts")
        conn.execute(
            """
            CREATE VIRTUAL TABLE kb_fts USING fts5(
                id UNINDEXED,
                title,
                domain UNINDEXED,
                jurisdiction UNINDEXED,
                language UNINDEXED,
                body,
                sources UNINDEXED
            )
            """
        )
        for article in articles:
            conn.execute(
                "INSERT INTO kb_fts(id, title, domain, jurisdiction, language, body, sources) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    article["id"],
                    article["title"],
                    article["domain"],
                    article["jurisdiction"],
                    article["language"],
                    article["body"],
                    json.dumps(article.get("source_ids") or [], ensure_ascii=False),
                ),
            )
        conn.commit()
    return index_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PetVault local KB SQLite FTS index.")
    parser.add_argument("skill_dir", type=Path, nargs="?", default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    skill_dir = skill_dir_from_arg(args.skill_dir)
    index_path = build_index(skill_dir)
    print(f"Built KB index: {index_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
