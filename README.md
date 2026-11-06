# Enterprise PKI & mTLS Infrastructure (Option A)

![Status](https://img.shields.io/badge/status-complete-success)
![License](https://img.shields.io/badge/license-MIT-blue)
![OpenSSL](https://img.shields.io/badge/OpenSSL-3.x-green)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Security Standard](https://img.shields.io/badge/NIST-SP%20800--57-informational)

A robust, production-grade Public Key Infrastructure (PKI) implementation and web service hardening project featuring a 3-tier trust hierarchy, automated OpenSSL scripting, mutual TLS (mTLS) authentication, and Certificate Revocation List (CRL) management.

---

## 📂 Repository Structure

```
.
├── .github/                  # GitHub community and issue templates
│   ├── SECURITY.md
│   ├── CONTRIBUTING.md
│   └── ISSUE_TEMPLATE/
├── root-ca/                  # Offline Root CA (Air-Gapped)
│   ├── root.cnf              # Root CA OpenSSL configuration
│   ├── private/root.key      # Root CA private key (ECDSA P-384, AES-256 encrypted)
│   └── certs/root.crt        # Root CA self-signed certificate
├── inter-ca/                 # Online Issuing / Intermediate CA
│   ├── inter.cnf             # Intermediate CA OpenSSL configuration
│   ├── private/inter.key     # Intermediate CA private key
│   ├── certs/inter.crt       # Intermediate CA certificate signed by Root
│   ├── certs/ca-chain.pem    # Full trust chain (Intermediate + Root)
│   └── crl/inter.crl         # Certificate Revocation List (CRL)
├── server/                   # Server Entity (app.demo.local)
│   ├── private/server.key     # Server private key (ECDSA P-256)
│   ├── certs/server.crt      # Server certificate with SAN
│   ├── certs/server-chain.crt# Server chain (Server + Intermediate)
│   └── certs/crl-bundle.pem  # Combined CRL bundle for Nginx
├── client/                   # End-User Entity (Alice)
│   ├── private/alice.key     # Client private key
│   ├── certs/alice.crt       # Client certificate (clientAuth)
│   └── certs/alice.p12       # PKCS#12 bundle for browser import
├── scripts/                  # Python Automation Scripts
│   ├── pki_setup.py          # PKI initialization & certificate issuance script
│   └── pki_revoke.py         # Certificate revocation & CRL generation script
├── docs/                     # Documentation & Deliverables
│   ├── cp-cps.md             # Certification Practice Statement (Mini CP/CPS)
│   └── technical-report.md   # Technical report & cryptographic justifications
├── LICENSE                   # MIT License
└── README.md                 # Project documentation
```

---

## 🚀 Quick Start Guide

### 1. Generate the PKI Hierarchy & Certificates
Run the automation script to initialize directories, generate private keys, create CSRs, and issue certificates for the Root CA, Intermediate CA, Server, and Client:
```bash
python scripts/pki_setup.py
```

### 2. Test Certificate Revocation (CRL)
To revoke a certificate (e.g., client `alice` for `keyCompromise`), generate the updated CRL bundle, and enforce revocation:
```bash
python scripts/pki_revoke.py
```

### 3. Nginx mTLS Configuration
Configure Nginx (`app.demo.local`) to enforce mutual TLS and strict CRL verification:
```nginx
server {
    listen 443 ssl;
    server_name app.demo.local;

    ssl_certificate     server/certs/server-chain.crt;
    ssl_certificate_key server/private/server.key;

    ssl_client_certificate inter-ca/certs/ca-chain.pem;
    ssl_verify_client      on;
    ssl_verify_depth       2;
    ssl_crl                server/certs/crl-bundle.pem;
}
```

---

## 🛡️ Key Features & Cryptographic Compliance
- **NIST SP 800-57 Compliant**: ECDSA P-384 for CAs, P-256 for end-entities.
- **SHA-384 Hashing**: Eliminates collision risks associated with legacy hash functions.
- **Strict X.509 Constraints**: `pathlen:0` on intermediate CA, mandatory `SAN` for servers (`DNS:app.demo.local`).
- **Incident Resiliency**: Designed with learnings from recent CA compromises (e.g., entropy verification and rapid revocation workflows).

## 📄 License
This project is licensed under the [MIT License](LICENSE).
