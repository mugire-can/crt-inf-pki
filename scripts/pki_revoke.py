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

def run_cmd(cmd):
    if cmd.startswith('openssl '):
        cmd = f'"{OPENSSL}"' + cmd[7:]
    print(f"[RUN] {cmd}")
    res = subprocess.run(cmd, shell=True)
    if res.returncode != 0:
        print(f"[ERROR] Command failed with exit code {res.returncode}")
        sys.exit(res.returncode)

def main():
    parser = argparse.ArgumentParser(description="Revoke a certificate and generate the CRL bundle.")
    parser.add_argument("--certificate", required=True, help="Certificate path relative to the repository.")
    parser.add_argument(
        "--reason",
        default="unspecified",
        choices=["unspecified", "keyCompromise", "CACompromise", "affiliationChanged",
                 "superseded", "cessationOfOperation", "certificateHold"],
        help="OpenSSL revocation reason.",
    )
    args = parser.parse_args()
    if not os.environ.get("INTERMEDIATE_CA_PASSWORD"):
        raise RuntimeError("Missing required environment variable: INTERMEDIATE_CA_PASSWORD")

    print(f"--- Revoking {args.certificate} ---")
    run_cmd(f'openssl ca -batch -config inter-ca/inter.cnf -revoke "{args.certificate}" -crl_reason {args.reason} -passin env:INTERMEDIATE_CA_PASSWORD')

    print("--- Generating Intermediate CRL ---")
    run_cmd('openssl ca -batch -config inter-ca/inter.cnf -gencrl -out inter-ca/crl/inter.crl -passin env:INTERMEDIATE_CA_PASSWORD')

    # Create CRL bundle for Nginx
    crl_bundle = "server/certs/crl-bundle.pem"
    os.makedirs("server/certs", exist_ok=True)
    with open(crl_bundle, "wb") as outfile:
        for fname in ["root-ca/crl/root.crl", "inter-ca/crl/inter.crl"]:
            if os.path.exists(fname):
                with open(fname, "rb") as infile:
                    outfile.write(infile.read())

    print("--- Verifying CRL ---")
    run_cmd(f'"{OPENSSL}" crl -in inter-ca/crl/inter.crl -noout -text')

    print("[SUCCESS] Revocation and CRL generation completed successfully!")

if __name__ == "__main__":
    main()
