"""
Certificate Issuer

Issues X.509 certificates to students, door devices, and servers.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID, KeyUsageOID

from backend.ca.ca_manager import CAManager


class CertificateIssuer:
    """Issues certificates signed by the CA."""

    def __init__(self, ca_manager: CAManager, certs_dir: Path):
        """
        Initialize Certificate Issuer.

        Args:
            ca_manager: CA Manager instance
            certs_dir: Directory to store issued certificates
        """
        self.ca_manager = ca_manager
        self.certs_dir = Path(certs_dir)
        self.certs_dir.mkdir(parents=True, exist_ok=True)

    def issue_student_certificate(
        self,
        student_id: str,
        email: Optional[str] = None,
        validity_years: int = 1,
        key_size: int = 2048
    ) -> Tuple[rsa.RSAPrivateKey, x509.Certificate]:
        """
        Issue a certificate to a student.

        Args:
            student_id: Unique student identifier
            email: Student email (optional)
            validity_years: Certificate validity period
            key_size: RSA key size in bits

        Returns:
            Tuple of (private key, certificate)
        """
        # Generate student key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )

        # Build subject name
        name_attributes = [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "College"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Students"),
            x509.NameAttribute(NameOID.COMMON_NAME, f"student_{student_id}"),
        ]
        if email:
            name_attributes.append(x509.NameAttribute(NameOID.EMAIL_ADDRESS, email))

        subject = x509.Name(name_attributes)

        # Get CA key and certificate
        ca_private_key = self.ca_manager.get_ca_private_key()
        ca_cert = self.ca_manager.get_ca_certificate()

        # Build certificate
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(ca_cert.subject)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365 * validity_years))
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.ExtendedKeyUsage([
                    ExtendedKeyUsageOID.CLIENT_AUTH,
                ]),
                critical=False,
            )
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()),
                critical=False,
            )
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                    ca_cert.extensions.get_extension_for_oid(
                        x509.ExtensionOID.SUBJECT_KEY_IDENTIFIER
                    ).value
                ),
                critical=False,
            )
            .sign(ca_private_key, hashes.SHA256())
        )

        # Save certificate
        cert_dir = self.certs_dir / "students" / student_id
        cert_dir.mkdir(parents=True, exist_ok=True)

        cert_path = cert_dir / "certificate.pem"
        key_path = cert_dir / "private_key.pem"

        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        with open(key_path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        # Update registry
        self.ca_manager._update_registry(
            "students",
            student_id,
            cert.serial_number,
            str(subject)
        )

        print(f"Issued certificate for student {student_id}")
        print(f"  Certificate: {cert_path}")
        print(f"  Private Key: {key_path}")
        print(f"  Serial: {cert.serial_number}")
        print(f"  Valid until: {cert.not_valid_after}")

        return private_key, cert

    def issue_door_certificate(
        self,
        door_id: str,
        room_id: str,
        validity_years: int = 5,
        key_size: int = 2048
    ) -> Tuple[rsa.RSAPrivateKey, x509.Certificate]:
        """
        Issue a certificate to a door device.

        Args:
            door_id: Unique door identifier
            room_id: Room identifier
            validity_years: Certificate validity period
            key_size: RSA key size in bits

        Returns:
            Tuple of (private key, certificate)
        """
        # Generate door key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )

        # Build subject name
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "College"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Doors"),
            x509.NameAttribute(NameOID.COMMON_NAME, f"door_{door_id}"),
        ])

        # Add room_id as custom extension (using OID 2.5.29.17 - Subject Alternative Name)
        # We'll use the common name format: room_id in OU
        # Better: use SAN extension for room_id
        san_extension = x509.SubjectAlternativeName([
            x509.DirectoryName(
                x509.Name([
                    x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, f"Room:{room_id}"),
                ])
            )
        ])

        # Get CA key and certificate
        ca_private_key = self.ca_manager.get_ca_private_key()
        ca_cert = self.ca_manager.get_ca_certificate()

        # Build certificate
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(ca_cert.subject)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=365 * validity_years))
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.ExtendedKeyUsage([
                    ExtendedKeyUsageOID.CLIENT_AUTH,
                    ExtendedKeyUsageOID.SERVER_AUTH,
                ]),
                critical=False,
            )
            .add_extension(san_extension, critical=False)
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(private_key.public_key()),
                critical=False,
            )
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                    ca_cert.extensions.get_extension_for_oid(
                        x509.ExtensionOID.SUBJECT_KEY_IDENTIFIER
                    ).value
                ),
                critical=False,
            )
            .sign(ca_private_key, hashes.SHA256())
        )

        # Save certificate
        cert_dir = self.certs_dir / "doors" / door_id
        cert_dir.mkdir(parents=True, exist_ok=True)

        cert_path = cert_dir / "certificate.pem"
        key_path = cert_dir / "private_key.pem"

        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        with open(key_path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        # Update registry
        self.ca_manager._update_registry(
            "doors",
            door_id,
            cert.serial_number,
            str(subject)
        )

        print(f"Issued certificate for door {door_id} (room: {room_id})")
        print(f"  Certificate: {cert_path}")
        print(f"  Private Key: {key_path}")
        print(f"  Serial: {cert.serial_number}")

        return private_key, cert
