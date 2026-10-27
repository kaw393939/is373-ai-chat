"""Probe the installed CA bundle and HTTPX verification using loopback TLS only.

Run inside the tested image with networking disabled and writable /tmp. The
synthetic CA is added to one in-memory client context, never the installed bundle.
This does not reproduce compromised intermediate keys or test a paid provider.
"""

import hashlib
import json
import os
import ssl
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory

import certifi
import httpx
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

# Fingerprints from certifi's tagged, upstream cacert.pem files:
# https://github.com/certifi/python-certifi/blob/2026.07.22/certifi/cacert.pem
# https://github.com/certifi/python-certifi/blob/2026.10.23/certifi/cacert.pem
REMOVED = "86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b"
RETAINED = "40f6af0346a99aa1cd1d555a4e9cce62c7f9634603ee406615833dc8c8d00367"


def installed_context():
    context = ssl.create_default_context(cafile=certifi.where())
    if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname:
        raise RuntimeError("Certificate and hostname verification must remain enabled")
    return context


def check_bundle():
    context = installed_context()
    fingerprints = {
        hashlib.sha256(der).hexdigest() for der in context.get_ca_certs(binary_form=True)
    }
    names = {
        value
        for cert in context.get_ca_certs()
        for component in cert["subject"]
        for attribute, value in component
        if attribute == "commonName"
    }
    if REMOVED in fingerprints or "emSign ECC Root CA - G3" in names:
        raise RuntimeError("Compromised emSign G3 root remains trusted")
    if RETAINED not in fingerprints or "emSign Root CA - G1" not in names:
        raise RuntimeError("Unaffected emSign G1 root was unnecessarily removed")
    return {
        "certifi": version("certifi"),
        "bundle_sha256": hashlib.sha256(Path(certifi.where()).read_bytes()).hexdigest(),
        "ca_count": len(fingerprints),
        "compromised_g3_absent": True,
        "unaffected_g1_retained": True,
    }


def certificates(directory):
    now = datetime.now(timezone.utc)
    ca_key, leaf_key = (ec.generate_private_key(ec.SECP256R1()) for _ in range(2))
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "IS373 disposable TLS CA")])

    def builder(subject, public_key, is_ca):
        return (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(ca_name)
            .public_key(public_key)
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5))
            .not_valid_after(now + timedelta(hours=1))
            .add_extension(x509.BasicConstraints(ca=is_ca, path_length=0 if is_ca else None), True)
            .add_extension(
                x509.KeyUsage(True, False, False, False, False, is_ca, is_ca, False, False),
                True,
            )
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(public_key), False)
        )

    ca = builder(ca_name, ca_key.public_key(), True).sign(ca_key, hashes.SHA256())
    leaf = (
        builder(
            x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")]),
            leaf_key.public_key(),
            False,
        )
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), False)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), False)
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), False
        )
        .sign(ca_key, hashes.SHA256())
    )
    cert_path, key_path = Path(directory) / "server.pem", Path(directory) / "server.key"
    for path, data in [
        (cert_path, leaf.public_bytes(serialization.Encoding.PEM)),
        (
            key_path,
            leaf_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            ),
        ),
    ]:
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as file:
            file.write(data)
    return ca.public_bytes(serialization.Encoding.PEM).decode(), cert_path, key_path


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", "6")
        self.end_headers()
        self.wfile.write(b"tls-ok")

    def log_message(self, *_):
        pass


class Server(HTTPServer):
    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(2)
        try:
            return self.context.wrap_socket(connection, server_side=True), address
        except BaseException:
            connection.close()
            raise


def rejected(context, url):
    try:
        with httpx.Client(verify=context, trust_env=False, timeout=2) as client:
            client.get(url)
    except httpx.ConnectError as error:
        pending, seen = [error], set()
        while pending:
            cause = pending.pop()
            if cause is None or id(cause) in seen:
                continue
            seen.add(id(cause))
            if isinstance(cause, ssl.SSLCertVerificationError):
                return cause.verify_code
            pending.extend([cause.__cause__, cause.__context__])
        raise RuntimeError("Connection failed without certificate-verification evidence") from error
    raise RuntimeError("Invalid TLS peer was accepted")


def main():
    bundle = check_bundle()
    with TemporaryDirectory(prefix="is373-tls-", dir="/tmp") as directory:
        ca, cert_path, key_path = certificates(directory)
        server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_context.load_cert_chain(cert_path, key_path)
        server = Server(("127.0.0.1", 0), Handler)
        server.context = server_context
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05})
        thread.start()
        try:
            trusted = installed_context()
            trusted.load_verify_locations(cadata=ca)
            port = server.server_port
            with httpx.Client(verify=trusted, trust_env=False, timeout=2) as client:
                response = client.get(f"https://localhost:{port}/")
                if response.status_code != 200 or response.text != "tls-ok":
                    raise RuntimeError("Trusted, matching TLS peer did not succeed")
            untrusted = rejected(installed_context(), f"https://localhost:{port}/")
            mismatch = rejected(trusted, f"https://127.0.0.1:{port}/")
            if untrusted not in {20, 21} or mismatch not in {62, 64}:
                raise RuntimeError("TLS rejection had an unexpected verification reason")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
            if thread.is_alive():
                raise RuntimeError("TLS server thread did not stop")
    if Path(directory).exists() or check_bundle() != bundle:
        raise RuntimeError("Temporary TLS material remains or installed bundle changed")
    app_version = Path("/app/VERSION")
    print(
        json.dumps(
            {
                "status": "passed",
                "scope": "installed certifi bundle and synthetic loopback TLS; no provider call",
                "commit": os.environ.get("COMMIT_SHA", "unknown"),
                "application_version": app_version.read_text().strip()
                if app_version.is_file()
                else None,
                "bundle": bundle,
                "cases": {
                    "trusted_matching_peer": "passed",
                    "untrusted_issuer_rejected": untrusted,
                    "wrong_hostname_rejected": mismatch,
                },
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"status": "failed", "error": str(error)}, sort_keys=True))
        raise SystemExit(1) from None
