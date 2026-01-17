"""
Signature Verification

Verifies digital signatures on challenges and other data.
"""

import json
import hashlib
from typing import Tuple, Optional

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

from backend.auth.challenge_gen import Challenge


class SignatureVerificationError(Exception):
    """Raised when signature verification fails."""
    pass


class SignatureVerifier:
    """Verifies digital signatures using certificate public keys."""

    @staticmethod
    def verify_challenge_signature(
        challenge: Challenge,
        signature: bytes,
        certificate: x509.Certificate
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify a signature on a challenge.

        Args:
            challenge: Challenge object that was signed
            signature: Digital signature bytes
            certificate: Certificate containing the public key

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Get public key from certificate
            public_key = certificate.public_key()

            # Serialize challenge to JSON for signing
            challenge_json = challenge.to_json().encode('utf-8')

            # Hash the challenge (SHA-256)
            challenge_hash = hashlib.sha256(challenge_json).digest()

            # Verify signature
            # Note: Assuming RSA PKCS1v15 padding (standard for RSA-SHA256)
            try:
                public_key.verify(
                    signature,
                    challenge_json,  # Verify against original message, not hash
                    padding.PKCS1v15(),
                    hashes.SHA256(),
                )
                return True, None
            except InvalidSignature:
                return False, "Signature verification failed - invalid signature"
            except Exception as e:
                return False, f"Signature verification error: {str(e)}"

        except Exception as e:
            return False, f"Signature verification failed: {str(e)}"

    @staticmethod
    def verify_challenge_signature_strict(
        challenge: Challenge,
        signature: bytes,
        certificate: x509.Certificate
    ) -> bool:
        """
        Verify signature and raise exception on failure.

        Args:
            challenge: Challenge object that was signed
            signature: Digital signature bytes
            certificate: Certificate containing the public key

        Returns:
            True if signature is valid

        Raises:
            SignatureVerificationError: If verification fails
        """
        is_valid, error_msg = SignatureVerifier.verify_challenge_signature(
            challenge, signature, certificate
        )
        if not is_valid:
            raise SignatureVerificationError(error_msg or "Signature verification failed")
        return True

    @staticmethod
    def verify_data_signature(
        data: bytes,
        signature: bytes,
        certificate: x509.Certificate,
        hash_algorithm = hashes.SHA256()
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify a signature on arbitrary data.

        Args:
            data: Data that was signed
            signature: Digital signature bytes
            certificate: Certificate containing the public key
            hash_algorithm: Hash algorithm used (default: SHA256)

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            public_key = certificate.public_key()

            try:
                public_key.verify(
                    signature,
                    data,
                    padding.PKCS1v15(),
                    hash_algorithm,
                )
                return True, None
            except InvalidSignature:
                return False, "Signature verification failed - invalid signature"
            except Exception as e:
                return False, f"Signature verification error: {str(e)}"

        except Exception as e:
            return False, f"Signature verification failed: {str(e)}"

    @staticmethod
    def verify_hash_signature(
        data_hash: bytes,
        signature: bytes,
        certificate: x509.Certificate,
        hash_algorithm = hashes.SHA256()
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify a signature on a pre-computed hash.

        Note: This assumes the signature was created by signing the hash directly.
        In standard PKCS#1 v1.5, you sign the message, not the hash. This method
        is provided for specific use cases.

        Args:
            data_hash: Hash of the data that was signed
            signature: Digital signature bytes
            certificate: Certificate containing the public key
            hash_algorithm: Hash algorithm used (default: SHA256)

        Returns:
            Tuple of (is_valid, error_message)
        """
        # For RSA PKCS#1 v1.5, we actually need to sign the full message
        # This method is a placeholder for hash-based verification patterns
        # In practice, use verify_data_signature instead
        return False, "Hash-based signature verification not supported - use verify_data_signature"
