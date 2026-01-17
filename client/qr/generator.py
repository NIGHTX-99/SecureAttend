"""
QR Code Generator

Generates QR codes containing student certificate and authentication data.
"""

import json
import secrets
from pathlib import Path
from typing import Optional, Dict
import qrcode
from qrcode.image.pil import PilImage

from cryptography import x509
from cryptography.hazmat.primitives import serialization


class QRGenerator:
    """Generates QR codes for student authentication."""

    def __init__(self, qr_version: int = 1, qr_error_correction: str = "M"):
        """
        Initialize QR Generator.

        Args:
            qr_version: QR code version (1-40, higher = more data capacity)
            qr_error_correction: Error correction level (L, M, Q, H)
        """
        self.qr_version = qr_version
        error_correction_map = {
            "L": qrcode.constants.ERROR_CORRECT_L,
            "M": qrcode.constants.ERROR_CORRECT_M,
            "Q": qrcode.constants.ERROR_CORRECT_Q,
            "H": qrcode.constants.ERROR_CORRECT_H,
        }
        self.error_correction = error_correction_map.get(
            qr_error_correction, qrcode.constants.ERROR_CORRECT_M
        )

    def generate_nonce(self, size: int = 32) -> str:
        """
        Generate a cryptographically secure random nonce.

        Args:
            size: Size in bytes (default: 32 = 256 bits)

        Returns:
            Hex-encoded nonce string
        """
        nonce_bytes = secrets.token_bytes(size)
        return nonce_bytes.hex()

    def create_qr_data(
        self,
        student_id: str,
        certificate_pem: str,
        nonce: Optional[str] = None
    ) -> Dict:
        """
        Create QR code data structure.

        Args:
            student_id: Student identifier
            certificate_pem: Student certificate in PEM format
            nonce: Optional nonce (generated if not provided)

        Returns:
            Dictionary containing QR data
        """
        if nonce is None:
            nonce = self.generate_nonce()

        qr_data = {
            "student_id": student_id,
            "certificate": certificate_pem,
            "nonce": nonce,
            "version": "1.0",  # QR data format version
        }

        return qr_data

    def qr_data_to_json(self, qr_data: Dict) -> str:
        """
        Convert QR data to JSON string.

        Args:
            qr_data: QR data dictionary

        Returns:
            JSON string
        """
        return json.dumps(qr_data, sort_keys=True)

    def generate_qr_code(
        self,
        student_id: str,
        certificate_pem: str,
        output_path: Optional[Path] = None,
        display: bool = True
    ) -> tuple:
        """
        Generate QR code image.

        Args:
            student_id: Student identifier
            certificate_pem: Student certificate in PEM format
            output_path: Optional path to save QR code image
            display: Whether to display QR code in console (default: True)

        Returns:
            Tuple of (QR code image, QR data JSON string)
        """
        # Create QR data
        qr_data = self.create_qr_data(student_id, certificate_pem)
        qr_json = self.qr_data_to_json(qr_data)

        # Generate QR code
        qr = qrcode.QRCode(
            version=self.qr_version,
            error_correction=self.error_correction,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_json)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save if path provided
        if output_path:
            img.save(output_path)
            print(f"QR code saved to: {output_path}")

        # Display in console if requested
        if display:
            print("\n" + "=" * 60)
            print("QR CODE DATA")
            print("=" * 60)
            print(f"Student ID: {student_id}")
            print(f"Nonce: {qr_data['nonce']}")
            print("\nScan this QR code with a door scanner:\n")
            # Print QR code as ASCII art
            qr.print_ascii(invert=True)

        return img, qr_json

    def parse_qr_data(self, qr_json: str) -> Dict:
        """
        Parse QR code JSON data.

        Args:
            qr_json: QR code JSON string

        Returns:
            Parsed QR data dictionary
        """
        try:
            return json.loads(qr_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid QR code data format: {str(e)}")


def load_student_certificate(cert_path: Path) -> tuple[str, x509.Certificate]:
    """
    Load student certificate from file.

    Args:
        cert_path: Path to certificate PEM file

    Returns:
        Tuple of (certificate PEM string, certificate object)
    """
    if not cert_path.exists():
        raise FileNotFoundError(f"Certificate not found: {cert_path}")

    with open(cert_path, "rb") as f:
        cert_pem_bytes = f.read()
        cert = x509.load_pem_x509_certificate(cert_pem_bytes)

    cert_pem = cert_pem_bytes.decode('utf-8')
    return cert_pem, cert
