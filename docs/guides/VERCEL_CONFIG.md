# Vercel Configuration Notes

## Important: Vercel v2 Schema Limitations

### ❌ Invalid Properties (Do NOT Use)
- `rootDirectory` - This property is NOT supported in Vercel v2 schema

### ✅ Correct Configuration for Subdirectory Builds

When your frontend is in a subdirectory (e.g., `frontend/`), use these patterns:

```json
{
  "version": 2,
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/build",
  "installCommand": "cd frontend && npm ci",
  "framework": "create-react-app"
}
```

### Common Error
```
The vercel.json schema validation failed with the following message: 
should NOT have additional property 'rootDirectory'
```

### Solution
Replace `rootDirectory` with explicit `cd` commands in:
- `buildCommand`
- `outputDirectory` path
- `installCommand`

### Full Working Example

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "version": 2,
  "name": "wolf-goat-pig",
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/build",
  "installCommand": "cd frontend && npm ci",
  "framework": "create-react-app",
  "build": {
    "env": {
      "REACT_APP_API_URL": "https://wolf-goat-pig.onrender.com"
    }
  }
}
```

## Reference
- Vercel Configuration: https://vercel.com/docs/projects/project-configuration
- Schema validation is strict in Vercel v2
- Use Vercel CLI `vercel dev` to test locally before deploying

---
Last Updated: 2026-01-12
