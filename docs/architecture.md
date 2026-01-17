# SecureAttend Architecture

## System Overview

SecureAttend is a PKI-based access control and attendance system that uses X.509 certificates, digital signatures, and challenge-response authentication to provide secure, passwordless access to classrooms.

## Architecture Diagram

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Student   │      │ Door Scanner │      │   Backend   │
│   Client    │◄────►│  Simulator   │◄────►│    Server   │
└─────────────┘      └──────────────┘      └─────────────┘
      │                     │                      │
      │                     │                      │
      ▼                     ▼                      ▼
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│ QR Display  │      │ QR Reader    │      │   FastAPI   │
│ Certificate │      │ Challenge    │      │    API      │
│  Private    │      │  Forwarding  │      │  Endpoints  │
│    Key      │      │              │      │             │
└─────────────┘      └──────────────┘      └─────────────┘
                                                      │
                                                      ▼
                                            ┌─────────────┐
                                            │ Certificate │
                                            │  Authority  │
                                            │   (CA)      │
                                            └─────────────┘
                                                      │
                                                      ▼
                                            ┌─────────────┐
                                            │  Database   │
                                            │  (SQLite)   │
                                            │  Attendance │
                                            │  Records    │
                                            └─────────────┘
```

## Components

### 1. Certificate Authority (CA)

**Location**: `backend/ca/`

- **CA Manager**: Manages root CA certificate and private key
- **Certificate Issuer**: Issues X.509 certificates to students and door devices
- **CRL Manager**: Manages certificate revocation lists

**Responsibilities**:
- Generate and maintain root CA certificate
- Issue student certificates (1-year validity)
- Issue door device certificates (5-year validity)
- Maintain certificate registry
- Generate and maintain Certificate Revocation Lists (CRL)

### 2. Backend Server

**Location**: `backend/api/` and `backend/auth/`

- **FastAPI Application**: RESTful API server
- **Certificate Validator**: Validates certificates (chain, expiry, revocation)
- **Challenge Generator**: Generates authentication challenges
- **Signature Verifier**: Verifies digital signatures
- **Attendance Storage**: Manages attendance records and authorizations

**API Endpoints**:
- `POST /api/auth/challenge` - Generate authentication challenge
- `POST /api/auth/verify` - Verify signed challenge and grant access
- `GET /api/attendance/records` - Query attendance records
- `POST /api/attendance/authorizations` - Add room authorizations
- `POST /api/attendance/enrollments` - Add student enrollments

### 3. Client Application

**Location**: `client/`

- **QR Generator**: Generates QR codes with certificate and nonce
- **Key Manager**: Manages student private keys and certificates
- **Challenge Signer**: Signs authentication challenges
- **CLI Interface**: User-friendly command-line interface

**Features**:
- Display QR codes for scanning
- Sign authentication challenges
- Complete authentication flow

### 4. Door Scanner Simulator

**Location**: `simulator/`

- Simulates door scanner hardware
- Reads QR codes
- Communicates with backend API
- Grants/denies access based on verification

### 5. Database

**Location**: `backend/attendance/storage.py`

**Tables**:
- `attendance_records`: Stores attendance with cryptographic signatures
- `room_authorizations`: Maps students to authorized rooms
- `student_enrollments`: Course enrollment information

## Authentication Flow

1. **Student displays QR code**:
   - Client generates QR with student_id, certificate, and nonce
   - QR code displayed on screen

2. **Door scanner reads QR**:
   - Extracts student_id, certificate, and nonce
   - Sends to backend: `POST /api/auth/challenge`

3. **Backend generates challenge**:
   - Validates certificate (chain, expiry, revocation)
   - Generates new challenge with nonce and timestamp
   - Returns challenge to scanner

4. **Scanner forwards challenge to client**:
   - Client receives challenge

5. **Client signs challenge**:
   - Signs challenge with student's private key
   - Returns signature to scanner

6. **Scanner verifies with backend**:
   - Sends signed challenge: `POST /api/auth/verify`
   - Backend verifies signature and checks authorization
   - If valid: grants access and records attendance
   - If invalid: denies access

## Security Features

1. **PKI-Based Authentication**:
   - X.509 certificates with proper extensions
   - Certificate chain validation
   - Certificate revocation checking

2. **Challenge-Response Protocol**:
   - Nonce-based challenges prevent replay attacks
   - Timestamp expiration (30 seconds)
   - Digital signatures ensure authenticity

3. **Data Integrity**:
   - All attendance records are signed
   - SHA-256 hashing for data integrity
   - Cryptographic verification

4. **Access Control**:
   - Room-based authorization
   - Time-based access control
   - Enrollment-based permissions

## Deployment Architecture

### Development

```
┌─────────────────────┐
│  Python Environment │
│  - Backend API      │
│  - Client CLI       │
│  - Simulator        │
└─────────────────────┘
```

### Production (Docker)

```
┌─────────────────────┐
│   Docker Compose    │
│  ┌───────────────┐  │
│  │ Backend       │  │
│  │ Container     │  │
│  └───────────────┘  │
│  ┌───────────────┐  │
│  │ Database      │  │
│  │ (SQLite/Postgres)│
│  └───────────────┘  │
└─────────────────────┘
```

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, SQLite
- **Cryptography**: cryptography library (X.509, RSA, SHA-256)
- **Client**: Python 3.11+, Click, qrcode, requests
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions

## Scalability Considerations

1. **Database**: SQLite suitable for small-medium deployments. For larger scale, use PostgreSQL.
2. **Challenge Storage**: In-memory storage suitable for small deployments. Consider Redis for distributed systems.
3. **CRL**: File-based CRL suitable for small deployments. Consider OCSP for real-time revocation checking.
4. **Load Balancing**: FastAPI can be deployed behind a load balancer (nginx, Traefik).

## Known Limitations

1. **Network Security**: No TLS/HTTPS in prototype (add for production)
2. **Key Storage**: Private keys stored unencrypted (add encryption for production)
3. **CRL Distribution**: File-based (use network distribution for production)
4. **Time Sync**: Relies on system clocks (use NTP for production)
5. **Scalability**: Single-server deployment (add clustering for production)
