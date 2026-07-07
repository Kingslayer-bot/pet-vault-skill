from pathlib import Path
import argparse
import subprocess
import sys


REQUIRED_FILES = [
    "SKILL.md",
    "agents/openai.yaml",
    "scripts/run_pipeline.py",
    "scripts/petvault_core.py",
    "scripts/query_knowledge_base.py",
    "templates/styles.tex.j2",
    "templates/report_bill_explain.tex.j2",
    "schemas/material_index.schema.json",
    "schemas/report_manifest.schema.json",
    "schemas/qa_result.schema.json",
    "kb/articles/claim-packet-us.md",
]


def validate_skill(skill_dir: Path) -> list[str]:
    errors = []
    if not skill_dir.exists() or not skill_dir.is_dir():
        return [f"Skill directory not found: {skill_dir}"]

    for rel_path in REQUIRED_FILES:
        if not (skill_dir / rel_path).exists():
            errors.append(f"Missing required file: {rel_path}")

    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        text = skill_md.read_text(encoding="utf-8")
        if not text.startswith("---"):
            errors.append("SKILL.md must start with YAML frontmatter.")
        if "name: pet-vault-skill" not in text:
            errors.append("SKILL.md frontmatter must include name: pet-vault-skill.")
        if "description:" not in text:
            errors.append("SKILL.md frontmatter must include description.")
        if "TODO" in text:
            errors.append("SKILL.md must not contain TODO placeholders.")

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if openai_yaml.exists():
        yaml_text = openai_yaml.read_text(encoding="utf-8")
        if "$pet-vault-skill" not in yaml_text:
            errors.append("agents/openai.yaml default_prompt must mention $pet-vault-skill.")

    run_pipeline = skill_dir / "scripts" / "run_pipeline.py"
    if run_pipeline.exists():
        result = subprocess.run(
            [sys.executable, str(run_pipeline), "--help"],
            cwd=skill_dir.parent,
            text=True,
            capture_output=True,
            timeout=20,
        )
        if result.returncode != 0:
            errors.append("scripts/run_pipeline.py --help failed.")
        elif "--request" not in result.stdout or "--pdf-policy" not in result.stdout:
            errors.append("run_pipeline.py help must expose --request and --pdf-policy.")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the pet-vault-skill package.")
    parser.add_argument("skill_dir", type=Path)
    args = parser.parse_args()
    errors = validate_skill(args.skill_dir)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("pet-vault-skill validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
