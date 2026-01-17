"""
Key Manager

Manages student private keys and certificates.
"""

from pathlib import Path
from typing import Optional, Tuple

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


class KeyManager:
    """Manages student private keys and certificates."""

    def __init__(self, keys_dir: Path):
        """
        Initialize Key Manager.

        Args:
            keys_dir: Directory containing student keys and certificates
        """
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(parents=True, exist_ok=True)

    def load_student_keys(
        self,
        student_id: str
    ) -> Tuple[rsa.RSAPrivateKey, x509.Certificate]:
        """
        Load student private key and certificate.

        Args:
            student_id: Student identifier

        Returns:
            Tuple of (private key, certificate)
        """
        key_path = self.keys_dir / "students" / student_id / "private_key.pem"
        cert_path = self.keys_dir / "students" / student_id / "certificate.pem"

        if not key_path.exists():
            raise FileNotFoundError(
                f"Private key not found for student {student_id}. "
                f"Expected at: {key_path}"
            )

        if not cert_path.exists():
            raise FileNotFoundError(
                f"Certificate not found for student {student_id}. "
                f"Expected at: {cert_path}"
            )

        # Load private key
        with open(key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,  # In production, prompt for password
            )

        # Load certificate
        with open(cert_path, "rb") as f:
            certificate = x509.load_pem_x509_certificate(f.read())

        return private_key, certificate

    def get_certificate_pem(self, student_id: str) -> str:
        """
        Get student certificate as PEM string.

        Args:
            student_id: Student identifier

        Returns:
            Certificate PEM string
        """
        cert_path = self.keys_dir / "students" / student_id / "certificate.pem"

        if not cert_path.exists():
            raise FileNotFoundError(
                f"Certificate not found for student {student_id}"
            )

        with open(cert_path, "rb") as f:
            return f.read().decode('utf-8')
