"""
Initialize Backend System

This script initializes the CA, issues test certificates, and sets up database.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.ca.ca_manager import CAManager
from backend.ca.cert_issuer import CertificateIssuer
from backend.attendance.storage import AttendanceStorage


def initialize_system():
    """Initialize the backend system with test data."""
    print("=" * 60)
    print("Initializing SecureAttend Backend")
    print("=" * 60)

    # Paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    ca_dir = data_dir / "ca"
    certs_dir = data_dir / "certs"
    db_path = data_dir / "attendance.db"

    print("\n1. Initializing Certificate Authority...")
    ca_manager = CAManager(ca_dir)
    ca_manager.initialize_ca()
    print("   ✓ CA initialized")

    print("\n2. Issuing test certificates...")
    issuer = CertificateIssuer(ca_manager, certs_dir)

    # Issue student certificates
    for student_id in ["student_001", "student_002", "student_003"]:
        issuer.issue_student_certificate(
            student_id=student_id,
            email=f"{student_id}@college.edu",
            validity_years=1
        )
        print(f"   ✓ Issued certificate for {student_id}")

    # Issue door certificates
    doors = [
        ("door_001", "CS101"),
        ("door_002", "CS102"),
        ("door_003", "MATH201"),
    ]
    for door_id, room_id in doors:
        issuer.issue_door_certificate(
            door_id=door_id,
            room_id=room_id,
            validity_years=5
        )
        print(f"   ✓ Issued certificate for {door_id} (room: {room_id})")

    print("\n3. Initializing database and adding test authorizations...")
    attendance_storage = AttendanceStorage(db_path, ca_manager)

    # Add room authorizations
    authorizations = [
        ("student_001", "CS101", "CS101", "09:00", "10:30"),  # Student 1 in CS101
        ("student_001", "CS102", "CS102", "11:00", "12:30"),  # Student 1 in CS102
        ("student_002", "CS101", "CS101", "09:00", "10:30"),  # Student 2 in CS101
        ("student_002", "MATH201", "MATH201", "14:00", "15:30"),  # Student 2 in MATH201
        ("student_003", "CS102", "CS102", "11:00", "12:30"),  # Student 3 in CS102
    ]

    for student_id, room_id, course_id, start_time, end_time in authorizations:
        attendance_storage.add_room_authorization(
            student_id=student_id,
            room_id=room_id,
            course_id=course_id,
            start_time=start_time,
            end_time=end_time
        )
        print(f"   ✓ Authorized {student_id} for {room_id} ({start_time}-{end_time})")

    print("\n" + "=" * 60)
    print("Backend initialization complete!")
    print("=" * 60)
    print(f"\nCA Directory: {ca_dir}")
    print(f"Certificates Directory: {certs_dir}")
    print(f"Database: {db_path}")
    print("\nYou can now start the backend server:")
    print("  python -m backend.api.main")
    print("\nOr use uvicorn:")
    print("  uvicorn backend.api.main:app --reload")


if __name__ == '__main__':
    try:
        initialize_system()
    except Exception as e:
        print(f"\n✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
