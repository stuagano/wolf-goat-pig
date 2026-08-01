# Frontend Routing

Firebase Hosting serves the React SPA. The catch-all rewrite in the root
`firebase.json` sends every non-static route to `/index.html`:

```json
{
  "rewrites": [
    { "source": "**", "destination": "/index.html" }
  ]
}
```

This lets React Router handle routes such as `/signup`, `/account`, and
`/game/123` while Firebase serves existing static assets directly.

Production routing smoke tests live under `frontend/tests/e2e/tests/`.
