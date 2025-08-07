# Scripts

This folder contains utility scripts for deployment and verification.

## Scripts

### 🔍 [verify_deployment.py](./verify_deployment.py)
Python script to verify deployment status and system health:
- Database connectivity check
- Health endpoint verification
- Storage system validation
- API endpoint testing

### 🛡️ [verify_production.sh](./verify_production.sh)
Bash script for production environment verification:
- Service status checks
- Network connectivity
- Environment variable validation
- Security configuration review

## Usage

### Deployment Verification

```bash
# Run Python verification script
python scripts/verify_deployment.py

# Run bash verification script
bash scripts/verify_production.sh
```

### From Backend Directory

If you need to run scripts with backend context:

```bash
cd backend
python ../scripts/verify_deployment.py
```

## Script Dependencies

- `verify_deployment.py`: Requires `requests` library
- `verify_production.sh`: Standard bash utilities

These scripts are designed to work in both development and production environments.
