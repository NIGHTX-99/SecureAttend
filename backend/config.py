"""
Configuration and Dependency Injection

Manages global instances and configuration for the backend.
"""

from pathlib import Path
from functools import lru_cache

from backend.ca.ca_manager import CAManager
from backend.ca.crl_manager import CRLManager
from backend.auth.cert_validator import CertificateValidator
from backend.auth.challenge_gen import ChallengeGenerator
from backend.attendance.storage import AttendanceStorage
from backend.attendance.recorder import AttendanceRecorder

# Default paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CA_DIR = DATA_DIR / "ca"
CERTS_DIR = DATA_DIR / "certs"
CRL_DIR = DATA_DIR / "crl"
DB_PATH = DATA_DIR / "attendance.db"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_ca_manager() -> CAManager:
    """Get CA Manager instance (singleton)."""
    return CAManager(CA_DIR)


@lru_cache()
def get_crl_manager() -> CRLManager:
    """Get CRL Manager instance (singleton)."""
    return CRLManager(get_ca_manager(), CRL_DIR)


@lru_cache()
def get_cert_validator() -> CertificateValidator:
    """Get Certificate Validator instance (singleton)."""
    return CertificateValidator(get_ca_manager(), get_crl_manager())


@lru_cache()
def get_challenge_generator() -> ChallengeGenerator:
    """Get Challenge Generator instance (singleton)."""
    return ChallengeGenerator(nonce_size=32, challenge_ttl_seconds=30)


@lru_cache()
def get_attendance_storage() -> AttendanceStorage:
    """Get Attendance Storage instance (singleton)."""
    return AttendanceStorage(DB_PATH, get_ca_manager())


@lru_cache()
def get_attendance_recorder() -> AttendanceRecorder:
    """Get Attendance Recorder instance (singleton)."""
    return AttendanceRecorder(get_attendance_storage())
