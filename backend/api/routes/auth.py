"""
Authentication Routes

Handles challenge generation and verification.
"""

from fastapi import APIRouter, HTTPException, status
from cryptography import x509
from cryptography.hazmat.primitives import serialization

from backend.api.models import (
    ChallengeRequest,
    ChallengeResponse,
    ChallengeVerificationRequest,
    ChallengeVerificationResponse,
    ErrorResponse,
)
from backend.auth.cert_validator import CertificateValidator, CertificateValidationError
from backend.auth.challenge_gen import ChallengeGenerator, Challenge
from backend.auth.signature_verify import SignatureVerifier, SignatureVerificationError
from backend.attendance.storage import AttendanceStorage
from backend.attendance.recorder import AttendanceRecorder

# Global instances (in production, use dependency injection)
from backend.config import get_ca_manager, get_crl_manager, get_challenge_generator, get_cert_validator, get_attendance_storage, get_attendance_recorder

router = APIRouter()


@router.post("/challenge", response_model=ChallengeResponse)
async def generate_challenge(request: ChallengeRequest):
    """
    Generate an authentication challenge for a student.

    This endpoint is called by the door scanner after reading a QR code.
    """
    try:
        # Parse certificate from PEM
        try:
            cert = x509.load_pem_x509_certificate(request.certificate_pem.encode('utf-8'))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid certificate format: {str(e)}"
            )

        # Validate certificate
        cert_validator = get_cert_validator()
        is_valid, error_msg = cert_validator.validate_certificate(cert)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Certificate validation failed: {error_msg}"
            )

        # Extract student ID from certificate
        student_id = cert_validator.extract_student_id(cert)
        if not student_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract student ID from certificate"
            )

        # Verify student_id matches request
        if student_id != request.student_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student ID in certificate does not match request"
            )

        # Generate challenge
        challenge_gen = get_challenge_generator()
        challenge = challenge_gen.generate_challenge(
            room_id=request.room_id,
            door_id=request.door_id,
            previous_nonce=request.previous_nonce
        )

        return ChallengeResponse(
            challenge_id=challenge.challenge_id,
            challenge=challenge.to_dict(),
            message="Challenge generated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/verify", response_model=ChallengeVerificationResponse)
async def verify_challenge(request: ChallengeVerificationRequest):
    """
    Verify a signed challenge and grant/deny access.

    This endpoint is called by the door scanner after receiving the signed challenge from the client.
    """
    try:
        # Parse certificate from PEM
        try:
            cert = x509.load_pem_x509_certificate(request.certificate_pem.encode('utf-8'))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid certificate format: {str(e)}"
            )

        # Reconstruct challenge from dictionary
        try:
            challenge = Challenge.from_dict(request.challenge)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid challenge format: {str(e)}"
            )

        # Verify challenge ID matches
        challenge_gen = get_challenge_generator()
        stored_challenge = challenge_gen.get_challenge_by_id(request.challenge_id)
        if not stored_challenge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired challenge ID"
            )

        # Validate certificate
        cert_validator = get_cert_validator()
        is_valid, error_msg = cert_validator.validate_certificate(cert)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Certificate validation failed: {error_msg}"
            )

        # Extract student ID
        student_id = cert_validator.extract_student_id(cert)
        if not student_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract student ID from certificate"
            )

        # Validate challenge freshness and structure
        is_valid_challenge, challenge_error = challenge_gen.validate_challenge(challenge)
        if not is_valid_challenge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Challenge validation failed: {challenge_error}"
            )

        # Verify signature
        try:
            signature_bytes = bytes.fromhex(request.signature)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature format (expected hex-encoded)"
            )

        is_valid_sig, sig_error = SignatureVerifier.verify_challenge_signature(
            challenge, signature_bytes, cert
        )
        if not is_valid_sig:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Signature verification failed: {sig_error}"
            )

        # Check room authorization
        attendance_storage = get_attendance_storage()
        is_authorized, auth_error = attendance_storage.check_room_authorization(
            student_id=student_id,
            room_id=challenge.room_id
        )

        if not is_authorized:
            return ChallengeVerificationResponse(
                success=False,
                access_granted=False,
                message=f"Access denied: {auth_error}",
                attendance_record=None
            )

        # Grant access and record attendance
        attendance_recorder = get_attendance_recorder()
        attendance_record = attendance_recorder.record_attendance(
            student_id=student_id,
            room_id=challenge.room_id,
            door_id=challenge.door_id
        )

        # Clean up challenge (mark as used)
        # In a production system, you might want to track used challenges

        return ChallengeVerificationResponse(
            success=True,
            access_granted=True,
            message="Access granted",
            attendance_record=attendance_record
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
