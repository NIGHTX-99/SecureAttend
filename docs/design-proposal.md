# SecureAttend
## Technical Design Proposal

---

## 1. Python Tech Stack

### Core Libraries

#### Backend Stack
- **FastAPI** (`fastapi`) - Modern, fast web framework for building APIs
  - Built-in OpenAPI documentation
  - Async support for better performance
  - Type hints support
  - Easy to test

- **Cryptography** (`cryptography`) - Primary crypto library
  - X.509 certificate creation and validation
  - RSA/ECC key generation and signing
  - Certificate signing requests (CSR)
  - Certificate revocation list (CRL) basics

- **SQLite3** (built-in) - Lightweight database for:
  - Certificate storage (public certs only)
  - Attendance records
  - Room authorization rules
  - Certificate revocation list

- **Pydantic** (via FastAPI) - Data validation and serialization

#### Client Stack
- **qrcode** (`qrcode`) + **Pillow** (`Pillow`) - QR code generation
- **cryptography** - Same library for consistent crypto operations
- **Click** (`click`) - CLI framework for user-friendly commands
- **requests** (`requests`) - HTTP client for backend communication

#### DevOps & Infrastructure
- **Docker** - Containerization
- **pytest** (`pytest`) - Testing framework
- **black** (`black`) - Code formatting (optional, for CI)
- **mypy** (`mypy`) - Type checking (optional, for CI)

---

## 2. Cryptographic Protocol

### Phase 1: Certificate Issuance (Setup)

```
CA (Certificate Authority)
├── Generates self-signed root CA certificate
├── Issues X.509 certificates to:
│   ├── Students (Subject: student_id, email)
│   ├── Door devices (Subject: door_id, room_id)
│   └── Backend server (Subject: server_id)
└── Maintains certificate registry
```

**Certificate Fields (Student):**
- Subject: `CN=student_{id}, O=College, OU=Students`
- Validity: 1 year
- Key Usage: Digital Signature
- Extended Key Usage: Client Authentication

**Certificate Fields (Door Device):**
- Subject: `CN=door_{id}, O=College, OU=Doors`
- Validity: 5 years
- Key Usage: Digital Signature

### Phase 2: Authentication Flow

```
1. Student opens client app
   └─> Generates/loads private key (if not exists, generates new)
   └─> Loads certificate
   └─> Displays QR code containing:
       - student_id
       - certificate (public key embedded)
       - nonce (random value for freshness)

2. Door Scanner reads QR code
   └─> Extracts student_id, certificate, nonce
   └─> Validates certificate structure (format check only)
   └─> Sends to backend: {student_id, certificate, nonce, room_id, door_id}

3. Backend Verification Server
   ├─> Validates certificate:
   │   ├─> Certificate chain (checks CA signature)
   │   ├─> Certificate expiry
   │   ├─> Certificate revocation status (CRL check)
   │   └─> Certificate purpose (client authentication)
   ├─> Generates challenge:
   │   └─> challenge = {
   │         nonce: random_256bit,
   │         timestamp: current_time,
   │         room_id: requested_room,
   │         door_id: scanner_door,
   │         previous_nonce: from_QR
   │       }
   └─> Returns challenge to door scanner

4. Door Scanner forwards challenge to client (via display or network)

5. Client signs challenge
   ├─> Receives challenge
   ├─> Validates timestamp (within 30 seconds)
   ├─> Validates nonce freshness (not seen before)
   ├─> Signs challenge:
   │   └─> signature = Sign(private_key, SHA256(challenge_json))
   └─> Returns: {challenge, signature, certificate}

6. Backend verifies signature
   ├─> Validates certificate (again, for defense in depth)
   ├─> Verifies signature:
   │   └─> Verify(certificate.public_key, SHA256(challenge_json), signature)
   ├─> Checks room authorization:
   │   └─> Is student authorized for room_id? (enrollment database)
   ├─> Checks time authorization:
   │   └─> Is access time valid? (class schedule)
   └─> Checks challenge freshness:
       └─> timestamp not older than 30 seconds

7. Access Decision
   ├─> If valid:
   │   ├─> Send "GRANT" to door scanner
   │   ├─> Record attendance:
   │   │   └─> attendance_record = {
   │   │         student_id: ...,
   │   │         room_id: ...,
   │   │         timestamp: ...,
   │   │         signature: Sign(backend_key, SHA256(record))
   │   │       }
   │   └─> Log access event
   └─> If invalid:
       ├─> Send "DENY" to door scanner
       └─> Log security event
```

### Phase 3: Security Mechanisms

#### Replay Attack Prevention
1. **Nonce-based**: Each QR code contains a unique nonce
2. **Timestamp-based**: Challenges expire after 30 seconds
3. **Challenge-response**: Server generates new challenge, not just using QR nonce
4. **Nonce registry**: Backend maintains seen nonces (memory, 5-minute TTL)

#### Tampering Prevention
1. **Digital signatures**: All critical data is signed
2. **Certificate validation**: Certificate chain verification
3. **Integrity checks**: SHA256 hashing for all signed data

#### Key Management
1. **Private keys**: Stored encrypted on client (password-protected, if needed)
2. **Certificate storage**: Public certificates in SQLite
3. **Revocation**: CRL maintained by CA (simple list, checked on each auth)

---

## 3. Data Structures

### Challenge Object
```json
{
  "nonce": "hex-encoded-256-bit-random",
  "timestamp": "2024-01-15T10:30:00Z",
  "room_id": "CS101",
  "door_id": "door_001",
  "previous_nonce": "nonce-from-qr"
}
```

### Attendance Record
```json
{
  "student_id": "student_123",
  "room_id": "CS101",
  "timestamp": "2024-01-15T10:30:15Z",
  "door_id": "door_001",
  "record_hash": "sha256-hash-of-record",
  "backend_signature": "hex-encoded-signature"
}
```

---

## 4. System Architecture

### Backend Services
```
backend/
├── ca/              # Certificate Authority logic
│   ├── ca_manager.py      # CA key/cert management
│   ├── cert_issuer.py     # Issue certificates to students/doors
│   └── crl_manager.py     # Certificate Revocation List
│
├── auth/            # Authentication logic
│   ├── cert_validator.py  # Certificate validation
│   ├── challenge_gen.py   # Challenge generation
│   └── signature_verify.py # Signature verification
│
├── attendance/      # Attendance recording
│   ├── recorder.py        # Record attendance
│   └── storage.py         # Database operations
│
└── api/             # FastAPI endpoints
    ├── main.py            # FastAPI app
    ├── routes/
    │   ├── auth.py        # /auth/challenge, /auth/verify
    │   └── attendance.py  # /attendance/records
    └── models.py          # Pydantic models
```

### Client Application
```
client/
├── qr/              # QR code generation
│   └── generator.py
│
├── signing/         # Cryptographic operations
│   ├── key_manager.py     # Load/generate keys
│   └── signer.py          # Sign challenges
│
└── ui/              # User interface
    ├── cli.py             # Click-based CLI
    └── display.py         # QR display logic
```

---

## 5. Security Assumptions

1. **CA Security**: CA private key is kept secure (in production, use hardware security module)
2. **Network**: TLS for all client-backend communication (not implemented in prototype)
3. **Client Security**: Student private keys stored locally, password-protected if sensitive
4. **Backend Security**: Backend has access to CA public key and revocation lists
5. **Door Scanner**: Trusted device, but could be compromised (backend always verifies)

---

## 6. Known Limitations

1. **Proxy Attendance**: Student could share private key (solution: biometrics - out of scope)
2. **Network Attacks**: No TLS in prototype (add for production)
3. **CRL Size**: Simple in-memory CRL (use OCSP or distributed CRL for scale)
4. **Time Sync**: Relies on system clocks (use NTP in production)
5. **QR Theft**: QR codes are short-lived (nonce-based), but physical theft during display could be an issue

---

## 7. Development Phases

1. ✅ **Phase 1**: Repository structure + CA foundation
2. ⏳ **Phase 2**: Backend authentication logic
3. ⏳ **Phase 3**: Client QR + signing
4. ⏳ **Phase 4**: Integration + testing
5. ⏳ **Phase 5**: Docker + CI/CD
6. ⏳ **Phase 6**: Documentation

---

This design provides a solid foundation for implementing the PKI-based access control system with proper cryptographic practices.
