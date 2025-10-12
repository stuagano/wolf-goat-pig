# Deployment Troubleshooting Guide

This guide helps you diagnose and fix common deployment issues with the Wolf-Goat-Pig application on Render (backend) and Vercel (frontend).

## Quick Diagnostic Commands

```bash
# Check deployment readiness
.husky/deployment-checklist

# Test production builds locally
./scripts/test-prod-all.sh

# Verify deployment health
python scripts/verify-deployments.py --production
```

## Common Issues and Solutions

### 🔴 Backend (Render) Issues

#### 1. Service Won't Start

**Symptoms:**
- Render shows "Deploy failed"
- Logs show module import errors
- Service crashes on startup

**Solutions:**
```bash
# Check requirements.txt is complete
cd backend
pip freeze > requirements_check.txt
diff requirements.txt requirements_check.txt

# Test with production server locally
./scripts/test-prod-backend.sh

# Check for missing dependencies
python -c "from app.main import app"
```

**Common Fixes:**
- Ensure `gunicorn` is in requirements.txt
- Add `uvicorn[standard]` for async workers
- Check Python version matches (3.11.x)

#### 2. Database Connection Fails

**Symptoms:**
- "could not connect to server" errors
- "relation does not exist" errors
- Timeout errors

**Solutions:**
```bash
# Test PostgreSQL connection locally
docker run -d --name test-pg -e POSTGRES_PASSWORD=test -p 5432:5432 postgres:15
export DATABASE_URL="postgresql://postgres:test@localhost:5432/test"
python -c "from app.database import engine; engine.connect()"
```

**Render Configuration:**
- Use internal connection string for same-region databases
- Enable connection pooling
- Set `SQLALCHEMY_POOL_SIZE=5` and `SQLALCHEMY_MAX_OVERFLOW=10`

#### 3. Environment Variables Missing

**Symptoms:**
- Auth0 authentication fails
- Email service errors
- "KeyError" in logs

**Check on Render:**
```bash
# List all environment variables (from Render dashboard)
# Or use Render CLI
render envvars list --service <service-name>

# Set missing variables
render envvars set KEY=value --service <service-name>
```

**Required Variables:**
```
ENVIRONMENT=production
DATABASE_URL=<postgres-url>
AUTH0_DOMAIN=<your-domain>
AUTH0_API_AUDIENCE=<your-audience>
AUTH0_CLIENT_ID=<your-client-id>
AUTH0_CLIENT_SECRET=<your-secret>
FRONTEND_URL=<vercel-url>
```

#### 4. CORS Errors

**Symptoms:**
- "CORS policy" errors in browser console
- API calls blocked from frontend

**Fix in backend/app/main.py:**
```python
# Ensure your Vercel URL is in allowed origins
ALLOWED_ORIGINS = [
    "https://your-app.vercel.app",
    "https://your-custom-domain.com"
]
```

### 🔴 Frontend (Vercel) Issues

#### 1. Build Fails

**Symptoms:**
- Vercel shows "Build Error"
- "Module not found" errors
- TypeScript errors

**Local Testing:**
```bash
# Test build locally first
cd frontend
npm ci  # Clean install
npm run build

# Check build output size
du -sh build/
```

**Common Fixes:**
- Clear npm cache: `npm cache clean --force`
- Use exact versions in package.json
- Check for case-sensitive imports (works locally, fails on Linux)

#### 2. API Connection Fails

**Symptoms:**
- Network errors in browser
- "Failed to fetch" errors
- 404 on API calls

**Verify Configuration:**
```bash
# Check environment variables in Vercel
vercel env pull

# Verify REACT_APP_API_URL is set correctly
grep REACT_APP_API_URL .env.production
```

**Common Issues:**
- Missing `REACT_APP_` prefix for React env vars
- Using HTTP instead of HTTPS
- Trailing slash in API URL

#### 3. Authentication Issues

**Symptoms:**
- Login redirects fail
- "Invalid callback URL" errors
- Token validation failures

**Auth0 Checklist:**
1. Verify callback URLs in Auth0 dashboard include:
   - `https://your-app.vercel.app/callback`
   - Any preview URLs
   - Local development URLs

2. Check audience matches exactly:
   ```bash
   # Backend and frontend must use same audience
   echo "Backend: $AUTH0_API_AUDIENCE"
   echo "Frontend: $REACT_APP_AUTH0_AUDIENCE"
   ```

3. Verify client ID and domain are correct

#### 4. Blank Page / App Won't Load

**Symptoms:**
- White screen on production
- Console errors about missing files
- React errors

**Debug Steps:**
```bash
# Check if build files exist
ls -la frontend/build/static/

# Verify index.html has correct script tags
grep -E "script|link" frontend/build/index.html

# Test with local production server
npx serve -s frontend/build
```

### 🔧 Docker Production Issues

#### 1. Containers Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend

# Rebuild from scratch
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up
```

#### 2. Database Migration Issues

```bash
# Run migrations manually
docker-compose -f docker-compose.prod.yml exec backend \
  python -c "from app.database import init_db; init_db()"
```

## Verification Checklist

### Before Deployment

- [ ] Run `.husky/deployment-checklist`
- [ ] Test with `./scripts/test-prod-all.sh`
- [ ] Build succeeds locally
- [ ] No console.log statements in production code
- [ ] Environment variables configured
- [ ] Database connection tested

### After Deployment

- [ ] Service health checks pass
- [ ] API documentation accessible
- [ ] Frontend loads without errors
- [ ] Authentication flow works
- [ ] API calls succeed
- [ ] No CORS errors

### Production Verification

```bash
# Full verification
python scripts/verify-deployments.py \
  --backend https://your-app.onrender.com \
  --frontend https://your-app.vercel.app

# Check specific endpoints
curl https://your-app.onrender.com/health
curl https://your-app.onrender.com/docs
```

## Emergency Rollback

### Render
1. Go to Render dashboard
2. Select your service
3. Click "Rollback" to previous deploy
4. Or use CLI: `render deploy rollback --service <name>`

### Vercel
1. Go to Vercel dashboard
2. Select your project
3. Go to "Deployments"
4. Click "..." on a previous deployment
5. Select "Promote to Production"

## Getting Help

### Logs and Monitoring

**Render Logs:**
```bash
render logs --service <service-name> --tail
```

**Vercel Logs:**
```bash
vercel logs --follow
```

### Debug Information

Collect this information when seeking help:

1. **Error messages** (exact text)
2. **Deployment logs** (last 100 lines)
3. **Environment configuration** (variable names, not values)
4. **Local test results** (`./scripts/test-prod-all.sh` output)
5. **Verification output** (`verify-deployments.py` results)

### Common Error Patterns

| Error | Likely Cause | Quick Fix |
|-------|-------------|-----------|
| `ModuleNotFoundError` | Missing dependency | Add to requirements.txt |
| `Connection refused` | Wrong port/host | Check DATABASE_URL |
| `401 Unauthorized` | Auth misconfiguration | Verify Auth0 settings |
| `CORS blocked` | Missing origin | Add to ALLOWED_ORIGINS |
| `Build exceeded limit` | Large dependencies | Optimize package.json |
| `Invalid Host header` | Proxy issue | Update webpack config |

## Prevention Tips

1. **Always test locally first:**
   ```bash
   npm run deploy:check
   ./scripts/test-prod-all.sh
   ```

2. **Use environment templates:**
   - Keep `.env.example` updated
   - Use `config/.env.production.template`

3. **Monitor after deployment:**
   - Watch logs for first 5 minutes
   - Run verification script
   - Test critical user paths

4. **Maintain documentation:**
   - Update this guide with new issues
   - Document environment changes
   - Keep README current

Remember: Most deployment issues are environment configuration problems. Double-check your environment variables first!