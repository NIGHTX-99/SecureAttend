"""
Certificate Revocation List (CRL) Manager

Manages certificate revocation for students, doors, and servers.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Set

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from backend.ca.ca_manager import CAManager


class CRLManager:
    """Manages Certificate Revocation Lists."""

    def __init__(self, ca_manager: CAManager, crl_dir: Path):
        """
        Initialize CRL Manager.

        Args:
            ca_manager: CA Manager instance
            crl_dir: Directory to store CRLs
        """
        self.ca_manager = ca_manager
        self.crl_dir = Path(crl_dir)
        self.crl_dir.mkdir(parents=True, exist_ok=True)
        self.crl_path = self.crl_dir / "crl.pem"
        self.revoked_serials_path = self.crl_dir / "revoked_serials.json"

    def revoke_certificate(
        self, 
        serial_number: int, 
        revocation_reason: x509.ReasonFlags = x509.ReasonFlags.unspecified
    ):
        """
        Revoke a certificate by serial number.

        Args:
            serial_number: Certificate serial number to revoke
            revocation_reason: Reason for revocation
        """
        # Load revoked serials
        revoked_serials = self._load_revoked_serials()
        
        # Add to revoked list
        revoked_serials[str(serial_number)] = {
            "serial_number": str(serial_number),
            "revoked_at": datetime.utcnow().isoformat(),
            "reason": revocation_reason.name,
        }

        # Save revoked serials
        self._save_revoked_serials(revoked_serials)

        # Update CRL
        self._generate_crl(revoked_serials)

        print(f"Certificate with serial {serial_number} revoked: {revocation_reason.name}")

    def revoke_student_certificate(self, student_id: str, reason: str = "unspecified"):
        """
        Revoke a student certificate.

        Args:
            student_id: Student identifier
            reason: Revocation reason
        """
        registry = self.ca_manager.get_registry()
        
        if student_id not in registry.get("students", {}):
            raise ValueError(f"Student {student_id} not found in registry")

        student_info = registry["students"][student_id]
        serial_number = int(student_info["serial_number"])

        # Map reason string to ReasonFlags
        reason_map = {
            "unspecified": x509.ReasonFlags.unspecified,
            "key_compromise": x509.ReasonFlags.key_compromise,
            "superseded": x509.ReasonFlags.superseded,
            "cessation_of_operation": x509.ReasonFlags.cessation_of_operation,
        }
        reason_flag = reason_map.get(reason, x509.ReasonFlags.unspecified)

        self.revoke_certificate(serial_number, reason_flag)

        # Mark as revoked in registry
        registry["students"][student_id]["revoked"] = True
        self._update_registry(registry)

    def is_revoked(self, serial_number: int) -> bool:
        """
        Check if a certificate is revoked.

        Args:
            serial_number: Certificate serial number

        Returns:
            True if revoked, False otherwise
        """
        revoked_serials = self._load_revoked_serials()
        return str(serial_number) in revoked_serials

    def _load_revoked_serials(self) -> dict:
        """Load revoked serial numbers from file."""
        if not self.revoked_serials_path.exists():
            return {}

        with open(self.revoked_serials_path, "r") as f:
            return json.load(f)

    def _save_revoked_serials(self, revoked_serials: dict):
        """Save revoked serial numbers to file."""
        with open(self.revoked_serials_path, "w") as f:
            json.dump(revoked_serials, f, indent=2)

    def _generate_crl(self, revoked_serials: dict):
        """
        Generate a Certificate Revocation List (CRL).

        Args:
            revoked_serials: Dictionary of revoked serial numbers
        """
        ca_private_key = self.ca_manager.get_ca_private_key()
        ca_cert = self.ca_manager.get_ca_certificate()

        # Build list of revoked certificate entries
        revoked_certs = []
        for serial_str, info in revoked_serials.items():
            serial_number = int(serial_str)
            
            # Map reason string to ReasonFlags
            reason_map = {
                "unspecified": x509.ReasonFlags.unspecified,
                "key_compromise": x509.ReasonFlags.key_compromise,
                "superseded": x509.ReasonFlags.superseded,
                "cessation_of_operation": x509.ReasonFlags.cessation_of_operation,
            }
            reason = reason_map.get(info.get("reason", "unspecified"), x509.ReasonFlags.unspecified)
            
            revoked_at = datetime.fromisoformat(info["revoked_at"])

            revoked_certs.append(
                x509.RevokedCertificateBuilder()
                .serial_number(serial_number)
                .revocation_date(revoked_at)
                .add_extension(
                    x509.CRLReason(reason),
                    critical=False,
                )
                .build()
            )

        # Build CRL
        crl = (
            x509.CertificateRevocationListBuilder()
            .issuer_name(ca_cert.subject)
            .last_update(datetime.utcnow())
            .next_update(datetime.utcnow() + timedelta(days=7))  # CRL valid for 7 days
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                    ca_cert.extensions.get_extension_for_oid(
                        x509.ExtensionOID.SUBJECT_KEY_IDENTIFIER
                    ).value
                ),
                critical=False,
            )
        )

        # Add revoked certificates
        for revoked_cert in revoked_certs:
            crl = crl.add_revoked_certificate(revoked_cert)

        # Sign CRL
        crl = crl.sign(ca_private_key, hashes.SHA256())

        # Save CRL
        with open(self.crl_path, "wb") as f:
            f.write(crl.public_bytes(serialization.Encoding.PEM))

    def get_crl(self) -> x509.CertificateRevocationList:
        """
        Get the current Certificate Revocation List.

        Returns:
            CertificateRevocationList object
        """
        if not self.crl_path.exists():
            # Generate empty CRL
            self._generate_crl({})

        with open(self.crl_path, "rb") as f:
            return x509.load_pem_x509_crl(f.read())

    def _update_registry(self, registry: dict):
        """Update the certificate registry (helper method)."""
        registry_path = self.ca_manager.cert_registry_path
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2)
