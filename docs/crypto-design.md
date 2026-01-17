# Cryptographic Design

## Overview

SecureAttend uses Public Key Infrastructure (PKI) with X.509 certificates, RSA digital signatures, and challenge-response authentication to provide secure, passwordless access control.

## Cryptographic Components

### 1. Certificate Authority (CA)

**Algorithm**: RSA-2048 with SHA-256

**Certificate Structure**:
- **Subject**: `CN={Organization} Root CA, O={Organization}, OU=Certificate Authority`
- **Validity**: 10 years (configurable)
- **Extensions**:
  - `BasicConstraints`: CA=True, pathLength=None
  - `KeyUsage`: keyCertSign, crlSign
  - `SubjectKeyIdentifier`: SHA-1 hash of public key
  - `AuthorityKeyIdentifier`: Self-referencing

**Key Storage**: CA private key stored in PEM format (unencrypted in prototype)

### 2. Student Certificates

**Algorithm**: RSA-2048 with SHA-256

**Certificate Structure**:
- **Subject**: `CN=student_{id}, O=College, OU=Students, EMAIL={email}`
- **Validity**: 1 year (configurable)
- **Extensions**:
  - `BasicConstraints`: CA=False
  - `KeyUsage`: digitalSignature
  - `ExtendedKeyUsage`: clientAuth
  - `SubjectKeyIdentifier`: SHA-1 hash of public key
  - `AuthorityKeyIdentifier`: Points to CA

**Key Generation**: RSA key pair generated with public_exponent=65537

### 3. Door Device Certificates

**Algorithm**: RSA-2048 with SHA-256

**Certificate Structure**:
- **Subject**: `CN=door_{id}, O=College, OU=Doors`
- **Validity**: 5 years (configurable)
- **Extensions**:
  - `BasicConstraints`: CA=False
  - `KeyUsage`: digitalSignature
  - `ExtendedKeyUsage`: clientAuth, serverAuth
  - `SubjectAlternativeName`: Room ID embedded
  - `SubjectKeyIdentifier`: SHA-1 hash of public key
  - `AuthorityKeyIdentifier`: Points to CA

### 4. Challenge-Response Protocol

**Challenge Structure**:
```json
{
  "nonce": "hex-encoded-256-bit-random",
  "timestamp": "ISO-8601-timestamp",
  "room_id": "room-identifier",
  "door_id": "door-identifier",
  "previous_nonce": "nonce-from-qr",
  "challenge_id": "unique-challenge-id"
}
```

**Signing Process**:
1. Challenge serialized to JSON
2. JSON bytes hashed with SHA-256
3. Hash signed with RSA-2048 (PKCS#1 v1.5 padding)
4. Signature hex-encoded for transmission

**Verification Process**:
1. Challenge serialized to JSON (same as signing)
2. Signature decoded from hex
3. RSA signature verified with certificate's public key
4. SHA-256 hash verified

### 5. Nonce Generation

**Algorithm**: `secrets.token_bytes(32)` (256-bit)

**Usage**:
- QR code nonce: Prevents QR code replay
- Challenge nonce: Ensures challenge uniqueness
- Nonce registry: Tracks seen nonces (5-minute TTL)

### 6. Certificate Revocation

**Method**: Certificate Revocation List (CRL)

**CRL Structure**:
- X.509 CRL format
- Signed by CA private key
- Includes revocation reason codes
- Validity: 7 days
- Updated on revocation

**Revocation Reasons**:
- unspecified
- key_compromise
- superseded
- cessation_of_operation

### 7. Attendance Record Integrity

**Hash Algorithm**: SHA-256

**Record Structure**:
```json
{
  "student_id": "...",
  "room_id": "...",
  "door_id": "...",
  "timestamp": "...",
  "record_hash": "sha256-hash",
  "backend_signature": "rsa-signature-hex"
}
```

**Signing Process**:
1. Record data serialized to JSON (sorted keys)
2. SHA-256 hash computed
3. Record signed with backend private key (RSA-2048, PKCS#1 v1.5)
4. Signature hex-encoded and stored

## Security Properties

### 1. Authentication

- **Certificate-based**: Students authenticate using X.509 certificates
- **Chain verification**: Certificates validated against CA
- **Revocation checking**: Revoked certificates rejected

### 2. Integrity

- **Digital signatures**: All critical data signed
- **Hash verification**: Data integrity checked with SHA-256
- **Signed records**: Attendance records cryptographically signed

### 3. Non-Repudiation

- **Digital signatures**: Student cannot deny signing challenge
- **Signed attendance**: Attendance records provide proof

### 4. Replay Prevention

- **Nonce-based**: Each challenge includes unique nonce
- **Timestamp-based**: Challenges expire after 30 seconds
- **Nonce tracking**: Previous nonces tracked (5-minute window)

### 5. Confidentiality

- **Note**: Currently no encryption for data in transit (add TLS for production)
- **Private keys**: Stored locally (add encryption for production)

## Cryptographic Algorithms Summary

| Component | Algorithm | Key Size | Hash |
|-----------|-----------|----------|------|
| CA Key | RSA | 2048 bits | SHA-256 |
| Student Key | RSA | 2048 bits | SHA-256 |
| Door Key | RSA | 2048 bits | SHA-256 |
| Signatures | RSA-PKCS#1v1.5 | 2048 bits | SHA-256 |
| Nonces | Random | 256 bits | - |
| Record Hashes | - | - | SHA-256 |

## Key Management

### CA Private Key

- **Storage**: `data/ca/ca_private_key.pem`
- **Protection**: File system permissions (add encryption for production)
- **Backup**: Critical - secure backup required

### Student Private Keys

- **Storage**: `data/certs/students/{id}/private_key.pem`
- **Protection**: File system permissions (add password encryption for production)
- **Distribution**: Issued by CA, delivered securely to students

### Certificate Distribution

- **Public certificates**: Can be distributed freely
- **Private keys**: Must be kept secret
- **Revocation**: Published via CRL

## Security Assumptions

1. **CA Security**: CA private key is kept secure (use HSM in production)
2. **System Security**: Backend server is trusted and secure
3. **Clock Synchronization**: System clocks are synchronized (use NTP)
4. **Network Security**: TLS/HTTPS for all network communication (add for production)
5. **Key Storage**: Private keys stored securely (add encryption for production)

## Threat Model

### Mitigated Threats

1. **Replay Attacks**: Prevented by nonces and timestamps
2. **Certificate Forgery**: Prevented by CA signature verification
3. **Data Tampering**: Prevented by digital signatures
4. **Man-in-the-Middle**: Mitigated by certificate validation (add TLS for complete protection)

### Known Limitations

1. **Key Compromise**: If private key stolen, attacker can impersonate student (mitigated by revocation)
2. **CA Compromise**: If CA key stolen, entire system compromised (use HSM)
3. **Time Manipulation**: Clock skew can affect timestamp validation (use NTP)
4. **QR Code Theft**: QR codes are short-lived, but physical theft possible (nonce prevents reuse)

## Production Recommendations

1. **TLS/HTTPS**: Add TLS for all network communication
2. **Key Encryption**: Encrypt private keys with strong passwords
3. **HSM**: Use Hardware Security Module for CA key storage
4. **OCSP**: Implement Online Certificate Status Protocol for real-time revocation
5. **Key Rotation**: Implement certificate renewal and key rotation policies
6. **Audit Logging**: Log all cryptographic operations for security audits
7. **Rate Limiting**: Implement rate limiting to prevent brute force attacks
8. **Network Segmentation**: Isolate CA infrastructure from public networks
