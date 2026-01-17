# SecureAttend

A Python-based system that uses Public Key Infrastructure (PKI) to provide passwordless authentication, secure classroom door access, and automatic attendance marking.

## Features

- **PKI-Based Authentication**: X.509 certificates for students and door devices
- **Challenge-Response Protocol**: Digital signatures prevent replay attacks
- **Automatic Attendance**: Secure attendance records with cryptographic integrity
- **QR Code Interface**: User-friendly QR code display for students
- **Certificate Management**: CA certificate issuance and revocation support

## Architecture

See [docs/architecture.md](docs/architecture.md) for detailed system architecture.

## Quick Start

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (optional)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd SecureAttend

# Install dependencies
pip install -r requirements.txt

# Initialize CA and generate certificates
python -m backend.ca.ca_manager init
```

### Running the System

```bash
# 1. Initialize backend (CA, certificates, database)
python scripts/init_backend.py

# 2. Start backend server
python scripts/start_backend.py
# Or: uvicorn backend.api.main:app --reload

# 3. In another terminal, use client
# Display QR code
python -m client.ui.cli show-qr --student-id student_001

# Complete authentication flow
python -m client.ui.cli authenticate student_001 CS101 door_001
```

### Docker

```bash
docker-compose up
```

## Development

### Repository Structure

```
SecureAttend/
├── backend/          # Backend services (CA, auth, attendance, API)
├── client/           # Client application (QR, signing, UI)
├── docker/           # Dockerfiles
├── docs/             # Documentation
└── tests/            # Unit and integration tests
```

### Branching Strategy

- `main` - Stable, production-ready code
- `develop` - Integration branch
- `backend-dev` - Backend and cryptography work
- `client-dev` - Client and QR logic work

## Security Considerations

This system demonstrates proper PKI usage but is a **prototype** for academic purposes. For production use, consider:

- Hardware Security Module (HSM) for CA keys
- TLS/HTTPS for all network communication
- OCSP for certificate revocation checking
- Secure key storage mechanisms
- Biometric authentication to prevent key sharing

## License

See [LICENSE](LICENSE) file for details.

## Documentation

- [Architecture](docs/architecture.md)
- [Cryptographic Design](docs/crypto-design.md)
- [Threat Model](docs/threat-model.md)
- [Design Proposal](docs/design-proposal.md)
