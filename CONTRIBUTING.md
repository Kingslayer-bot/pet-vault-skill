# Contributing to PetVault AI

## How to Contribute

### Reporting Issues

- Use GitHub Issues to report bugs or request features
- Include steps to reproduce for bug reports
- For KB content issues, specify the article ID and the problem

### Knowledge Base Contributions

KB articles follow a strict schema. To add or modify articles:

1. Read `references/local_knowledge_base.md` for KB routing and storage guidance
2. Use the article template from existing articles in `kb/articles/`
3. Every article must have all 13 required frontmatter fields
4. Sources must exist in `kb/sources.yaml` before referencing them
5. Run `python pet-vault-skill/scripts/validate_kb.py pet-vault-skill` to verify

### Code Contributions

1. Fork the repository
2. Create a feature branch from `main`
3. Write tests for new functionality
4. Run `python -m unittest discover -s pet-vault-skill/tests -p "test_*.py" -v`
5. Submit a pull request

### Safety Rules

- Never add content that diagnoses, prescribes, or replaces veterinary judgment
- Never promise insurance coverage or claim outcomes
- Never recommend specific brands or products
- Always include `forbidden_outputs` in article frontmatter
- Internal terms (routing, dispatch, confidence, etc.) must never appear in user-facing output

## Development Setup

```bash
pip install pyyaml
python -m unittest discover -s pet-vault-skill/tests -p "test_*.py" -v
```

## Code Style

- Python 3.11+
- Google-style docstrings
- Type annotations on public functions
- No unused imports
