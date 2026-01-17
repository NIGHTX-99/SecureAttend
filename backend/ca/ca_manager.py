"""
Certificate Authority (CA) Manager

Handles CA key generation, certificate creation, and CA certificate management.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID, KeyUsageOID


class CAManager:
    """Manages the Certificate Authority operations."""

    def __init__(self, ca_dir: Path):
        """
        Initialize CA Manager.

        Args:
            ca_dir: Directory to store CA keys and certificates
        """
        self.ca_dir = Path(ca_dir)
        self.ca_dir.mkdir(parents=True, exist_ok=True)
        
        self.ca_key_path = self.ca_dir / "ca_private_key.pem"
        self.ca_cert_path = self.ca_dir / "ca_certificate.pem"
        self.cert_registry_path = self.ca_dir / "cert_registry.json"

    def initialize_ca(
        self, 
        organization: str = "College",
        validity_years: int = 10,
        key_size: int = 2048
    ) -> Tuple[rsa.RSAPrivateKey, x509.Certificate]:
        """
        Initialize or load the CA.

        Args:
            organization: Organization name for CA certificate
            validity_years: CA certificate validity period in years
            key_size: RSA key size in bits

        Returns:
            Tuple of (CA private key, CA certificate)
        """
        if self.ca_key_path.exists() and self.ca_cert_path.exists():
            # Load existing CA
            return self._load_ca()

        # Generate new CA
        return self._generate_ca(organization, validity_years, key_size)

    def _generate_ca(
        self, 
        organization: str, 
        validity_years: int,
        key_size: int
    ) -> Tuple[rsa.RSAPrivateKey, x509.Certificate]:
        """Generate a new CA key pair and self-signed certificate."""
        print(f"Generating new CA with {key_size}-bit RSA key...")

        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )

        # Create self-signed CA certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Certificate Authority"),
            x509.NameAttribute(NameOID.COMMON_NAME, f"{organization} Root CA"),
        ])

        ca_cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365 * validity_years))
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    key_cert_sign=True,
                    crl_sign=True,
                    digital_signature=True,
                    key_encipherment=False,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()),
                critical=False,
            )
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                    x509.SubjectKeyIdentifier.from_public_key(private_key.public_key())
                ),
                critical=False,
            )
            .sign(private_key, hashes.SHA256())
        )

        # Save CA key (encrypted in production)
        with open(self.ca_key_path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),  # In production, use encryption
                )
            )

        # Save CA certificate
        with open(self.ca_cert_path, "wb") as f:
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))

        # Initialize certificate registry
        self._init_cert_registry()

        print(f"CA initialized successfully!")
        print(f"  CA Key: {self.ca_key_path}")
        print(f"  CA Cert: {self.ca_cert_path}")
        print(f"  Valid until: {ca_cert.not_valid_after}")

        return private_key, ca_cert

    def _load_ca(self) -> Tuple[rsa.RSAPrivateKey, x509.Certificate]:
        """Load existing CA key and certificate."""
        print("Loading existing CA...")

        with open(self.ca_key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
            )

        with open(self.ca_cert_path, "rb") as f:
            ca_cert = x509.load_pem_x509_certificate(f.read())

        print(f"CA loaded. Valid until: {ca_cert.not_valid_after}")
        return private_key, ca_cert

    def get_ca_certificate(self) -> x509.Certificate:
        """Get the CA certificate (public)."""
        if not self.ca_cert_path.exists():
            raise FileNotFoundError("CA certificate not found. Initialize CA first.")

        with open(self.ca_cert_path, "rb") as f:
            return x509.load_pem_x509_certificate(f.read())

    def get_ca_private_key(self) -> rsa.RSAPrivateKey:
        """Get the CA private key."""
        if not self.ca_key_path.exists():
            raise FileNotFoundError("CA private key not found. Initialize CA first.")

        with open(self.ca_key_path, "rb") as f:
            return serialization.load_pem_private_key(
                f.read(),
                password=None,
            )

    def _init_cert_registry(self):
        """Initialize certificate registry."""
        if not self.cert_registry_path.exists():
            registry = {
                "students": {},
                "doors": {},
                "servers": {},
            }
            with open(self.cert_registry_path, "w") as f:
                json.dump(registry, f, indent=2)

    def _update_registry(
        self, 
        cert_type: str, 
        identifier: str, 
        serial_number: int,
        subject: str
    ):
        """
        Update certificate registry.

        Args:
            cert_type: Type of certificate (students, doors, servers)
            identifier: Unique identifier (student_id, door_id, etc.)
            serial_number: Certificate serial number
            subject: Certificate subject DN
        """
        with open(self.cert_registry_path, "r") as f:
            registry = json.load(f)

        registry[cert_type][identifier] = {
            "serial_number": str(serial_number),
            "subject": subject,
            "issued_at": datetime.utcnow().isoformat(),
            "revoked": False,
        }

        with open(self.cert_registry_path, "w") as f:
            json.dump(registry, f, indent=2)

    def get_registry(self) -> dict:
        """Get the certificate registry."""
        if not self.cert_registry_path.exists():
            self._init_cert_registry()

        with open(self.cert_registry_path, "r") as f:
            return json.load(f)
