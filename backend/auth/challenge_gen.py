"""
Challenge Generator

Generates cryptographic challenges for challenge-response authentication.
"""

import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class Challenge:
    """Represents an authentication challenge."""

    nonce: str  # Random nonce
    timestamp: str  # ISO format timestamp
    room_id: str  # Requested room
    door_id: str  # Door/scanner identifier
    previous_nonce: Optional[str] = None  # Nonce from QR code
    challenge_id: Optional[str] = None  # Unique challenge identifier

    def to_dict(self) -> Dict:
        """Convert challenge to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert challenge to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict) -> 'Challenge':
        """Create challenge from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Challenge':
        """Create challenge from JSON string."""
        return cls.from_dict(json.loads(json_str))


class ChallengeGenerator:
    """Generates cryptographic challenges."""

    def __init__(self, nonce_size: int = 32, challenge_ttl_seconds: int = 30):
        """
        Initialize Challenge Generator.

        Args:
            nonce_size: Size of nonce in bytes (default: 32 = 256 bits)
            challenge_ttl_seconds: Challenge time-to-live in seconds (default: 30)
        """
        self.nonce_size = nonce_size
        self.challenge_ttl_seconds = challenge_ttl_seconds
        self.seen_nonces: Dict[str, datetime] = {}  # Track seen nonces
        self.generated_challenges: Dict[str, Challenge] = {}  # Track generated challenges

    def generate_nonce(self) -> str:
        """
        Generate a cryptographically secure random nonce.

        Returns:
            Hex-encoded nonce string
        """
        nonce_bytes = secrets.token_bytes(self.nonce_size)
        return nonce_bytes.hex()

    def generate_challenge(
        self,
        room_id: str,
        door_id: str,
        previous_nonce: Optional[str] = None
    ) -> Challenge:
        """
        Generate a new authentication challenge.

        Args:
            room_id: Requested room identifier
            door_id: Door/scanner identifier
            previous_nonce: Optional nonce from QR code

        Returns:
            Challenge object
        """
        # Generate new nonce
        nonce = self.generate_nonce()

        # Generate challenge ID for tracking
        challenge_id = self.generate_nonce()[:16]  # Shorter ID for tracking

        # Create challenge
        challenge = Challenge(
            nonce=nonce,
            timestamp=datetime.utcnow().isoformat() + "Z",
            room_id=room_id,
            door_id=door_id,
            previous_nonce=previous_nonce,
            challenge_id=challenge_id,
        )

        # Store challenge for validation
        self.generated_challenges[challenge_id] = challenge

        # Track nonce (prevent reuse)
        if previous_nonce:
            self.seen_nonces[previous_nonce] = datetime.utcnow()

        return challenge

    def validate_challenge(self, challenge: Challenge) -> Tuple[bool, Optional[str]]:
        """
        Validate a challenge (check freshness, nonce reuse, etc.).

        Args:
            challenge: Challenge to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if challenge exists in our generated list
            if challenge.challenge_id:
                if challenge.challenge_id not in self.generated_challenges:
                    return False, "Unknown challenge ID"

                # Get original challenge
                original = self.generated_challenges[challenge.challenge_id]

                # Verify nonce matches
                if challenge.nonce != original.nonce:
                    return False, "Challenge nonce mismatch"

            # Parse timestamp
            try:
                challenge_time = datetime.fromisoformat(challenge.timestamp.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return False, "Invalid challenge timestamp format"

            # Check challenge freshness (time-to-live)
            now = datetime.utcnow(challenge_time.tzinfo) if challenge_time.tzinfo else datetime.utcnow()
            age_seconds = (now - challenge_time).total_seconds()

            if age_seconds > self.challenge_ttl_seconds:
                return False, f"Challenge expired (age: {age_seconds:.1f}s, TTL: {self.challenge_ttl_seconds}s)"

            if age_seconds < 0:
                return False, "Challenge timestamp in the future"

            # Check previous nonce reuse (if present)
            if challenge.previous_nonce:
                if challenge.previous_nonce in self.seen_nonces:
                    # Check if recently seen (within 5 minutes)
                    seen_time = self.seen_nonces[challenge.previous_nonce]
                    if (now - seen_time).total_seconds() < 300:  # 5 minutes
                        return False, "Previous nonce reuse detected (possible replay attack)"

            return True, None

        except Exception as e:
            return False, f"Challenge validation error: {str(e)}"

    def cleanup_expired_challenges(self, max_age_seconds: int = 300):
        """
        Clean up expired challenges and old nonces.

        Args:
            max_age_seconds: Maximum age for challenges/nonces to keep
        """
        now = datetime.utcnow()
        
        # Clean challenges
        expired_challenges = []
        for challenge_id, challenge in self.generated_challenges.items():
            try:
                challenge_time = datetime.fromisoformat(challenge.timestamp.replace("Z", "+00:00"))
                age = (now - challenge_time).total_seconds()
                if age > max_age_seconds:
                    expired_challenges.append(challenge_id)
            except (ValueError, AttributeError):
                expired_challenges.append(challenge_id)

        for challenge_id in expired_challenges:
            del self.generated_challenges[challenge_id]

        # Clean nonces
        expired_nonces = []
        for nonce, seen_time in self.seen_nonces.items():
            age = (now - seen_time).total_seconds()
            if age > max_age_seconds:
                expired_nonces.append(nonce)

        for nonce in expired_nonces:
            del self.seen_nonces[nonce]

    def get_challenge_by_id(self, challenge_id: str) -> Optional[Challenge]:
        """
        Get a challenge by its ID.

        Args:
            challenge_id: Challenge identifier

        Returns:
            Challenge or None if not found
        """
        return self.generated_challenges.get(challenge_id)
