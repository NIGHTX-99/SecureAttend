# Quick Start Guide

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

## Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd SecureAttend
   ```

2. **Create a virtual environment (recommended)**:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Phase 1: Certificate Authority Setup

### Step 1: Initialize the CA

Initialize the Certificate Authority (this creates the root CA certificate):

```bash
python -m backend.ca.cli init
```

This will create:
- `data/ca/ca_private_key.pem` - CA private key
- `data/ca/ca_certificate.pem` - CA public certificate
- `data/ca/cert_registry.json` - Certificate registry

### Step 2: Issue Student Certificates

Issue a certificate to a student:

```bash
python -m backend.ca.cli issue-student student_001 --email student001@college.edu
```

This creates:
- `data/certs/students/student_001/certificate.pem`
- `data/certs/students/student_001/private_key.pem`

### Step 3: Issue Door Certificates

Issue a certificate to a door device:

```bash
python -m backend.ca.cli issue-door door_001 CS101
```

This creates:
- `data/certs/doors/door_001/certificate.pem`
- `data/certs/doors/door_001/private_key.pem`

### Step 4: List Certificates

View all issued certificates:

```bash
python -m backend.ca.cli list-certs
```

### Step 5: Revoke a Certificate (if needed)

Revoke a student certificate:

```bash
python -m backend.ca.cli revoke-student student_001 --reason key_compromise
```

## Testing Phase 1

Run the comprehensive test suite:

```bash
python scripts/test_ca.py
```

This will test:
- CA initialization
- Student certificate issuance
- Door certificate issuance
- Certificate revocation
- Certificate registry

## Phase 2: Backend Setup

### Step 1: Initialize Backend System

Initialize the CA, issue test certificates, and set up the database:

```bash
python scripts/init_backend.py
```

This will:
- Initialize the CA (if not already done)
- Issue certificates for 3 test students and 3 door devices
- Create the database with test room authorizations

### Step 2: Start Backend Server

Start the FastAPI backend server:

```bash
python scripts/start_backend.py
```

Or using uvicorn directly:

```bash
uvicorn backend.api.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Step 3: Test the API

Open http://localhost:8000/docs in your browser to access the interactive API documentation (Swagger UI).

You can test the endpoints directly from the browser.

## Next Steps

Once Phase 2 is complete, proceed to Phase 3: Client Implementation (QR generation and signing).

See `docs/architecture.md` for system design and `docs/crypto-design.md` for cryptographic details.

## Troubleshooting

### Issue: "CA certificate not found"

**Solution**: Run `python -m backend.ca.cli init` first to initialize the CA.

### Issue: "Module not found" errors

**Solution**: Make sure you're in the project root directory and dependencies are installed:
```bash
pip install -r requirements.txt
```

### Issue: Permission errors

**Solution**: Make sure you have write permissions in the project directory.

## Custom Configuration

You can customize directories using CLI options:

```bash
# Custom CA directory
python -m backend.ca.cli --ca-dir ./my_ca init

# Custom certificates directory
python -m backend.ca.cli --certs-dir ./my_certs issue-student student_001
```
