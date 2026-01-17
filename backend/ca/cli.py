"""
Command-line interface for CA operations.

This allows initialization and certificate issuance from the command line.
"""

import click
from pathlib import Path

from backend.ca.ca_manager import CAManager
from backend.ca.cert_issuer import CertificateIssuer
from backend.ca.crl_manager import CRLManager


@click.group()
@click.option('--ca-dir', default='./data/ca', help='CA directory')
@click.option('--certs-dir', default='./data/certs', help='Certificates directory')
@click.option('--crl-dir', default='./data/crl', help='CRL directory')
@click.pass_context
def cli(ctx, ca_dir, certs_dir, crl_dir):
    """PKI Certificate Authority CLI"""
    ctx.ensure_object(dict)
    ctx.obj['ca_dir'] = Path(ca_dir)
    ctx.obj['certs_dir'] = Path(certs_dir)
    ctx.obj['crl_dir'] = Path(crl_dir)


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize the Certificate Authority"""
    ca_dir = ctx.obj['ca_dir']
    ca_manager = CAManager(ca_dir)
    
    click.echo("Initializing Certificate Authority...")
    ca_manager.initialize_ca()
    click.echo("✓ CA initialized successfully!")


@cli.command()
@click.argument('student_id')
@click.option('--email', help='Student email address')
@click.option('--validity-years', default=1, help='Certificate validity in years')
@click.pass_context
def issue_student(ctx, student_id, email, validity_years):
    """Issue a certificate to a student"""
    ca_dir = ctx.obj['ca_dir']
    certs_dir = ctx.obj['certs_dir']
    
    ca_manager = CAManager(ca_dir)
    issuer = CertificateIssuer(ca_manager, certs_dir)
    
    click.echo(f"Issuing certificate for student {student_id}...")
    issuer.issue_student_certificate(
        student_id=student_id,
        email=email,
        validity_years=validity_years
    )
    click.echo("✓ Certificate issued successfully!")


@cli.command()
@click.argument('door_id')
@click.argument('room_id')
@click.option('--validity-years', default=5, help='Certificate validity in years')
@click.pass_context
def issue_door(ctx, door_id, room_id, validity_years):
    """Issue a certificate to a door device"""
    ca_dir = ctx.obj['ca_dir']
    certs_dir = ctx.obj['certs_dir']
    
    ca_manager = CAManager(ca_dir)
    issuer = CertificateIssuer(ca_manager, certs_dir)
    
    click.echo(f"Issuing certificate for door {door_id} (room: {room_id})...")
    issuer.issue_door_certificate(
        door_id=door_id,
        room_id=room_id,
        validity_years=validity_years
    )
    click.echo("✓ Certificate issued successfully!")


@cli.command()
@click.argument('student_id')
@click.option('--reason', default='unspecified', 
              type=click.Choice(['unspecified', 'key_compromise', 'superseded', 'cessation_of_operation']),
              help='Revocation reason')
@click.pass_context
def revoke_student(ctx, student_id, reason):
    """Revoke a student certificate"""
    ca_dir = ctx.obj['ca_dir']
    crl_dir = ctx.obj['crl_dir']
    
    ca_manager = CAManager(ca_dir)
    crl_manager = CRLManager(ca_manager, crl_dir)
    
    click.echo(f"Revoking certificate for student {student_id}...")
    crl_manager.revoke_student_certificate(student_id, reason)
    click.echo("✓ Certificate revoked successfully!")


@cli.command()
@click.pass_context
def list_certs(ctx):
    """List all issued certificates"""
    ca_dir = ctx.obj['ca_dir']
    
    ca_manager = CAManager(ca_dir)
    registry = ca_manager.get_registry()
    
    click.echo("\n=== Certificate Registry ===\n")
    
    click.echo("Students:")
    for student_id, info in registry.get('students', {}).items():
        status = "REVOKED" if info.get('revoked') else "VALID"
        click.echo(f"  {student_id}: Serial {info['serial_number']} - {status}")
    
    click.echo("\nDoors:")
    for door_id, info in registry.get('doors', {}).items():
        status = "REVOKED" if info.get('revoked') else "VALID"
        click.echo(f"  {door_id}: Serial {info['serial_number']} - {status}")


if __name__ == '__main__':
    cli()
