# Technical Report: Enterprise PKI Implementation and Securing
*Academic PKI Project — Option A (Complete Core)*

---

## 1. Executive Summary
This project involves the design, deployment, and operation of a three-tier hierarchical Public Key Infrastructure (PKI) comprising an offline Root CA, an online Intermediate CA, and end-entity certificates to secure a web service via HTTPS and mutual TLS (mTLS).

## 2. Trust Chain Architecture
```
[ Root CA (Offline, Air-Gapped, P-384) ]
       │
       ▼ (Signs)
[ Intermediate CA (Online, P-384) ]
       ├──► Server Certificate (app.demo.local, P-256) ──► Nginx (TLS + mTLS)
       └──► Client Certificate (Alice, P-256) ──────────► Client Authentication (PKCS#12)
```

## 3. Cryptographic Choices Justification
- **Algorithms and Elliptic Curves (ECDSA)**:
  - Curve **P-384** selected for CA hierarchy to provide a higher security margin than current recommendations (~192-bit security level), ensuring long-term resistance against advances in computing power.
  - Curve **P-256** selected for end-entities (server and client) providing an optimal trade-off between TLS handshake performance and security.
- **Hash Function**: **SHA-384** for certificate and CRL signatures, eliminating collision risks (SHA-1 being strictly prohibited).
- **X.509 Extensions and SAN**:
  - Systematic use of **Subject Alternative Name (SAN)** for server certificates (`DNS:app.demo.local`), essential for modern client validation.
  - Strict CA constraints (`basicConstraints = CA:TRUE`, `pathlen:0` on the intermediate CA to prevent cascading sub-CA issuance).

## 4. Incident Analysis: Lessons from the eMudhra CA Compromise (October 2026)
Analysis of the October 2026 incident involving eMudhra intermediate CAs highlights a critical risk: **weak entropy during private key generation**, allowing direct key derivation from public certificates.
- **Mitigation measures applied in our PKI**:
  1. Use of cryptographically secure pseudo-random number generators (CSPRNG) underlying OpenSSL and NIST curves.
  2. Rigorous private key protection (`chmod 400`, AES-256-CBC encryption of CA keys).
  3. Establishment of a strict revocation policy (CRL) and rigorous validation of certification chains.

## 5. Revocation Demonstration
Certificate revocation (tested with `alice`'s client certificate using the `keyCompromise` reason) demonstrates the operational effectiveness of the CRL. Once the certificate is revoked and the CRL is updated in the Nginx bundle, the server immediately rejects any connection originating from that certificate, ensuring perimeter security integrity.
