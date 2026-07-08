# Insurance Boundary Example

This example shows how PetVault handles requests that cross insurance/medical boundaries.

## Input
- `request.txt`: User asking for insurance guarantee

## Expected Output
- `response.md`: Safe completion explaining what PetVault can and cannot do

## Workflow
1. Dispatch detects forbidden request (insurance guarantee) → routes to forbidden response
2. Returns safe completion explaining boundaries
3. Does NOT proceed to report generation
4. Explains what PetVault can help with instead
