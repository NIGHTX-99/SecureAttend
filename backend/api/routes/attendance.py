"""
Attendance Routes

Handles attendance record queries and management.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional, List

from backend.api.models import (
    AttendanceRecordResponse,
    RoomAuthorizationRequest,
    StudentEnrollmentRequest,
)
from backend.config import get_attendance_storage

router = APIRouter()


@router.get("/records", response_model=List[AttendanceRecordResponse])
async def get_attendance_records(
    student_id: Optional[str] = Query(None, description="Filter by student ID"),
    room_id: Optional[str] = Query(None, description="Filter by room ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
):
    """
    Retrieve attendance records with optional filters.
    """
    try:
        attendance_storage = get_attendance_storage()

        # Parse dates
        start_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format (expected ISO format)"
                )

        end_dt = None
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format (expected ISO format)"
                )

        records = attendance_storage.get_attendance_records(
            student_id=student_id,
            room_id=room_id,
            start_date=start_dt,
            end_date=end_dt,
            limit=limit
        )

        return [AttendanceRecordResponse(**record) for record in records]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/authorizations")
async def add_room_authorization(request: RoomAuthorizationRequest):
    """
    Add room authorization for a student.
    """
    try:
        attendance_storage = get_attendance_storage()
        attendance_storage.add_room_authorization(
            student_id=request.student_id,
            room_id=request.room_id,
            course_id=request.course_id,
            start_time=request.start_time,
            end_time=request.end_time
        )

        return {
            "message": "Room authorization added successfully",
            "student_id": request.student_id,
            "room_id": request.room_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add room authorization: {str(e)}"
        )


@router.post("/enrollments")
async def add_student_enrollment(request: StudentEnrollmentRequest):
    """
    Add student enrollment in a course/room.
    """
    try:
        attendance_storage = get_attendance_storage()
        attendance_storage.add_student_enrollment(
            student_id=request.student_id,
            course_id=request.course_id,
            room_id=request.room_id,
            schedule_start=request.schedule_start,
            schedule_end=request.schedule_end
        )

        return {
            "message": "Student enrollment added successfully",
            "student_id": request.student_id,
            "course_id": request.course_id,
            "room_id": request.room_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add enrollment: {str(e)}"
        )
