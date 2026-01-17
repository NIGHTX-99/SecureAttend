"""
Challenge Signer

Signs authentication challenges with student private keys.
"""

import json
import hashlib
from typing import Dict

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa

from backend.auth.challenge_gen import Challenge


class ChallengeSigner:
    """Signs authentication challenges."""

    @staticmethod
    def sign_challenge(
        challenge: Challenge,
        private_key: rsa.RSAPrivateKey
    ) -> bytes:
        """
        Sign an authentication challenge.

        Args:
            challenge: Challenge object to sign
            private_key: Student's private key

        Returns:
            Digital signature bytes
        """
        # Serialize challenge to JSON
        challenge_json = challenge.to_json().encode('utf-8')

        # Sign using RSA-SHA256 with PKCS#1 v1.5 padding
        signature = private_key.sign(
            challenge_json,
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        return signature

    @staticmethod
    def sign_challenge_hex(
        challenge: Challenge,
        private_key: rsa.RSAPrivateKey
    ) -> str:
        """
        Sign challenge and return hex-encoded signature.

        Args:
            challenge: Challenge object to sign
            private_key: Student's private key

        Returns:
            Hex-encoded signature string
        """
        signature_bytes = ChallengeSigner.sign_challenge(challenge, private_key)
        return signature_bytes.hex()

    @staticmethod
    def sign_challenge_from_dict(
        challenge_dict: Dict,
        private_key: rsa.RSAPrivateKey
    ) -> str:
        """
        Sign challenge from dictionary and return hex-encoded signature.

        Args:
            challenge_dict: Challenge dictionary
            private_key: Student's private key

        Returns:
            Hex-encoded signature string
        """
        challenge = Challenge.from_dict(challenge_dict)
        return ChallengeSigner.sign_challenge_hex(challenge, private_key)
