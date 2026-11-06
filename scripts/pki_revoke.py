import os
import subprocess
import sys
import shutil

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
    print("--- Revoking Alice's Certificate ---")
    run_cmd('openssl ca -batch -config inter-ca/inter.cnf -revoke client/certs/alice.crt -crl_reason keyCompromise -passin pass:intersecret')

    print("--- Generating Intermediate CRL ---")
    run_cmd('openssl ca -batch -config inter-ca/inter.cnf -gencrl -out inter-ca/crl/inter.crl -passin pass:intersecret')

    # Create CRL bundle for Nginx
    crl_bundle = "server/certs/crl-bundle.pem"
    os.makedirs("server/certs", exist_ok=True)
    if os.path.exists("root-ca/crl/root.crl"):
        with open(crl_bundle, "wb") as outfile:
            for fname in ["root-ca/crl/root.crl", "inter-ca/crl/inter.crl"]:
                if os.path.exists(fname):
                    with open(fname, "rb") as infile:
                        outfile.write(infile.read())
    else:
        shutil.copy("inter-ca/crl/inter.crl", crl_bundle)

    print("--- Verifying CRL ---")
    run_cmd(f'"{OPENSSL}" crl -in inter-ca/crl/inter.crl -noout -text')

    print("[SUCCESS] Revocation and CRL generation completed successfully!")

if __name__ == "__main__":
    main()
