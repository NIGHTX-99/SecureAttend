"""
Attendance Storage

Database operations for attendance records.
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from backend.ca.ca_manager import CAManager


class AttendanceStorage:
    """Manages attendance records in SQLite database."""

    def __init__(self, db_path: Path, ca_manager: CAManager):
        """
        Initialize Attendance Storage.

        Args:
            db_path: Path to SQLite database file
            ca_manager: CA Manager for signing attendance records
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ca_manager = ca_manager
        self._init_database()

    def _init_database(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Attendance records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                room_id TEXT NOT NULL,
                door_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                record_hash TEXT NOT NULL,
                backend_signature TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, room_id, timestamp)
            )
        """)

        # Room authorization table (which students can access which rooms)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS room_authorizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                room_id TEXT NOT NULL,
                course_id TEXT,
                start_time TEXT,
                end_time TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, room_id)
            )
        """)

        # Student enrollment table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                course_id TEXT NOT NULL,
                room_id TEXT NOT NULL,
                schedule_start TEXT,
                schedule_end TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, course_id)
            )
        """)

        conn.commit()
        conn.close()

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
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        # Create attendance record
        record = {
            "student_id": student_id,
            "room_id": room_id,
            "door_id": door_id,
            "timestamp": timestamp.isoformat() + "Z",
        }

        # Compute record hash
        record_json = json.dumps(record, sort_keys=True)
        record_hash = hashlib.sha256(record_json.encode('utf-8')).hexdigest()

        # Sign record with backend key (use CA key for now, in production use separate key)
        backend_key = self.ca_manager.get_ca_private_key()
        signature_bytes = backend_key.sign(
            record_json.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        backend_signature = signature_bytes.hex()

        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO attendance_records 
                (student_id, room_id, door_id, timestamp, record_hash, backend_signature)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                student_id,
                room_id,
                door_id,
                record["timestamp"],
                record_hash,
                backend_signature,
            ))

            conn.commit()
            record_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            # Record already exists (duplicate)
            conn.close()
            raise ValueError("Attendance record already exists for this student/room/time")

        conn.close()

        # Add record ID and signature to return value
        record["id"] = record_id
        record["record_hash"] = record_hash
        record["backend_signature"] = backend_signature

        return record

    def get_attendance_records(
        self,
        student_id: Optional[str] = None,
        room_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Retrieve attendance records with optional filters.

        Args:
            student_id: Filter by student ID
            room_id: Filter by room ID
            start_date: Filter records from this date
            end_date: Filter records until this date
            limit: Maximum number of records to return

        Returns:
            List of attendance record dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM attendance_records WHERE 1=1"
        params = []

        if student_id:
            query += " AND student_id = ?"
            params.append(student_id)

        if room_id:
            query += " AND room_id = ?"
            params.append(room_id)

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat() + "Z")

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat() + "Z")

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        records = [dict(row) for row in rows]
        conn.close()

        return records

    def add_room_authorization(
        self,
        student_id: str,
        room_id: str,
        course_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ):
        """
        Add room authorization for a student.

        Args:
            student_id: Student identifier
            room_id: Room identifier
            course_id: Course identifier (optional)
            start_time: Access start time (optional, format: HH:MM)
            end_time: Access end time (optional, format: HH:MM)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO room_authorizations
                (student_id, room_id, course_id, start_time, end_time)
                VALUES (?, ?, ?, ?, ?)
            """, (student_id, room_id, course_id, start_time, end_time))

            conn.commit()
        except sqlite3.Error as e:
            conn.close()
            raise ValueError(f"Failed to add room authorization: {str(e)}")

        conn.close()

    def check_room_authorization(
        self,
        student_id: str,
        room_id: str,
        current_time: Optional[datetime] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a student is authorized to access a room.

        Args:
            student_id: Student identifier
            room_id: Room identifier
            current_time: Current time for time-based checks (default: now)

        Returns:
            Tuple of (is_authorized, error_message)
        """
        if current_time is None:
            current_time = datetime.utcnow()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM room_authorizations
            WHERE student_id = ? AND room_id = ?
        """, (student_id, room_id))

        row = cursor.fetchone()
        conn.close()

        if row is None:
            return False, "Student not authorized for this room"

        # Check time-based authorization if specified
        if row[4] and row[5]:  # start_time and end_time
            current_time_str = current_time.strftime("%H:%M")
            if current_time_str < row[4] or current_time_str > row[5]:
                return False, f"Access not authorized at current time {current_time_str}"

        return True, None

    def add_student_enrollment(
        self,
        student_id: str,
        course_id: str,
        room_id: str,
        schedule_start: Optional[str] = None,
        schedule_end: Optional[str] = None
    ):
        """
        Add student enrollment in a course/room.

        Args:
            student_id: Student identifier
            course_id: Course identifier
            room_id: Room identifier
            schedule_start: Class start time (optional)
            schedule_end: Class end time (optional)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO student_enrollments
                (student_id, course_id, room_id, schedule_start, schedule_end)
                VALUES (?, ?, ?, ?, ?)
            """, (student_id, course_id, room_id, schedule_start, schedule_end))

            conn.commit()
        except sqlite3.Error as e:
            conn.close()
            raise ValueError(f"Failed to add enrollment: {str(e)}")

        conn.close()

        # Automatically create room authorization from enrollment
        self.add_room_authorization(
            student_id=student_id,
            room_id=room_id,
            course_id=course_id,
            start_time=schedule_start,
            end_time=schedule_end
        )
