# Bill Explanation Example

This example shows how PetVault explains a veterinary bill.

## Input
- `request.txt`: User request to explain a bill
- `sample_invoice_transcription.md`: Synthetic invoice transcription

## Expected Output
- `report.md`: Bill explanation report with cost categories, high-value items, and questions for the clinic

## Workflow
1. Dispatch detects bill-related request → routes to report pipeline
2. Material organizer classifies as invoice/bill
3. Bill analysis extracts line items and totals
4. Report composer creates structured explanation
5. Sanitizer removes any internal terms
6. Output: user-facing report.md
