# Threat Model

## Overview

This document identifies potential security threats to SecureAttend and describes how the system mitigates or accepts these risks.

## Attack Surfaces

### 1. Certificate Authority (CA)

**Threats**:
- **CA Key Compromise**: Attacker gains access to CA private key
- **Unauthorized Certificate Issuance**: Attacker issues fraudulent certificates
- **Certificate Modification**: Attacker modifies certificate registry

**Mitigations**:
- CA private key stored securely (file system permissions)
- Certificate registry integrity protected
- CRL prevents use of revoked certificates
- **Recommendation**: Use HSM for CA key storage in production

### 2. Student Client

**Threats**:
- **Private Key Theft**: Student private key stolen or compromised
- **QR Code Replay**: Attacker reuses captured QR code
- **Challenge Replay**: Attacker reuses signed challenge
- **Key Sharing**: Student shares private key with others

**Mitigations**:
- Nonce-based challenges prevent QR code replay
- Timestamp expiration prevents challenge reuse
- Certificate revocation prevents use of compromised keys
- **Limitation**: Key sharing cannot be prevented without biometrics

### 3. Door Scanner

**Threats**:
- **Scanner Compromise**: Attacker compromises door scanner device
- **QR Code Manipulation**: Attacker modifies QR code data
- **Challenge Manipulation**: Attacker modifies challenge

**Mitigations**:
- Backend always validates certificates and signatures
- Scanner compromise doesn't grant access (backend verification required)
- QR code tampering detected by certificate validation
- Challenge tampering detected by signature verification

### 4. Backend Server

**Threats**:
- **Server Compromise**: Attacker gains control of backend server
- **Database Tampering**: Attacker modifies attendance records
- **Certificate Validation Bypass**: Attacker bypasses certificate checks
- **Challenge Replay**: Attacker accepts replayed challenges

**Mitigations**:
- Signed attendance records prevent tampering
- Challenge validation (nonce, timestamp) prevents replay
- Certificate chain validation cannot be bypassed
- **Recommendation**: Harden server security, use network segmentation

### 5. Network Communication

**Threats**:
- **Man-in-the-Middle (MITM)**: Attacker intercepts network traffic
- **Traffic Analysis**: Attacker analyzes network patterns
- **Replay Attacks**: Attacker replays network messages
- **Eavesdropping**: Attacker reads network traffic

**Mitigations**:
- Digital signatures prevent message tampering
- Nonces prevent replay attacks
- **Limitation**: No encryption in prototype (add TLS/HTTPS for production)

## Threat Categories

### High Severity Threats

#### 1. CA Private Key Compromise

**Description**: Attacker gains access to CA private key

**Impact**: 
- Attacker can issue fraudulent certificates
- Complete system compromise

**Likelihood**: Low (key stored securely)

**Mitigation**: 
- Secure key storage
- **Production**: Use HSM

**Status**: ✅ Mitigated (prototype), ⚠️ Needs HSM for production

#### 2. Student Private Key Theft

**Description**: Attacker steals student's private key

**Impact**: 
- Attacker can impersonate student
- Unauthorized access to rooms

**Likelihood**: Medium (depends on key storage)

**Mitigation**: 
- Certificate revocation
- Key encryption (recommended)

**Status**: ⚠️ Partially mitigated (revocation available)

#### 3. Server Compromise

**Description**: Attacker gains control of backend server

**Impact**: 
- Attacker can modify attendance records
- Attacker can grant unauthorized access

**Likelihood**: Low (server security depends on deployment)

**Mitigation**: 
- Server hardening
- Signed records provide audit trail
- **Production**: Network segmentation, monitoring

**Status**: ⚠️ Partially mitigated (audit trail available)

### Medium Severity Threats

#### 4. QR Code Replay

**Description**: Attacker captures and reuses QR code

**Impact**: 
- Unauthorized access if QR code reused

**Likelihood**: Medium (QR codes displayed on screen)

**Mitigation**: 
- Nonce-based challenges
- QR code nonce prevents reuse

**Status**: ✅ Mitigated

#### 5. Challenge Replay

**Description**: Attacker reuses signed challenge

**Impact**: 
- Unauthorized access if challenge accepted multiple times

**Likelihood**: Low (challenge expires in 30 seconds)

**Mitigation**: 
- Timestamp expiration (30 seconds)
- Nonce tracking
- Challenge ID validation

**Status**: ✅ Mitigated

#### 6. Certificate Forgery

**Description**: Attacker creates fake certificate

**Impact**: 
- Unauthorized access with fake certificate

**Likelihood**: Low (requires CA key compromise)

**Mitigation**: 
- Certificate chain validation
- CA signature verification

**Status**: ✅ Mitigated

### Low Severity Threats

#### 7. Network Eavesdropping

**Description**: Attacker reads network traffic

**Impact**: 
- Privacy violation
- Potential information leakage

**Likelihood**: Medium (depends on network security)

**Mitigation**: 
- **Production**: Use TLS/HTTPS

**Status**: ⚠️ Not mitigated in prototype (add TLS for production)

#### 8. Time Manipulation

**Description**: Attacker manipulates system clock

**Impact**: 
- Challenge expiration bypass
- Timestamp validation failure

**Likelihood**: Low (requires system access)

**Mitigation**: 
- **Production**: Use NTP for clock synchronization

**Status**: ⚠️ Partially mitigated (timestamp validation works, but clock sync needed)

#### 9. Denial of Service (DoS)

**Description**: Attacker floods backend with requests

**Impact**: 
- System unavailability
- Legitimate users unable to access

**Likelihood**: Medium (depends on infrastructure)

**Mitigation**: 
- **Production**: Rate limiting, load balancing

**Status**: ⚠️ Not mitigated in prototype

## Accepted Risks

### 1. Key Sharing

**Description**: Student shares private key with another student

**Impact**: Proxy attendance (one student marks attendance for another)

**Mitigation**: Not technically feasible without biometrics

**Acceptance**: Acceptable risk for academic prototype

**Production Recommendation**: Add biometric authentication

### 2. QR Code Theft (Physical)

**Description**: Attacker physically steals QR code during display

**Impact**: Attacker can use QR code for one-time access

**Mitigation**: Nonce prevents reuse, short expiration time

**Acceptance**: Acceptable risk (limited to one-time access)

### 3. Single Point of Failure (Backend)

**Description**: Backend server failure causes system unavailability

**Impact**: No access control or attendance marking

**Mitigation**: **Production**: High availability deployment, clustering

**Acceptance**: Acceptable for prototype

## Security Controls Summary

| Control | Status | Production Recommendation |
|---------|--------|---------------------------|
| Certificate Chain Validation | ✅ Implemented | - |
| Certificate Revocation | ✅ Implemented | OCSP for real-time checking |
| Digital Signatures | ✅ Implemented | - |
| Nonce-based Replay Prevention | ✅ Implemented | - |
| Timestamp Expiration | ✅ Implemented | NTP for clock sync |
| TLS/HTTPS | ⚠️ Not implemented | **Required** |
| Key Encryption | ⚠️ Not implemented | **Required** |
| HSM for CA | ⚠️ Not implemented | **Recommended** |
| Rate Limiting | ⚠️ Not implemented | **Recommended** |
| Audit Logging | ⚠️ Basic only | **Recommended** |

## Compliance Considerations

### Data Protection

- **Student Data**: Minimal data collected (student_id, room_id, timestamp)
- **Privacy**: No personally identifiable information in QR codes
- **Retention**: Attendance records stored indefinitely (configurable)

### Access Control

- **Authorization**: Room-based access control
- **Audit Trail**: All access attempts logged with cryptographic proof
- **Revocation**: Certificate revocation for access removal

## Recommendations for Production

1. **Network Security**: Implement TLS/HTTPS for all communication
2. **Key Management**: Use HSM for CA keys, encrypt student keys
3. **Infrastructure**: Deploy with high availability, load balancing
4. **Monitoring**: Implement security monitoring and alerting
5. **Audit Logging**: Comprehensive audit logging for all operations
6. **Rate Limiting**: Implement rate limiting to prevent DoS
7. **Clock Synchronization**: Use NTP for accurate timestamps
8. **Certificate Management**: Implement automated certificate renewal
9. **Backup and Recovery**: Secure backup and disaster recovery procedures
10. **Security Testing**: Regular penetration testing and security audits

## Conclusion

SecureAttend provides strong cryptographic security for access control and attendance. The prototype mitigates most threats, but requires additional security controls (TLS, key encryption, HSM) for production deployment.

The system demonstrates proper PKI usage and cryptographic best practices while maintaining usability for end users.
