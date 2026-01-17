"""
Integration Tests

End-to-end tests for the complete authentication flow.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import requests
from cryptography import x509

from backend.ca.ca_manager import CAManager
from backend.ca.cert_issuer import CertificateIssuer
from backend.attendance.storage import AttendanceStorage
from client.qr.generator import QRGenerator
from client.signing.key_manager import KeyManager
from client.signing.signer import ChallengeSigner
from backend.auth.challenge_gen import Challenge


@pytest.fixture
def test_setup(tmp_path):
    """Set up test environment."""
    # Setup paths
    ca_dir = tmp_path / "ca"
    certs_dir = tmp_path / "certs"
    db_path = tmp_path / "test.db"

    # Initialize CA
    ca_manager = CAManager(ca_dir)
    ca_manager.initialize_ca()

    # Issue test certificates
    issuer = CertificateIssuer(ca_manager, certs_dir)
    private_key, cert = issuer.issue_student_certificate(
        student_id="test_student_001",
        email="test@example.com"
    )
    issuer.issue_door_certificate(door_id="test_door_001", room_id="TEST101")

    # Setup attendance storage
    storage = AttendanceStorage(db_path, ca_manager)
    storage.add_room_authorization(
        student_id="test_student_001",
        room_id="TEST101"
    )

    return {
        "ca_manager": ca_manager,
        "certs_dir": certs_dir,
        "storage": storage,
        "student_id": "test_student_001",
        "room_id": "TEST101",
        "door_id": "test_door_001",
    }


def test_qr_generation(test_setup):
    """Test QR code generation."""
    qr_gen = QRGenerator()
    cert_path = test_setup["certs_dir"] / "students" / "test_student_001" / "certificate.pem"
    
    with open(cert_path, "rb") as f:
        cert_pem = f.read().decode('utf-8')

    qr_data = qr_gen.create_qr_data(
        student_id="test_student_001",
        certificate_pem=cert_pem
    )

    assert "student_id" in qr_data
    assert "certificate" in qr_data
    assert "nonce" in qr_data
    assert qr_data["student_id"] == "test_student_001"


def test_challenge_signing(test_setup):
    """Test challenge signing."""
    key_manager = KeyManager(test_setup["certs_dir"])
    private_key, cert = key_manager.load_student_keys("test_student_001")

    # Create test challenge
    challenge = Challenge(
        nonce="test_nonce_123",
        timestamp="2024-01-01T12:00:00Z",
        room_id="TEST101",
        door_id="test_door_001",
        challenge_id="test_challenge_001"
    )

    # Sign challenge
    signature = ChallengeSigner.sign_challenge_hex(challenge, private_key)

    assert signature is not None
    assert len(signature) > 0
    # Should be hex-encoded
    assert all(c in '0123456789abcdef' for c in signature.lower())


def test_certificate_validation(test_setup):
    """Test certificate validation."""
    from backend.auth.cert_validator import CertificateValidator
    from backend.ca.crl_manager import CRLManager

    crl_manager = CRLManager(test_setup["ca_manager"], test_setup["certs_dir"] / "crl")
    validator = CertificateValidator(test_setup["ca_manager"], crl_manager)

    cert_path = test_setup["certs_dir"] / "students" / "test_student_001" / "certificate.pem"
    with open(cert_path, "rb") as f:
        cert = x509.load_pem_x509_certificate(f.read())

    is_valid, error = validator.validate_certificate(cert)
    assert is_valid, f"Certificate validation failed: {error}"

    # Extract student ID
    student_id = validator.extract_student_id(cert)
    assert student_id == "test_student_001"


def test_end_to_end_flow(test_setup):
    """Test complete end-to-end authentication flow."""
    # This test would require a running backend server
    # For now, we test the components separately
    
    # 1. Generate QR code
    qr_gen = QRGenerator()
    cert_path = test_setup["certs_dir"] / "students" / "test_student_001" / "certificate.pem"
    with open(cert_path, "rb") as f:
        cert_pem = f.read().decode('utf-8')

    qr_data = qr_gen.create_qr_data("test_student_001", cert_pem)
    
    # 2. Generate challenge (simulating backend)
    from backend.auth.challenge_gen import ChallengeGenerator
    challenge_gen = ChallengeGenerator()
    challenge = challenge_gen.generate_challenge(
        room_id="TEST101",
        door_id="test_door_001",
        previous_nonce=qr_data["nonce"]
    )

    # 3. Sign challenge
    key_manager = KeyManager(test_setup["certs_dir"])
    private_key, _ = key_manager.load_student_keys("test_student_001")
    signature = ChallengeSigner.sign_challenge_hex(challenge, private_key)

    # 4. Verify signature (simulating backend)
    from backend.auth.signature_verify import SignatureVerifier
    with open(cert_path, "rb") as f:
        cert = x509.load_pem_x509_certificate(f.read())

    signature_bytes = bytes.fromhex(signature)
    is_valid, error = SignatureVerifier.verify_challenge_signature(
        challenge, signature_bytes, cert
    )

    assert is_valid, f"Signature verification failed: {error}"

    # 5. Check room authorization
    is_authorized, auth_error = test_setup["storage"].check_room_authorization(
        student_id="test_student_001",
        room_id="TEST101"
    )

    assert is_authorized, f"Room authorization failed: {auth_error}"
