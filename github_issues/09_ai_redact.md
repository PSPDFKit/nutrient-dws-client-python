# Feature: AI-Powered Redaction Method

## Summary
Implement `ai_redact()` to use Nutrient's AI capabilities for automatic detection and redaction of sensitive information.

## Proposed Implementation
```python
def ai_redact(
    self,
    input_file: FileInput,
    output_path: Optional[str] = None,
    sensitivity_level: Literal["low", "medium", "high"] = "medium",
    entity_types: Optional[List[str]] = None,  # ["email", "ssn", "phone", etc.]
    review_mode: bool = False,  # Create redactions without applying
    confidence_threshold: float = 0.8,
) -> Optional[bytes]:
```

## Benefits
- Automated GDPR/CCPA compliance
- Reduce manual review time by 90%
- Consistent redaction across documents
- Multiple entity type detection
- Configurable sensitivity levels
- Review mode for human verification

## Implementation Details
- Use dedicated `/ai/redact` endpoint
- Different from create_redactions (rule-based)
- Support confidence thresholds
- Allow entity type filtering
- Option to review before applying

## Testing Requirements
- [ ] Test sensitivity levels (low/medium/high)
- [ ] Test specific entity detection
- [ ] Test review mode
- [ ] Test confidence thresholds
- [ ] Compare with manual redaction
- [ ] Test on various document types

## OpenAPI Reference
- Endpoint: `/ai/redact`
- Separate from Build API
- AI-powered detection
- Returns processed document

## Use Case Example
```python
# Automatic GDPR compliance
gdpr_safe = client.ai_redact(
    "customer_data.pdf",
    entity_types=["email", "phone", "name", "address"],
    sensitivity_level="high"
)

# Review before applying
review_pdf = client.ai_redact(
    "contract.pdf",
    entity_types=["ssn", "bank_account", "credit_card"],
    review_mode=True,  # Creates redaction annotations only
    confidence_threshold=0.9
)

# Then manually review and apply
final = client.apply_redactions(review_pdf)
```

## Supported Entity Types
- Personal: name, email, phone, address
- Financial: ssn, credit_card, bank_account, routing_number
- Medical: medical_record, diagnosis, prescription
- Custom: (API may support additional types)

## Priority
🟠 Priority 4 - Advanced feature

## Labels
- feature
- ai
- redaction
- compliance
- gdpr
- openapi-compliance