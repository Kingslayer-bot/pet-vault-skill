# PetVault Skill Examples

This directory contains synthetic examples showing how the PetVault skill handles common user tasks.

## Running Examples

### Bill Explanation
```bash
python scripts/run_pipeline.py \
  --input examples/bill_explain/input \
  --output /tmp/petvault_bill_explain \
  --vault /tmp/petvault_vault \
  --request "帮我解释这张账单" \
  --pet-name Mimi \
  --skip-pdf-compile
```

### Knowledge Query
```bash
python scripts/query_knowledge_base.py "理赔需要哪些材料" --limit 3
```

### Emergency Detection
```bash
python scripts/petvault_dispatch.py --request "狗吃了巧克力怎么办"
```

## What's User-Visible vs Internal

| Artifact | User-Visible? | Description |
|----------|--------------|-------------|
| `report.md` | ✅ Yes | Main report content |
| `report.pdf` | ✅ Yes | PDF version of report |
| `user_manifest.json` | ✅ Yes | User-safe metadata |
| `manifest.json` | ❌ Internal | Contains routing reasons |
| `qa_result.json` | ❌ Internal | QA check details |
| `build.log` | ❌ Internal | PDF compilation log |
| `materials_index.json` | ❌ Internal | Material classification |

## Safety Boundaries

- No diagnosis replacement
- No legal judgment
- No insurance payout promise
- No hospital fraud accusation
- No internal terms in user output
