# Fix SSL Certificate Error

## Quick Fix (Recommended)

```bash
# Disable strict SSL checking (temporary)
npm config set strict-ssl false

# Then install
cd frontend
npm install --legacy-peer-deps
```

## After Installation

You can re-enable strict SSL later:
```bash
npm config set strict-ssl true
```

## Alternative: Update CA Certificates

If you want to fix the root cause:

```bash
# Install/update CA certificates
brew install ca-certificates

# Update npm CA store
npm config set cafile /usr/local/etc/ca-certificates/cert.pem
```

## Alternative: Use HTTP Registry (Less Secure)

Only if the above doesn't work:

```bash
npm config set registry http://registry.npmjs.org/
npm install --legacy-peer-deps
npm config set registry https://registry.npmjs.org/  # Reset after
```

## Why This Happens

On older macOS systems (like macOS 11), the system CA certificates can be outdated, causing SSL verification to fail. Disabling strict SSL is a common workaround for development.
