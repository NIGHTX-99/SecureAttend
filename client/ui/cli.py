"""
Client CLI

Command-line interface for SecureAttend client.
"""

import sys
from pathlib import Path
import click
import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from client.qr.generator import QRGenerator, load_student_certificate
from client.signing.key_manager import KeyManager
from client.signing.signer import ChallengeSigner
from backend.auth.challenge_gen import Challenge


@click.group()
@click.option('--data-dir', default='./data', help='Data directory')
@click.option('--backend-url', default='http://localhost:8000', help='Backend API URL')
@click.pass_context
def cli(ctx, data_dir, backend_url):
    """SecureAttend Client CLI"""
    ctx.ensure_object(dict)
    ctx.obj['data_dir'] = Path(data_dir)
    ctx.obj['backend_url'] = backend_url
    ctx.obj['keys_dir'] = ctx.obj['data_dir'] / 'certs'
    ctx.obj['qr_generator'] = QRGenerator()
    ctx.obj['key_manager'] = KeyManager(ctx.obj['keys_dir'])


@cli.command()
@click.argument('student_id')
@click.option('--save', help='Save QR code to file (PNG)')
@click.pass_context
def show_qr(ctx, student_id, save):
    """Display QR code for authentication"""
    try:
        # Load certificate
        cert_pem = ctx.obj['key_manager'].get_certificate_pem(student_id)

        # Generate QR code
        output_path = Path(save) if save else None
        img, qr_json = ctx.obj['qr_generator'].generate_qr_code(
            student_id=student_id,
            certificate_pem=cert_pem,
            output_path=output_path,
            display=True
        )

        click.echo(f"\n✓ QR code generated for {student_id}")
        if save:
            click.echo(f"  Saved to: {save}")

    except FileNotFoundError as e:
        click.echo(f"✗ Error: {e}", err=True)
        click.echo(f"\nMake sure student certificate exists at:")
        click.echo(f"  {ctx.obj['keys_dir']}/students/{student_id}/certificate.pem", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('student_id')
@click.argument('challenge_id')
@click.option('--challenge-file', help='JSON file containing challenge')
@click.pass_context
def sign_challenge(ctx, student_id, challenge_id, challenge_file):
    """Sign an authentication challenge"""
    try:
        # Load student keys
        private_key, certificate = ctx.obj['key_manager'].load_student_keys(student_id)

        # Load challenge
        if challenge_file:
            with open(challenge_file, 'r') as f:
                import json
                challenge_dict = json.load(f)
        else:
            click.echo("Error: Challenge data required. Use --challenge-file", err=True)
            sys.exit(1)

        # Create challenge object
        challenge = Challenge.from_dict(challenge_dict)

        # Sign challenge
        signature_hex = ChallengeSigner.sign_challenge_hex(challenge, private_key)

        # Get certificate PEM
        cert_pem = ctx.obj['key_manager'].get_certificate_pem(student_id)

        # Display result
        click.echo(f"\n✓ Challenge signed for {student_id}")
        click.echo(f"\nChallenge ID: {challenge_id}")
        click.echo(f"Signature: {signature_hex}")
        click.echo(f"\nSend this to the door scanner:")
        click.echo(f"  Challenge ID: {challenge_id}")
        click.echo(f"  Signature: {signature_hex}")

    except FileNotFoundError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('student_id')
@click.argument('room_id')
@click.argument('door_id')
@click.pass_context
def authenticate(ctx, student_id, room_id, door_id):
    """Complete authentication flow (QR -> Challenge -> Sign -> Verify)"""
    try:
        backend_url = ctx.obj['backend_url']
        key_manager = ctx.obj['key_manager']
        qr_generator = ctx.obj['qr_generator']

        click.echo(f"\n=== SecureAttend Authentication Flow ===\n")
        click.echo(f"Student: {student_id}")
        click.echo(f"Room: {room_id}")
        click.echo(f"Door: {door_id}\n")

        # Step 1: Generate QR code
        click.echo("Step 1: Generating QR code...")
        cert_pem = key_manager.get_certificate_pem(student_id)
        qr_data = qr_generator.create_qr_data(student_id, cert_pem)
        click.echo("✓ QR code data generated")

        # Step 2: Request challenge from backend
        click.echo("\nStep 2: Requesting challenge from backend...")
        challenge_response = requests.post(
            f"{backend_url}/api/auth/challenge",
            json={
                "student_id": student_id,
                "certificate_pem": cert_pem,
                "room_id": room_id,
                "door_id": door_id,
                "previous_nonce": qr_data["nonce"],
            }
        )

        if challenge_response.status_code != 200:
            click.echo(f"✗ Error: {challenge_response.text}", err=True)
            sys.exit(1)

        challenge_data = challenge_response.json()
        challenge_id = challenge_data["challenge_id"]
        challenge_dict = challenge_data["challenge"]
        click.echo(f"✓ Challenge received: {challenge_id}")

        # Step 3: Sign challenge
        click.echo("\nStep 3: Signing challenge...")
        private_key, _ = key_manager.load_student_keys(student_id)
        challenge = Challenge.from_dict(challenge_dict)
        signature_hex = ChallengeSigner.sign_challenge_hex(challenge, private_key)
        click.echo("✓ Challenge signed")

        # Step 4: Verify with backend
        click.echo("\nStep 4: Verifying with backend...")
        verify_response = requests.post(
            f"{backend_url}/api/auth/verify",
            json={
                "challenge_id": challenge_id,
                "challenge": challenge_dict,
                "signature": signature_hex,
                "certificate_pem": cert_pem,
            }
        )

        if verify_response.status_code != 200:
            click.echo(f"✗ Error: {verify_response.text}", err=True)
            sys.exit(1)

        result = verify_response.json()
        
        if result["access_granted"]:
            click.echo("✓ ACCESS GRANTED!")
            click.echo(f"\nAttendance recorded:")
            attendance = result.get("attendance_record", {})
            click.echo(f"  Student: {attendance.get('student_id')}")
            click.echo(f"  Room: {attendance.get('room_id')}")
            click.echo(f"  Time: {attendance.get('timestamp')}")
        else:
            click.echo("✗ ACCESS DENIED", err=True)
            click.echo(f"Reason: {result.get('message')}", err=True)

    except requests.exceptions.ConnectionError:
        click.echo(f"✗ Error: Cannot connect to backend at {backend_url}", err=True)
        click.echo("Make sure the backend server is running:", err=True)
        click.echo("  python scripts/start_backend.py", err=True)
        sys.exit(1)
    except FileNotFoundError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    cli()
