# Frontend Routing Configuration

## Vercel Rewrite Rules

The `vercel.json` file contains two rewrite rules that work together to enable React Router:

### Rule 1: Root Path
```json
{
  "source": "/",
  "destination": "/index.html"
}
```
Handles requests to the root path `/` and serves `index.html`.

### Rule 2: Catch-All Routes
```json
{
  "source": "/:path((?!.*\\.).*)",
  "destination": "/index.html"
}
```
Handles all other routes that don't contain a file extension (no dots in the path).

## Why Both Rules Are Needed

**The regex pattern `/:path((?!.*\\.).*)` doesn't match the root path `/`** because:
- The pattern requires a `path` segment after the slash
- The negative lookahead `(?!.*\\.)` requires some content to check for dots
- An empty string after `/` doesn't satisfy these conditions

Therefore, we need an explicit rule for `/` (Rule 1) and a catch-all for other routes (Rule 2).

## What Gets Rewritten

✅ **Rewritten to index.html:**
- `/` (root)
- `/about`
- `/rules`
- `/game/123`
- `/user/profile`

❌ **NOT rewritten (served as static files):**
- `/static/js/main.js`
- `/styles.css`
- `/logo.png`
- `/manifest.json`
- Any path with a file extension

## Testing

Integration tests for these routing rules can be found in:
```
tests/e2e/tests/routing-integration.spec.js
```

Run the tests with:
```bash
cd tests/e2e
npm test routing-integration.spec.js
```
