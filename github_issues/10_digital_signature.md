# Feature: Digital Signature Method

## Summary
Implement `sign_pdf()` to apply digital signatures to PDFs with optional visual representation.

## Proposed Implementation
```python
def sign_pdf(
    self,
    input_file: FileInput,
    certificate_file: FileInput,
    private_key_file: FileInput,
    output_path: Optional[str] = None,
    password: Optional[str] = None,
    reason: Optional[str] = None,
    location: Optional[str] = None,
    contact_info: Optional[str] = None,
    # Visual signature
    show_signature: bool = True,
    signature_image: Optional[FileInput] = None,
    page_index: int = 0,
    position: Optional[Dict[str, int]] = None,  # {"x": 100, "y": 100, "width": 200, "height": 50}
    signature_type: Literal["cades", "pades"] = "pades",
) -> Optional[bytes]:
```

## Benefits
- Legal compliance and non-repudiation
- Document integrity verification
- Visual signature representation
- Support for CAdES and PAdES standards
- Timestamp support
- Certificate chain validation

## Implementation Details
- Use dedicated `/sign` endpoint
- Handle certificate and key file uploads
- Support PKCS#12 and PEM formats
- Optional visual signature placement
- Configurable signature standards

## Testing Requirements
- [ ] Test with PKCS#12 certificates
- [ ] Test with PEM certificates
- [ ] Test visual signature placement
- [ ] Test invisible signatures
- [ ] Test signature validation
- [ ] Test password-protected certificates
- [ ] Test CAdES vs PAdES formats

## OpenAPI Reference
- Endpoint: `/sign`
- Signature types: cades, pades
- Visual appearance options
- Position configuration

## Use Case Example
```python
# Simple digital signature
signed_pdf = client.sign_pdf(
    "contract.pdf",
    certificate_file="certificate.p12",
    private_key_file="private_key.pem",
    password="cert_password",
    reason="Agreement confirmation",
    location="New York, USA"
)

# Visual signature with image
signed_pdf = client.sign_pdf(
    "agreement.pdf",
    certificate_file="certificate.p12",
    private_key_file="private_key.pem",
    signature_image="signature.png",
    page_index=2,  # Third page
    position={"x": 400, "y": 100, "width": 150, "height": 50}
)

# PAdES Long-Term Validation
ltv_signed = client.sign_pdf(
    "document.pdf",
    certificate_file="certificate.p12",
    private_key_file="private_key.pem",
    signature_type="pades",  # For long-term validation
    show_signature=False  # Invisible signature
)
```

## Signature Standards
- **CAdES**: CMS Advanced Electronic Signatures
- **PAdES**: PDF Advanced Electronic Signatures (recommended)
  - Better for long-term validation
  - Embedded in PDF structure

## Priority
🟠 Priority 4 - Advanced feature

## Labels
- feature
- security
- digital-signature
- compliance
- openapi-compliance