import os
import subprocess
import sys
import shutil
import argparse

def get_openssl_path():
    p = shutil.which('openssl')
    if p:
        return p
    candidates = [
        r'C:\Program Files\Git\usr\bin\openssl.exe',
        r'C:\Program Files\OpenSSL-Win64\bin\openssl.exe',
        r'C:\Program Files\OpenSSL\bin\openssl.exe',
        r'C:\Program Files (x86)\OpenSSL-Win32\bin\openssl.exe'
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return 'openssl'

OPENSSL = get_openssl_path()
print(f"Using OpenSSL binary: {OPENSSL}")

def run_cmd(cmd):
    if cmd.startswith('openssl '):
        cmd = f'"{OPENSSL}"' + cmd[7:]
    print(f"[RUN] {cmd}")
    res = subprocess.run(cmd, shell=True)
    if res.returncode != 0:
        print(f"[ERROR] Command failed with exit code {res.returncode}")
        sys.exit(res.returncode)

def required_secret(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

def main():
    parser = argparse.ArgumentParser(description="Generate a disposable two-tier PKI.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete existing generated PKI directories before creating new material.",
    )
    args = parser.parse_args()
    required_secret("ROOT_CA_PASSWORD")
    required_secret("INTERMEDIATE_CA_PASSWORD")
    required_secret("CLIENT_BUNDLE_PASSWORD")

    # Clean previous generated runtime artifacts inside root-ca, inter-ca, server, client
    for d in ["root-ca", "inter-ca", "server", "client"]:
        if os.path.exists(d):
            if not args.force:
                raise RuntimeError(
                    f"{d} already exists; use --force only for disposable test material"
                )
            shutil.rmtree(d)

    # 1. Create directory structure
    dirs = [
        "root-ca/private", "root-ca/certs", "root-ca/newcerts", "root-ca/crl",
        "inter-ca/private", "inter-ca/certs", "inter-ca/newcerts", "inter-ca/crl", "inter-ca/csr",
        "server/certs", "server/private",
        "client/certs", "client/private"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    
    # 2. Write OpenSSL configuration files with correct relative paths
    root_cnf = """[ ca ]
default_ca = CA_default

[ CA_default ]
dir               = root-ca
certs             = $dir/certs
crl_dir           = $dir/crl
new_certs_dir     = $dir/newcerts
database          = $dir/index.txt
serial            = $dir/serial
RANDFILE          = $dir/private/.rand

private_key       = $dir/private/root.key
certificate       = $dir/certs/root.crt

crl               = $dir/crl/root.crl
crlnumber         = $dir/crlnumber
crl_extensions    = crl_ext
default_crl_days  = 30
default_days      = 7300
default_md        = sha384
preserve          = no
policy            = policy_strict

[ policy_strict ]
countryName             = optional
stateOrProvinceName     = optional
organizationName        = optional
organizationalUnitName  = optional
commonName              = supplied
emailAddress            = optional

[ req ]
default_bits        = 3072
distinguished_name  = req_distinguished_name
string_mask         = utf8only
default_md          = sha384
x509_extensions     = v3_ca

[ req_distinguished_name ]
countryName             = Country Name (2 letter code)
organizationName        = Organization Name
commonName              = Common Name

[ v3_ca ]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical, CA:TRUE
keyUsage = critical, keyCertSign, cRLSign

[ v3_intermediate_ca ]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical, CA:TRUE, pathlen:0
keyUsage = critical, keyCertSign, cRLSign

[ crl_ext ]
authorityKeyIdentifier=keyid:always
"""
    with open("root-ca/root.cnf", "w") as f:
        f.write(root_cnf)

    inter_cnf = """[ ca ]
default_ca = CA_default

[ CA_default ]
dir               = inter-ca
certs             = $dir/certs
crl_dir           = $dir/crl
new_certs_dir     = $dir/newcerts
database          = $dir/index.txt
serial            = $dir/serial
RANDFILE          = $dir/private/.rand

private_key       = $dir/private/inter.key
certificate       = $dir/certs/inter.crt

crl               = $dir/crl/inter.crl
crlnumber         = $dir/crlnumber
crl_extensions    = crl_ext
default_crl_days  = 7
default_days      = 1825
default_md        = sha384
preserve          = no
policy            = policy_loose

[ policy_loose ]
countryName             = optional
stateOrProvinceName     = optional
organizationName        = optional
organizationalUnitName  = optional
commonName              = supplied
emailAddress            = optional

[ req ]
default_bits        = 3072
distinguished_name  = req_distinguished_name
string_mask         = utf8only
default_md          = sha384

[ req_distinguished_name ]
countryName             = Country Name (2 letter code)
organizationName        = Organization Name
commonName              = Common Name

[ server_cert ]
basicConstraints = CA:FALSE
nsCertType = server
nsComment = "OpenSSL Generated Server Certificate"
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer:always
keyUsage = critical, digitalSignature
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[ client_cert ]
basicConstraints = CA:FALSE
nsCertType = client, email
nsComment = "OpenSSL Generated Client Certificate"
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer:always
keyUsage = critical, digitalSignature
extendedKeyUsage = clientAuth

[ alt_names ]
DNS.1 = app.demo.local

[ crl_ext ]
authorityKeyIdentifier=keyid:always
"""
    with open("inter-ca/inter.cnf", "w") as f:
        f.write(inter_cnf)

    # 3. Initialize database and serial files
    for ca in ["root-ca", "inter-ca"]:
        idx_path = os.path.join(ca, "index.txt")
        open(idx_path, "w").close()
        
        serial_path = os.path.join(ca, "serial")
        with open(serial_path, "w") as f:
            f.write("1000\n")
                
        crl_num_path = os.path.join(ca, "crlnumber")
        with open(crl_num_path, "w") as f:
            f.write("1000\n")

    # 4. Generate Root CA Private Key and Certificate
    run_cmd("openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-384 -aes-256-cbc -pass env:ROOT_CA_PASSWORD -out root-ca/private/root.key")
    run_cmd('openssl req -new -x509 -sha384 -days 7300 -config root-ca/root.cnf -extensions v3_ca -key root-ca/private/root.key -passin env:ROOT_CA_PASSWORD -out root-ca/certs/root.crt -subj "/O=Demo PKI/CN=Demo Root CA"')

    # 5. Generate Intermediate CA Private Key and CSR
    run_cmd("openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-384 -aes-256-cbc -pass env:INTERMEDIATE_CA_PASSWORD -out inter-ca/private/inter.key")
    run_cmd('openssl req -new -sha384 -key inter-ca/private/inter.key -passin env:INTERMEDIATE_CA_PASSWORD -out inter-ca/csr/inter.csr -subj "/O=Demo PKI/CN=Demo Intermediate CA"')

    # 6. Sign Intermediate CA CSR with Root CA
    run_cmd('openssl ca -batch -config root-ca/root.cnf -extensions v3_intermediate_ca -days 1825 -notext -in inter-ca/csr/inter.csr -out inter-ca/certs/inter.crt -passin env:ROOT_CA_PASSWORD')

    # 7. Create CA Chain (inter.crt + root.crt)
    with open("inter-ca/certs/ca-chain.pem", "wb") as outfile:
        for fname in ["inter-ca/certs/inter.crt", "root-ca/certs/root.crt"]:
            with open(fname, "rb") as infile:
                outfile.write(infile.read())

    # 8. Generate Server Key and CSR
    run_cmd("openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out server/private/server.key")
    run_cmd('openssl req -new -key server/private/server.key -out server/certs/server.csr -subj "/O=Demo PKI/CN=app.demo.local"')

    # 9. Sign Server Certificate with Intermediate CA
    run_cmd('openssl ca -batch -config inter-ca/inter.cnf -extensions server_cert -days 180 -notext -in server/certs/server.csr -out server/certs/server.crt -passin env:INTERMEDIATE_CA_PASSWORD')

    # Create server chain (server.crt + inter.crt)
    with open("server/certs/server-chain.crt", "wb") as outfile:
        for fname in ["server/certs/server.crt", "inter-ca/certs/inter.crt"]:
            with open(fname, "rb") as infile:
                outfile.write(infile.read())

    # 10. Generate Client (Alice) Key and CSR
    run_cmd("openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out client/private/alice.key")
    run_cmd('openssl req -new -key client/private/alice.key -out client/certs/alice.csr -subj "/O=Demo PKI/CN=alice"')

    # 11. Sign Client Certificate with Intermediate CA
    run_cmd('openssl ca -batch -config inter-ca/inter.cnf -extensions client_cert -days 180 -notext -in client/certs/alice.csr -out client/certs/alice.crt -passin env:INTERMEDIATE_CA_PASSWORD')

    # Export client PKCS#12 bundle
    run_cmd('openssl pkcs12 -export -inkey client/private/alice.key -in client/certs/alice.crt -certfile inter-ca/certs/ca-chain.pem -out client/certs/alice.p12 -passout env:CLIENT_BUNDLE_PASSWORD')

    print("[SUCCESS] PKI setup and certificate issuance completed successfully!")

if __name__ == "__main__":
    main()
