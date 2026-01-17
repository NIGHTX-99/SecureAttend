"""
FastAPI Main Application

Main entry point for the backend API server.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from cryptography import x509
from cryptography.hazmat.primitives import serialization

from backend.api.models import (
    ChallengeRequest,
    ChallengeResponse,
    ChallengeVerificationRequest,
    ChallengeVerificationResponse,
    AttendanceRecordResponse,
    RoomAuthorizationRequest,
    StudentEnrollmentRequest,
    ErrorResponse,
)
from backend.api.routes.auth import router as auth_router
from backend.api.routes.attendance import router as attendance_router

# Initialize FastAPI app
app = FastAPI(
    title="PKI-Based QR Access Control API",
    description="Backend API for PKI-based access control and attendance system",
    version="0.1.0",
)

# CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(attendance_router, prefix="/api/attendance", tags=["attendance"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "PKI-Based QR Access Control API",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
