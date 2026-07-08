## Summary

Brief description of changes.

## Type

- [ ] Bug fix
- [ ] Feature
- [ ] KB content
- [ ] Documentation
- [ ] CI/infrastructure

## Test Plan

```bash
python -m unittest discover -s pet-vault-skill/tests -p "test_*.py" -v
```

Expected: All tests pass, count >= current baseline.

## Checklist

- [ ] Tests pass locally
- [ ] No internal terms in user-facing output
- [ ] KB articles have all 13 required frontmatter fields
- [ ] Sources referenced by articles exist in sources.yaml
- [ ] No dangerous content (diagnosis, guarantees, brand recommendations)
