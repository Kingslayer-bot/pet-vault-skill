# Emergency Guardrail Example

This example shows how PetVault detects emergency symptoms and returns urgent safety guidance.

## Input
- `request.txt`: User describing emergency symptoms

## Expected Output
- `response.md`: Urgent safety response with emergency contacts

## Workflow
1. Dispatch detects emergency keywords → routes to emergency response
2. Returns immediate safety guidance
3. Does NOT proceed to report or KB query
4. User must confirm emergency resolved before continuing
