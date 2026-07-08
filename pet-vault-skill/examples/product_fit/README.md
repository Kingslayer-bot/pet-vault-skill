# Product Fit Example

This example shows how PetVault answers product fit questions from knowledge base.

## Input
- `request.txt`: User asking about pet food recommendations

## Expected Output
- `response.md`: Product fit guidance from knowledge base

## Workflow
1. Dispatch detects knowledge question → routes to KB query
2. KB search finds product-related articles
3. Returns guidance with recommendations
4. No report generated, no vault update
