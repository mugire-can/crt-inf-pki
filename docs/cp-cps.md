# Certification Practice Statement (Mini CP/CPS)
*Public Key Infrastructure (PKI) - Academic Project*

---

## 1. Introduction and Scope
This Certification Practice Statement (CP/CPS) defines the operational procedures and security requirements applicable to the "Demo PKI" academic Public Key Infrastructure.
- **Root CA**: `Demo Root CA`
- **Issuing CA**: `Demo Intermediate CA`
- **Scope**: TLS authentication and encryption for web services (`app.demo.local`) and mutual TLS (mTLS) authentication for client users (`alice`).

## 2. Cryptographic Choices
In accordance with **NIST SP 800-57** recommendations and **CA/Browser Forum** standards:
- **Key Algorithm**: Elliptic Curve Cryptography (ECDSA) with curve **P-384** for Certification Authorities (Root and Intermediate) ensuring robust security (~192-bit symmetric equivalent), and **P-256** for end-entity certificates (server and client) for optimal handshake performance.
- **Hash Function**: **SHA-384** (minimum SHA-256 required, SHA-1 strictly prohibited).
- **Validity Periods**:
  - Root CA: 20 years (7,300 days).
  - Intermediate CA: 5 years (1,825 days).
  - Server / Client Certificates: 180 days (aligned with public TLS lifecycle reduction trends).

## 3. Key Management and CA Security
- **Offline Root CA (Air-Gapped)**: The Root CA private key (`root.key`) is generated and stored on an offline, air-gapped secure medium, protected by a robust passphrase and strict permissions (`chmod 400`). It is used exclusively to sign intermediate CA certificates.
- **Intermediate CA**: Operated for daily signing of end-entity certificates (servers and clients) and CRL generation. Protected by an AES-256-CBC encrypted ECDSA P-384 private key.

## 4. Certificate Issuance
- **Pre-issuance Verification**: All Certificate Signing Requests (CSRs) undergo identity validation (Common Name and Subject Alternative Name - SAN).
- **X.509 Profiles (RFC 5280)**:
  - **Intermediate CA**: `basicConstraints = critical, CA:TRUE, pathlen:0`, `keyUsage = critical, keyCertSign, cRLSign`.
  - **Server**: `extendedKeyUsage = serverAuth`, `subjectAltName = DNS:app.demo.local`.
  - **Client**: `extendedKeyUsage = clientAuth`.

## 5. Revocation
- **Mechanisms**: Publication of Certificate Revocation Lists (**CRL**) and Online Certificate Status Protocol (**OCSP**) support.
- **Incident Management**: In case of key compromise (referencing recent incidents such as eMudhra in October 2026), immediate revocation with reason `keyCompromise`, CRL regeneration, and frontend service (Nginx) reloading.

## 6. Responsibilities
- **PKI Operator**: Responsible for key generation, renewal, and CA key protection.
- **System Administrator / DevOps**: Responsible for deploying certificates on the Nginx server and managing CRL enforcement.
