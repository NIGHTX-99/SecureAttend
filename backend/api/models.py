"""
Pydantic models for API requests and responses.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ChallengeRequest(BaseModel):
    """Request to generate a challenge."""
    student_id: str = Field(..., description="Student identifier")
    certificate_pem: str = Field(..., description="Student certificate in PEM format")
    room_id: str = Field(..., description="Requested room identifier")
    door_id: str = Field(..., description="Door/scanner identifier")
    previous_nonce: Optional[str] = Field(None, description="Nonce from QR code")


class ChallengeResponse(BaseModel):
    """Response containing authentication challenge."""
    challenge_id: str = Field(..., description="Unique challenge identifier")
    challenge: Dict[str, Any] = Field(..., description="Challenge object")
    message: str = Field(..., description="Response message")


class ChallengeVerificationRequest(BaseModel):
    """Request to verify a signed challenge."""
    challenge_id: str = Field(..., description="Challenge identifier")
    challenge: Dict[str, Any] = Field(..., description="Challenge object")
    signature: str = Field(..., description="Hex-encoded signature")
    certificate_pem: str = Field(..., description="Student certificate in PEM format")


class ChallengeVerificationResponse(BaseModel):
    """Response from challenge verification."""
    success: bool = Field(..., description="Whether verification succeeded")
    access_granted: bool = Field(..., description="Whether access is granted")
    message: str = Field(..., description="Response message")
    attendance_record: Optional[Dict[str, Any]] = Field(None, description="Attendance record if access granted")


class AttendanceRecordResponse(BaseModel):
    """Response containing attendance record."""
    id: int
    student_id: str
    room_id: str
    door_id: str
    timestamp: str
    record_hash: str
    backend_signature: str


class RoomAuthorizationRequest(BaseModel):
    """Request to add room authorization."""
    student_id: str
    room_id: str
    course_id: Optional[str] = None
    start_time: Optional[str] = None  # Format: HH:MM
    end_time: Optional[str] = None  # Format: HH:MM


class StudentEnrollmentRequest(BaseModel):
    """Request to add student enrollment."""
    student_id: str
    course_id: str
    room_id: str
    schedule_start: Optional[str] = None  # Format: HH:MM
    schedule_end: Optional[str] = None  # Format: HH:MM


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
