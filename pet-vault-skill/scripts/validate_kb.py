from __future__ import annotations

from pathlib import Path
import argparse
import sys

from query_knowledge_base import load_articles, parse_frontmatter


REQUIRED_FRONTMATTER = {
    "id", "title", "domain", "jurisdiction", "language", "species",
    "source_tier", "risk_level", "allowed_outputs", "forbidden_outputs",
    "sources", "last_reviewed", "expires_at",
}


def skill_dir_from_arg(path: Path) -> Path:
    path = path.resolve()
    if (path / "kb").exists() and (path / "scripts").exists():
        return path
    nested = path / "pet-vault-skill"
    if (nested / "kb").exists() and (nested / "scripts").exists():
        return nested
    raise SystemExit(f"Cannot find skill directory from {path}")


def load_source_ids(sources_path: Path) -> set[str]:
    ids = set()
    for line in sources_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- id:") or stripped.startswith("id:"):
            ids.add(stripped.split(":", 1)[1].strip().strip("\"'"))
    return ids


def validate(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    required_paths = [
        "kb/sources.yaml", "kb/ontology.yaml",
        "kb/rules/routing.yaml", "kb/rules/pdf_policy.yaml",
        "kb/rules/billing_validation.yaml", "kb/rules/insurance_guardrails.yaml",
        "kb/rules/medical_safety.yaml", "kb/rules/privacy.yaml",
    ]
    for rel in required_paths:
        if not (skill_dir / rel).exists():
            errors.append(f"Missing required KB file: {rel}")
    source_ids = load_source_ids(skill_dir / "kb" / "sources.yaml") if (skill_dir / "kb" / "sources.yaml").exists() else set()
    cards = []
    for path in sorted((skill_dir / "kb" / "articles").rglob("*.md")):
        metadata, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
        if "id" not in metadata and "article_id" in metadata:
            continue
        cards.append((path, metadata))
        missing = sorted(REQUIRED_FRONTMATTER - set(metadata))
        if missing:
            errors.append(f"{path}: missing frontmatter fields: {', '.join(missing)}")
        forbidden = metadata.get("forbidden_outputs") or []
        if not forbidden:
            errors.append(f"{path}: forbidden_outputs must not be empty")
        if metadata.get("risk_level") == "high" and not forbidden:
            errors.append(f"{path}: high risk cards require forbidden_outputs")
        if not metadata.get("expires_at") and not metadata.get("last_reviewed"):
            errors.append(f"{path}: expires_at or last_reviewed required")
        for source_id in metadata.get("sources") or []:
            if source_id not in source_ids:
                errors.append(f"{path}: unknown source id {source_id}")
        text = path.read_text(encoding="utf-8")
        if metadata.get("domain") == "insurance":
            for phrase in ["一定能赔", "一定不能赔", "保险公司违法"]:
                if phrase in text:
                    errors.append(f"{path}: forbidden insurance phrase {phrase}")
        if metadata.get("domain") == "safety":
            for phrase in ["观察一下", "问题不大"]:
                if phrase in text:
                    errors.append(f"{path}: forbidden safety phrase {phrase}")
    domains = {metadata.get("domain") for _path, metadata in cards}
    jurisdictions = {metadata.get("jurisdiction") for _path, metadata in cards}
    for domain in ["billing", "insurance", "medical", "safety", "jurisdiction"]:
        if domain not in domains:
            errors.append(f"Missing P0 KB domain card: {domain}")
    for jurisdiction in ["US", "CN"]:
        if jurisdiction not in jurisdictions:
            errors.append(f"Missing P0 jurisdiction card: {jurisdiction}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PetVault local KB cards and sources.")
    parser.add_argument("skill_dir", type=Path, nargs="?", default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    skill_dir = skill_dir_from_arg(args.skill_dir)
    errors = validate(skill_dir)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PetVault local KB validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
