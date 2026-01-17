"""
Door Scanner Simulator

Simulates a door scanner that reads QR codes and communicates with the backend.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import requests
import click

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from client.qr.generator import QRGenerator


class DoorScanner:
    """Simulates a door scanner device."""

    def __init__(self, door_id: str, room_id: str, backend_url: str = "http://localhost:8000"):
        """
        Initialize Door Scanner.

        Args:
            door_id: Door identifier
            room_id: Room identifier
            backend_url: Backend API URL
        """
        self.door_id = door_id
        self.room_id = room_id
        self.backend_url = backend_url

    def scan_qr_code(self, qr_json: str) -> Optional[dict]:
        """
        Process a scanned QR code.

        Args:
            qr_json: QR code JSON data

        Returns:
            Challenge data if successful, None otherwise
        """
        try:
            # Parse QR data
            qr_data = json.loads(qr_json)
            student_id = qr_data.get("student_id")
            certificate_pem = qr_data.get("certificate")
            previous_nonce = qr_data.get("nonce")

            if not all([student_id, certificate_pem]):
                print("✗ Invalid QR code: missing required fields")
                return None

            print(f"\n[Scanner] QR Code scanned:")
            print(f"  Student: {student_id}")
            print(f"  Door: {self.door_id}")
            print(f"  Room: {self.room_id}")

            # Request challenge from backend
            print(f"\n[Scanner] Requesting challenge from backend...")
            response = requests.post(
                f"{self.backend_url}/api/auth/challenge",
                json={
                    "student_id": student_id,
                    "certificate_pem": certificate_pem,
                    "room_id": self.room_id,
                    "door_id": self.door_id,
                    "previous_nonce": previous_nonce,
                }
            )

            if response.status_code != 200:
                print(f"✗ Error: {response.text}")
                return None

            challenge_data = response.json()
            print(f"✓ Challenge received: {challenge_data['challenge_id']}")
            
            return challenge_data

        except json.JSONDecodeError:
            print("✗ Invalid QR code format")
            return None
        except requests.exceptions.ConnectionError:
            print(f"✗ Cannot connect to backend at {self.backend_url}")
            return None
        except Exception as e:
            print(f"✗ Error: {e}")
            return None

    def verify_signature(
        self,
        challenge_id: str,
        challenge: dict,
        signature: str,
        certificate_pem: str
    ) -> bool:
        """
        Verify signed challenge with backend.

        Args:
            challenge_id: Challenge identifier
            challenge: Challenge dictionary
            signature: Hex-encoded signature
            certificate_pem: Student certificate PEM

        Returns:
            True if access granted, False otherwise
        """
        try:
            print(f"\n[Scanner] Verifying signature with backend...")
            response = requests.post(
                f"{self.backend_url}/api/auth/verify",
                json={
                    "challenge_id": challenge_id,
                    "challenge": challenge,
                    "signature": signature,
                    "certificate_pem": certificate_pem,
                }
            )

            if response.status_code != 200:
                print(f"✗ Error: {response.text}")
                return False

            result = response.json()

            if result.get("access_granted"):
                print("✓ ACCESS GRANTED - Door unlocking...")
                attendance = result.get("attendance_record", {})
                print(f"  Attendance recorded for {attendance.get('student_id')} at {attendance.get('timestamp')}")
                return True
            else:
                print(f"✗ ACCESS DENIED: {result.get('message')}")
                return False

        except requests.exceptions.ConnectionError:
            print(f"✗ Cannot connect to backend at {self.backend_url}")
            return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False


@click.command()
@click.option('--door-id', default='door_001', help='Door identifier')
@click.option('--room-id', default='CS101', help='Room identifier')
@click.option('--backend-url', default='http://localhost:8000', help='Backend API URL')
@click.argument('qr_file', type=click.Path(exists=True))
def scan_and_verify(door_id, room_id, backend_url, qr_file):
    """Simulate door scanner scanning QR code and verifying authentication"""
    scanner = DoorScanner(door_id, room_id, backend_url)

    # Read QR code data from file
    with open(qr_file, 'r') as f:
        qr_json = f.read()

    # Scan QR code and get challenge
    challenge_data = scanner.scan_qr_code(qr_json)
    if not challenge_data:
        sys.exit(1)

    # Display challenge (in real scenario, this would be sent to client)
    print(f"\n[Scanner] Challenge to sign:")
    print(json.dumps(challenge_data["challenge"], indent=2))
    print(f"\nSave this challenge to a file and have the student sign it.")
    print(f"Then verify with:")
    print(f"  python -m simulator.scanner verify --challenge-file challenge.json --signature <signature>")


@click.command()
@click.option('--door-id', default='door_001', help='Door identifier')
@click.option('--room-id', default='CS101', help='Room identifier')
@click.option('--backend-url', default='http://localhost:8000', help='Backend API URL')
@click.option('--challenge-file', required=True, help='Challenge JSON file')
@click.option('--signature', required=True, help='Hex-encoded signature')
@click.option('--certificate-file', required=True, help='Student certificate PEM file')
def verify(door_id, room_id, backend_url, challenge_file, signature, certificate_file):
    """Verify a signed challenge"""
    scanner = DoorScanner(door_id, room_id, backend_url)

    # Load challenge and certificate
    with open(challenge_file, 'r') as f:
        challenge_data = json.load(f)

    with open(certificate_file, 'r') as f:
        certificate_pem = f.read()

    challenge_id = challenge_data.get("challenge_id")
    challenge = challenge_data.get("challenge")

    if not challenge_id or not challenge:
        print("✗ Invalid challenge file format")
        sys.exit(1)

    # Verify
    success = scanner.verify_signature(challenge_id, challenge, signature, certificate_pem)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    # Create CLI group
    @click.group()
    def cli():
        """Door Scanner Simulator"""
        pass

    cli.add_command(scan_and_verify, name='scan')
    cli.add_command(verify)
    cli()
