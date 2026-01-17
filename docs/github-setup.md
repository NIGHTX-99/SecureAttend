# GitHub Setup Instructions

## Repository Structure

This project uses the following branch structure:
- `main` - Stable, production-ready code
- `develop` - Integration branch
- `backend-dev` - Backend and cryptography work
- `client-dev` - Client and QR logic work

## Initial GitHub Setup

### 1. Create GitHub Repository

1. Go to GitHub.com and create a new repository
2. Name it: `SecureAttend`
3. **Do NOT** initialize with README, .gitignore, or license (we already have these)
4. Copy the repository URL (e.g., `https://github.com/yourusername/SecureAttend.git`)

### 2. Add Remote and Push

```bash
# Add remote repository
git remote add origin https://github.com/yourusername/SecureAttend.git

# Push all branches
git push -u origin main
git push -u origin develop
git push -u origin backend-dev
git push -u origin client-dev
```

### 3. Set Default Branch

1. Go to repository settings on GitHub
2. Set default branch to `develop` (or `main` if you prefer)

## Current Status

- ✅ Git repository initialized
- ✅ All branches created (main, develop, backend-dev, client-dev)
- ✅ Initial commit made
- ⏳ Ready to push to GitHub

## Workflow

### Feature Development

1. **Backend work**: Work on `backend-dev` branch
   ```bash
   git checkout backend-dev
   # Make changes
   git add .
   git commit -m "Description"
   git push origin backend-dev
   ```

2. **Client work**: Work on `client-dev` branch
   ```bash
   git checkout client-dev
   # Make changes
   git add .
   git commit -m "Description"
   git push origin client-dev
   ```

3. **Integration**: Merge to `develop`
   ```bash
   git checkout develop
   git merge backend-dev
   git merge client-dev
   git push origin develop
   ```

4. **Release**: Merge `develop` to `main` when ready
   ```bash
   git checkout main
   git merge develop
   git push origin main
   ```

## Important Notes

- The `.gitignore` file already excludes sensitive files:
  - `*.pem`, `*.key`, `*.crt` (certificates and keys)
  - `*.db`, `*.sqlite*` (database files)
  - `data/` directory (CA data, certificates, database)

- **Never commit**:
  - Private keys
  - CA private keys
  - Database files with real data
  - Any sensitive credentials

- The `data/` directory should remain local (it's in .gitignore)
