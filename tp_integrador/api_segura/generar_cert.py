"""Genera un certificado TLS autofirmado para localhost (solo demo): tp_integrador/api_segura/certs/{cert.pem,key.pem}.

El navegador mostrara una advertencia porque no lo firma una autoridad de certificacion; en produccion
se usaria un certificado de una CA (o el balanceador/gateway terminaria el TLS).
"""
import datetime
import ipaddress
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

CERTS = Path(__file__).resolve().parent / "certs"
CERTS.mkdir(exist_ok=True)

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
nombre = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
ahora = datetime.datetime.now(datetime.timezone.utc)
cert = (
    x509.CertificateBuilder()
    .subject_name(nombre)
    .issuer_name(nombre)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(ahora - datetime.timedelta(minutes=1))
    .not_valid_after(ahora + datetime.timedelta(days=365))
    .add_extension(
        x509.SubjectAlternativeName([x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
        critical=False,
    )
    .sign(key, hashes.SHA256())
)
(CERTS / "key.pem").write_bytes(
    key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()
    )
)
(CERTS / "cert.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
print("Certificado generado en", CERTS)
