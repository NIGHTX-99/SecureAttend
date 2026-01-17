"""
Attendance Recorder

High-level interface for recording attendance.
"""

from datetime import datetime
from typing import Dict, Optional

from backend.attendance.storage import AttendanceStorage


class AttendanceRecorder:
    """Records student attendance with proper validation."""

    def __init__(self, storage: AttendanceStorage):
        """
        Initialize Attendance Recorder.

        Args:
            storage: Attendance Storage instance
        """
        self.storage = storage

    def record_attendance(
        self,
        student_id: str,
        room_id: str,
        door_id: str,
        timestamp: Optional[datetime] = None
    ) -> Dict:
        """
        Record student attendance.

        Args:
            student_id: Student identifier
            room_id: Room identifier
            door_id: Door identifier
            timestamp: Attendance timestamp (default: now)

        Returns:
            Attendance record dictionary

        Raises:
            ValueError: If attendance cannot be recorded (e.g., duplicate)
        """
        return self.storage.record_attendance(
            student_id=student_id,
            room_id=room_id,
            door_id=door_id,
            timestamp=timestamp
        )
