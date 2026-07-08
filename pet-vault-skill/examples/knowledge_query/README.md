# Knowledge Query Example

This example shows how PetVault answers a knowledge-only question without generating a report.

## Input
- `request.txt`: User question about pet insurance

## Expected Output
- `answer.md`: Brief answer from local knowledge base

## Workflow
1. Dispatch detects knowledge-only question → routes to KB query
2. KB search finds relevant articles
3. Returns concise answer with article references
4. No report generated, no vault update
