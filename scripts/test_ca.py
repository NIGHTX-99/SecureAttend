"""
Test script for CA functionality.

This script tests the Certificate Authority initialization and certificate issuance.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cryptography import x509
from backend.ca.ca_manager import CAManager
from backend.ca.cert_issuer import CertificateIssuer
from backend.ca.crl_manager import CRLManager


def test_ca_initialization():
    """Test CA initialization."""
    print("=" * 60)
    print("Test 1: CA Initialization")
    print("=" * 60)
    
    # Ensure test_data directory exists
    test_data_dir = Path("./test_data")
    test_data_dir.mkdir(exist_ok=True)
    
    ca_dir = test_data_dir / "ca"
    ca_manager = CAManager(ca_dir)
    
    # Initialize CA
    private_key, ca_cert = ca_manager.initialize_ca()
    
    assert ca_cert is not None, "CA certificate should be created"
    assert private_key is not None, "CA private key should be created"
    
    print("✓ CA initialized successfully")
    print(f"  CA Subject: {ca_cert.subject}")
    print(f"  CA Serial: {ca_cert.serial_number}")
    print(f"  Valid until: {ca_cert.not_valid_after}\n")
    
    return ca_manager


def test_student_certificate_issuance(ca_manager):
    """Test student certificate issuance."""
    print("=" * 60)
    print("Test 2: Student Certificate Issuance")
    print("=" * 60)
    
    test_data_dir = Path("./test_data")
    certs_dir = test_data_dir / "certs"
    issuer = CertificateIssuer(ca_manager, certs_dir)
    
    # Issue certificate to student
    student_id = "student_001"
    private_key, cert = issuer.issue_student_certificate(
        student_id=student_id,
        email="student@college.edu",
        validity_years=1
    )
    
    assert cert is not None, "Student certificate should be created"
    assert private_key is not None, "Student private key should be created"
    
    # Verify certificate chain
    ca_cert = ca_manager.get_ca_certificate()
    assert cert.issuer == ca_cert.subject, "Certificate should be issued by CA"
    
    print("✓ Student certificate issued successfully")
    print(f"  Student ID: {student_id}")
    print(f"  Certificate Subject: {cert.subject}")
    print(f"  Certificate Serial: {cert.serial_number}")
    print(f"  Valid until: {cert.not_valid_after}\n")
    
    return cert.serial_number


def test_door_certificate_issuance(ca_manager):
    """Test door certificate issuance."""
    print("=" * 60)
    print("Test 3: Door Certificate Issuance")
    print("=" * 60)
    
    test_data_dir = Path("./test_data")
    certs_dir = test_data_dir / "certs"
    issuer = CertificateIssuer(ca_manager, certs_dir)
    
    # Issue certificate to door
    door_id = "door_001"
    room_id = "CS101"
    private_key, cert = issuer.issue_door_certificate(
        door_id=door_id,
        room_id=room_id,
        validity_years=5
    )
    
    assert cert is not None, "Door certificate should be created"
    assert private_key is not None, "Door private key should be created"
    
    print("✓ Door certificate issued successfully")
    print(f"  Door ID: {door_id}")
    print(f"  Room ID: {room_id}")
    print(f"  Certificate Subject: {cert.subject}")
    print(f"  Certificate Serial: {cert.serial_number}\n")
    
    return cert.serial_number


def test_certificate_revocation(ca_manager, student_serial):
    """Test certificate revocation."""
    print("=" * 60)
    print("Test 4: Certificate Revocation")
    print("=" * 60)
    
    test_data_dir = Path("./test_data")
    crl_dir = test_data_dir / "crl"
    crl_manager = CRLManager(ca_manager, crl_dir)
    
    # Revoke student certificate
    crl_manager.revoke_certificate(
        serial_number=student_serial,
        revocation_reason=x509.ReasonFlags.key_compromise
    )
    
    # Check if revoked
    is_revoked = crl_manager.is_revoked(student_serial)
    assert is_revoked, "Certificate should be marked as revoked"
    
    # Get CRL
    crl = crl_manager.get_crl()
    assert crl is not None, "CRL should be generated"
    
    revoked_serials = [revoked_cert.serial_number for revoked_cert in crl]
    assert student_serial in revoked_serials, "Serial should be in CRL"
    
    print("✓ Certificate revocation successful")
    print(f"  Revoked Serial: {student_serial}")
    print(f"  CRL Last Update: {crl.last_update}")
    print(f"  CRL Next Update: {crl.next_update}\n")


def test_certificate_registry(ca_manager):
    """Test certificate registry."""
    print("=" * 60)
    print("Test 5: Certificate Registry")
    print("=" * 60)
    
    registry = ca_manager.get_registry()
    
    assert 'students' in registry, "Registry should have students"
    assert 'doors' in registry, "Registry should have doors"
    
    print("✓ Certificate registry check successful")
    print(f"  Students: {len(registry.get('students', {}))}")
    print(f"  Doors: {len(registry.get('doors', {}))}\n")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("PKI CA System - Phase 1 Testing")
    print("=" * 60 + "\n")
    
    try:
        # Run tests
        ca_manager = test_ca_initialization()
        student_serial = test_student_certificate_issuance(ca_manager)
        door_serial = test_door_certificate_issuance(ca_manager)
        test_certificate_revocation(ca_manager, student_serial)
        test_certificate_registry(ca_manager)
        
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
