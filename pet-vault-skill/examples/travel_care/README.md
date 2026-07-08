# Travel Care Example

This example shows how PetVault provides travel care checklist for pet owners.

## Input
- `request.txt`: User asking about pet travel requirements

## Expected Output
- `response.md`: Travel care checklist from knowledge base

## Workflow
1. Dispatch detects knowledge question → routes to KB query
2. KB search finds travel-related articles
3. Returns checklist with requirements
4. No report generated, no vault update
