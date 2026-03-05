# Auth0 Setup Instructions for Wolf Goat Pig

## Quick Setup Guide

Follow these steps to get Auth0 working with your Wolf Goat Pig application:

### 1. Create Auth0 Account and Application

1. Go to [auth0.com](https://auth0.com) and create a free account
2. In the Auth0 Dashboard, click "Create Application"
3. Choose "Single Page Web Applications"
4. Name it "Wolf Goat Pig" or similar
5. Select "React" as the technology

### 2. Configure Your Auth0 Application

In your Auth0 application settings, configure these URLs:

**Allowed Callback URLs:**
```
http://localhost:3000, https://your-production-domain.com
```

**Allowed Logout URLs:**
```
http://localhost:3000, https://your-production-domain.com
```

**Allowed Web Origins:**
```
http://localhost:3000, https://your-production-domain.com
```

**Allowed Origins (CORS):**
```
http://localhost:3000, https://your-production-domain.com
```

### 3. Update Environment Variables

Copy your Auth0 credentials from the Dashboard > Applications > Wolf Goat Pig > Settings:

1. **Domain**: Found under "Domain" (looks like: `dev-xxx.us.auth0.com`)
2. **Client ID**: Found under "Client ID" (long string of characters)

Update your `.env.local` file:

```bash
# Replace these with your actual Auth0 credentials
REACT_APP_AUTH0_DOMAIN=your-actual-domain.us.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your-actual-client-id
REACT_APP_AUTH0_AUDIENCE=https://api.wolf-goat-pig.com
REACT_APP_API_URL=http://localhost:8000

# Set to false to use real Auth0, true for testing with mock auth
REACT_APP_USE_MOCK_AUTH=false
```

### 4. Test the Integration

1. Restart your development server: `npm start`
2. Try to access a protected route like `/game` or `/simulation`
3. You should be redirected to Auth0's login page
4. After logging in, you should be redirected back to the application

### 5. Switch Between Real Auth0 and Mock Auth

The application is configured to support both modes:

**For development/testing with mock auth:**
```bash
REACT_APP_USE_MOCK_AUTH=true
```

**For production/real Auth0:**
```bash
REACT_APP_USE_MOCK_AUTH=false
```

## Features Included

✅ **Route Protection**: Game, Simulation, Analytics, and other features require login
✅ **Login/Logout**: Proper Auth0 integration with secure redirect flow  
✅ **User Profile**: Display user name in navigation
✅ **Public Routes**: Home page and Tutorial remain accessible without login
✅ **Mock Mode**: Easy switching between real Auth0 and mock auth for development

## Troubleshooting

### Common Issues:

1. **"Please define REACT_APP_AUTH0_DOMAIN" Error**
   - Make sure you've updated `.env.local` with real credentials
   - Restart the development server after changing environment variables

2. **Callback URL Error**
   - Verify the callback URLs in Auth0 dashboard match exactly: `http://localhost:3000`
   - No trailing slashes

3. **CORS Issues**
   - Ensure "Allowed Web Origins" includes your domain
   - Check that there are no extra spaces in the URLs

4. **Still seeing mock user**
   - Make sure `REACT_APP_USE_MOCK_AUTH=false` in `.env.local`
   - Restart the development server

### Testing Auth0 Integration:

1. Set `REACT_APP_USE_MOCK_AUTH=false`
2. Navigate to `/game`
3. Should redirect to Auth0 login
4. After login, should return to the game
5. User name should appear in navigation
6. Logout should work and redirect to home

## Next Steps (Optional)

For production deployment:
1. Add your production domain to Auth0 application settings
2. Consider setting up Auth0 Rules for additional user management
3. Implement JWT token validation in your FastAPI backend
4. Set up user roles and permissions if needed

The Auth0 integration is now complete and ready to use!