# Vercel Deployment Troubleshooting Guide

## Common Issues and Solutions

### 1. NPM Command Errors

**Problem**: Vercel fails with "Missing script: build" or similar npm errors.

**Root Cause**:
- Vercel runs `npm install` and `npm run build` at the **root** level by default
- Our project structure has the React app in `frontend/` subdirectory
- Root `package.json` didn't have a `build` script

**Solution Implemented**:
1. Added `build` script to root `package.json` that delegates to frontend
2. Added `install` script for consistency
3. Updated `vercel.json` with explicit `buildCommand` and `installCommand`

### 2. Peer Dependency Conflicts

**Problem**: React 19 has strict peer dependency requirements that break with older packages.

**Root Cause**:
- `react-scripts@5.0.1` expects React 18
- We're using React 19.2.3
- npm throws peer dependency errors

**Solution Implemented**:
1. Added `.npmrc` with `legacy-peer-deps=true`
2. Updated `vercel.json` install command to include `--legacy-peer-deps`
3. This allows React 19 to work with packages expecting React 18

### 3. Build Performance Issues

**Problem**: Builds timeout or take too long.

**Solutions Implemented**:
1. **Skip audits**: `--no-audit` flag speeds up installs
2. **Use cache**: `--prefer-offline` uses cached packages
3. **Ignore unchanged**: `ignoreCommand` in `vercel.json` skips builds when frontend hasn't changed
4. **Timeout increase**: Extended fetch-timeout in `.npmrc` for slow networks

### 4. Environment Variable Issues

**Current Configuration**:
```json
{
  "REACT_APP_API_URL": "https://wolf-goat-pig.onrender.com",
  "REACT_APP_USE_MOCK_AUTH": "true",
  "CI": "false"
}
```

**Why CI=false**:
- Prevents treating warnings as errors
- Allows build to succeed with minor linting issues
- More forgiving in production builds

## Testing Locally

### Test the exact Vercel build process:

```bash
# Clean install with Vercel flags
cd frontend
rm -rf node_modules
npm ci --legacy-peer-deps --no-audit

# Run build
npm run build

# Verify build output
ls -la build/
```

### Test from root (how Vercel sees it):

```bash
# From project root
npm run build

# Should delegate to frontend and build successfully
```

## Quick Fixes for Common Errors

### "Missing script: build"
- Check root `package.json` has `build` script
- Verify it points to correct subdirectory

### "Cannot find module" or dependency errors
- Delete `node_modules` and `package-lock.json`
- Run `npm ci --legacy-peer-deps`
- Check `.npmrc` is present

### "ERESOLVE unable to resolve dependency tree"
- Verify `.npmrc` contains `legacy-peer-deps=true`
- Check `vercel.json` install command includes `--legacy-peer-deps`

### Build succeeds locally but fails on Vercel
- Check Node version matches (18.x)
- Verify all env variables are set in Vercel dashboard
- Check `vercel.json` paths are correct relative to root

## Monitoring Deployment

### View logs:
```bash
vercel logs [deployment-url]
```

### Check build output:
- Go to Vercel Dashboard → Project → Deployments
- Click on failed deployment
- View "Build Logs" tab

## Making Deployment More Resilient

### Current Resilience Features:

1. **Fallback build paths**: Root scripts delegate to frontend
2. **Dependency resolution**: `.npmrc` handles peer dependency conflicts
3. **Cache optimization**: Prefer offline and skip audits
4. **Conditional builds**: Only rebuild when frontend changes
5. **Extended timeouts**: Handle slow network conditions
6. **CI mode disabled**: Allow builds with warnings

### Recommended Monitoring:

```bash
# Test before pushing
npm run build
npm run test:frontend

# Verify Vercel config
vercel build

# Preview deployment
vercel
```

## File Structure Summary

```
wolf-goat-pig/
├── package.json          # Root: has build script pointing to frontend
├── .npmrc                # NPM config for dependency resolution
├── vercel.json           # Vercel deployment configuration
└── frontend/
    ├── package.json      # Frontend: actual build happens here
    └── build/            # Output directory (generated)
```

## Vercel Configuration Reference

Key `vercel.json` settings:
- `buildCommand`: Explicitly tells Vercel how to build
- `installCommand`: Controls dependency installation
- `outputDirectory`: Where to find built files
- `ignoreCommand`: When to skip rebuilds
- `build.env`: Environment variables for build time

## Next Steps for Production

1. **Set up preview deployments** for branches
2. **Enable deployment protection** for production
3. **Configure custom domains** properly
4. **Set up monitoring** with Vercel Analytics
5. **Review security headers** in routes config
