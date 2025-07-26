# Frontend Deployment Guide

## Environment Variables

### Local Development
For local development, the frontend uses the proxy configuration in `package.json`:
```json
"proxy": "http://localhost:8000"
```

This means `API_URL` will be empty and requests will be proxied to `http://localhost:8000`.

### Production Deployment (Vercel)

For production deployment on Vercel, you need to set the following environment variable:

1. Go to your Vercel project dashboard
2. Navigate to Settings → Environment Variables
3. Add the following environment variable:
   - **Name**: `REACT_APP_API_URL`
   - **Value**: `https://wolf-goat-pig.onrender.com`
   - **Environment**: Production, Preview, Development

### Environment Variable Configuration

The frontend uses `API_URL = process.env.REACT_APP_API_URL || ""` for all API calls.

- **Local Development**: `API_URL` is empty, uses proxy
- **Production**: `API_URL` points to Render backend

## CORS Configuration

The backend has been configured to allow all origins without CORS restrictions. No additional CORS configuration is needed on the frontend.

## Deployment Steps

1. **Set Environment Variables** in Vercel dashboard
2. **Deploy** - Vercel will automatically build and deploy when you push to GitHub
3. **Verify** - Check that the frontend can communicate with the backend

## Troubleshooting

If you see CORS errors:
1. Verify the `REACT_APP_API_URL` environment variable is set correctly in Vercel
2. Check that the backend is running on Render
3. Ensure the backend URL is accessible 