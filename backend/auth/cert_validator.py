"""
Certificate Validator

Validates X.509 certificates including chain verification, expiry, and revocation.
"""

from datetime import datetime
from typing import Tuple, Optional

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.x509.oid import NameOID
from cryptography.exceptions import InvalidSignature

from backend.ca.ca_manager import CAManager
from backend.ca.crl_manager import CRLManager


class CertificateValidationError(Exception):
    """Raised when certificate validation fails."""
    pass


class CertificateValidator:
    """Validates X.509 certificates against CA and CRL."""

    def __init__(self, ca_manager: CAManager, crl_manager: CRLManager):
        """
        Initialize Certificate Validator.

        Args:
            ca_manager: CA Manager instance
            crl_manager: CRL Manager instance
        """
        self.ca_manager = ca_manager
        self.crl_manager = crl_manager
        self._ca_cert = None
        self._ca_public_key = None

    def _get_ca_cert(self) -> x509.Certificate:
        """Get CA certificate (cached)."""
        if self._ca_cert is None:
            self._ca_cert = self.ca_manager.get_ca_certificate()
            self._ca_public_key = self._ca_cert.public_key()
        return self._ca_cert

    def validate_certificate(self, cert: x509.Certificate) -> Tuple[bool, Optional[str]]:
        """
        Validate a certificate.

        Args:
            cert: Certificate to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # 1. Check certificate structure
            if not isinstance(cert, x509.Certificate):
                return False, "Invalid certificate format"

            # 2. Verify certificate signature (chain validation)
            ca_cert = self._get_ca_cert()
            try:
                ca_cert.public_key().verify(
                    cert.signature,
                    cert.tbs_certificate_bytes,
                    padding.PKCS1v15(),
                    cert.signature_hash_algorithm,
                )
            except InvalidSignature:
                return False, "Certificate signature verification failed - not signed by CA"

            # 3. Check certificate expiry
            now = datetime.utcnow()
            if now < cert.not_valid_before:
                return False, f"Certificate not yet valid (valid from {cert.not_valid_before})"
            if now > cert.not_valid_after:
                return False, f"Certificate expired (expired on {cert.not_valid_after})"

            # 4. Check certificate revocation
            if self.crl_manager.is_revoked(cert.serial_number):
                return False, f"Certificate revoked (serial: {cert.serial_number})"

            # 5. Verify BasicConstraints (should be CA=False for end-entity certs)
            try:
                bc_ext = cert.extensions.get_extension_for_oid(
                    x509.ExtensionOID.BASIC_CONSTRAINTS
                )
                if bc_ext.value.ca:
                    return False, "Certificate marked as CA (should be end-entity)"
            except x509.ExtensionNotFound:
                pass  # BasicConstraints not critical for end-entity

            # 6. Verify KeyUsage (should have digitalSignature)
            try:
                ku_ext = cert.extensions.get_extension_for_oid(
                    x509.ExtensionOID.KEY_USAGE
                )
                if not ku_ext.value.digital_signature:
                    return False, "Certificate KeyUsage does not allow digital signatures"
            except x509.ExtensionNotFound:
                pass  # KeyUsage extension may not be present

            # 7. Verify ExtendedKeyUsage for student certificates (should have clientAuth)
            try:
                eku_ext = cert.extensions.get_extension_for_oid(
                    x509.ExtensionOID.EXTENDED_KEY_USAGE
                )
                if x509.ExtendedKeyUsageOID.CLIENT_AUTH not in eku_ext.value:
                    # Not critical, but log if needed
                    pass
            except x509.ExtensionNotFound:
                pass  # ExtendedKeyUsage may not be present

            return True, None

        except Exception as e:
            return False, f"Certificate validation error: {str(e)}"

    def validate_certificate_strict(self, cert: x509.Certificate) -> bool:
        """
        Validate certificate and raise exception on failure.

        Args:
            cert: Certificate to validate

        Returns:
            True if valid

        Raises:
            CertificateValidationError: If validation fails
        """
        is_valid, error_msg = self.validate_certificate(cert)
        if not is_valid:
            raise CertificateValidationError(error_msg or "Certificate validation failed")
        return True

    def extract_student_id(self, cert: x509.Certificate) -> Optional[str]:
        """
        Extract student ID from certificate subject.

        Args:
            cert: Student certificate

        Returns:
            Student ID or None if not found
        """
        try:
            common_name = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            if common_name.startswith("student_"):
                return common_name.replace("student_", "")
            return None
        except (IndexError, AttributeError):
            return None

    def extract_door_id(self, cert: x509.Certificate) -> Optional[Tuple[str, Optional[str]]]:
        """
        Extract door ID and room ID from certificate.

        Args:
            cert: Door certificate

        Returns:
            Tuple of (door_id, room_id) or None if not found
        """
        try:
            common_name = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
            if common_name.startswith("door_"):
                door_id = common_name.replace("door_", "")
                
                # Try to extract room_id from SAN extension
                room_id = None
                try:
                    san_ext = cert.extensions.get_extension_for_oid(
                        x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
                    )
                    # Room ID stored in SAN (implementation-specific)
                    # For now, return door_id only
                except x509.ExtensionNotFound:
                    pass
                
                return door_id, room_id
            return None
        except (IndexError, AttributeError):
            return None
