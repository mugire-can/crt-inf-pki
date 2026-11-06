# Enterprise PKI & mTLS Infrastructure

![Status](https://img.shields.io/badge/status-academic--reference-informational)
![License](https://img.shields.io/badge/license-MIT-blue)
![OpenSSL](https://img.shields.io/badge/OpenSSL-3.x-green)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Security Standard](https://img.shields.io/badge/NIST-SP%20800--57-informational)

An academic reference implementation of a two-tier PKI (offline root and online issuing CA) with OpenSSL automation, mutual TLS (mTLS), and certificate revocation. It is not a production CA and must only be used with disposable test data.

---

## 📂 Repository Structure

```
.
├── .github/                  # GitHub community and issue templates
│   ├── SECURITY.md
│   ├── CONTRIBUTING.md
│   └── ISSUE_TEMPLATE/
├── root-ca/                  # Configuration plus generated offline CA (generated files ignored)
│   └── root.cnf              # Root CA OpenSSL profile
├── inter-ca/                 # Configuration plus generated issuing CA (generated files ignored)
│   └── inter.cnf             # Issuing CA OpenSSL profile
├── server/                   # Generated server certificate and key (ignored)
├── client/                   # Generated client certificate and key (ignored)
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

### 1. Generate the PKI hierarchy and certificates
The script requires explicit passphrases and refuses to overwrite an existing PKI unless `--force` is supplied. Use a disposable directory or backup before regenerating:
```bash
set ROOT_CA_PASSWORD=change-me
set INTERMEDIATE_CA_PASSWORD=change-me
set CLIENT_BUNDLE_PASSWORD=change-me
python scripts/pki_setup.py --force
```

On PowerShell, replace `set` with `$env:ROOT_CA_PASSWORD = "change-me"` (and the other two variables). Never use these values outside a disposable lab.

### 2. Revoke a certificate and regenerate the CRL
```bash
set INTERMEDIATE_CA_PASSWORD=change-me
python scripts/pki_revoke.py --certificate client/certs/alice.crt --reason keyCompromise
```

### 3. Nginx mTLS configuration
Configure Nginx (`app.demo.local`) to enforce mutual TLS and strict CRL verification:
```nginx
server {
    listen 443 ssl;
    server_name app.demo.local;

    ssl_certificate     /path/to/generated/server/certs/server-chain.crt;
    ssl_certificate_key /path/to/generated/server/private/server.key;

    ssl_client_certificate /path/to/generated/inter-ca/certs/ca-chain.pem;
    ssl_verify_client      on;
    ssl_verify_depth       2;
    ssl_crl                /path/to/generated/server/certs/crl-bundle.pem;
}
```

---

## Key features and limitations
- **NIST SP 800-57 aligned**: ECDSA P-384 for CAs, P-256 for end entities.
- **SHA-384 Hashing**: Eliminates collision risks associated with legacy hash functions.
- **Strict X.509 Constraints**: `pathlen:0` on intermediate CA, mandatory `SAN` for servers (`DNS:app.demo.local`).
- **Revocation workflow**: Generates an intermediate CRL and an Nginx CRL bundle.

The project intentionally does not commit private keys, PKCS#12 bundles, CSRs, issued certificates, or OpenSSL state files. The generated files are local lab artifacts and are excluded by `.gitignore`.

## Validation

After generation, inspect the chain and certificate purposes:

```bash
openssl verify -CAfile root-ca/certs/root.crt -untrusted inter-ca/certs/inter.crt server/certs/server.crt
openssl x509 -in server/certs/server.crt -noout -subject -issuer -ext subjectAltName -ext extendedKeyUsage
openssl x509 -in client/certs/alice.crt -noout -subject -issuer -ext extendedKeyUsage
```

## Project status

This repository is an academic demonstration, not a general-purpose CA. It does not provide OCSP despite the historical report mentioning it; the current implementation covers CRL-based revocation only.

## 📄 License
This project is licensed under the [MIT License](LICENSE).
