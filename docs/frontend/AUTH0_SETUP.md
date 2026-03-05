# Auth0 Frontend Integration Setup

This document explains how to configure and use Auth0 authentication in the Wolf Goat Pig frontend application.

## Installation

The Auth0 React SDK has been added to the project dependencies:

```bash
npm install @auth0/auth0-react
```

## Auth0 Configuration

### 1. Auth0 Dashboard Setup

1. Create an Auth0 account at [auth0.com](https://auth0.com)
2. Create a new Single Page Application (SPA)
3. Configure the following settings in your Auth0 application:

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

### 2. Environment Variables

Update the `.env.local` file in the frontend directory:

```bash
# Auth0 Configuration
REACT_APP_AUTH0_DOMAIN=your-auth0-domain.us.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your-client-id-from-auth0-dashboard
REACT_APP_AUTH0_AUDIENCE=your-api-identifier (optional)
```

**Where to find these values:**
- **Domain**: Found in Auth0 Dashboard > Applications > Your App > Settings > Domain
- **Client ID**: Found in Auth0 Dashboard > Applications > Your App > Settings > Client ID
- **Audience**: Found in Auth0 Dashboard > APIs > Your API > Settings > Identifier (optional for basic setup)

## Features Implemented

### Authentication Components

- **LoginButton**: Displays login button when user is not authenticated
- **LogoutButton**: Displays logout button when user is authenticated
- **Profile**: Shows user avatar, name, and email when authenticated
- **ProtectedRoute**: Wrapper component that requires authentication

### Route Protection

The following routes are now protected and require authentication:
- `/game` - Main game interface
- `/simulation` - Simulation mode
- `/monte-carlo` - Monte Carlo simulation
- `/analytics` - Analytics dashboard

Public routes (no authentication required):
- `/` - Home page
- `/tutorial` - Tutorial system

### Navigation Updates

The navigation bar now displays:
- Login button when user is not authenticated
- User profile and logout button when authenticated

### Homepage Updates

- Personalized welcome message for authenticated users
- Sign-in prompt for unauthenticated users
- Clear indication of which features require authentication

## Usage Examples

### Using Auth0 in Components

```javascript
import { useAuth0 } from '@auth0/auth0-react';

function MyComponent() {
  const { user, isAuthenticated, isLoading } = useAuth0();

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      {isAuthenticated ? (
        <p>Hello {user.name}!</p>
      ) : (
        <p>Please log in</p>
      )}
    </div>
  );
}
```

### Custom useAuth Hook

A custom `useAuth` hook is available with additional utilities:

```javascript
import { useAuth } from '../hooks/useAuth';

function MyComponent() {
  const { isLoggedIn, userName, userEmail, userPicture } = useAuth();

  return (
    <div>
      {isLoggedIn && <p>Welcome {userName}!</p>}
    </div>
  );
}
```

## Security Features

- **Secure Token Storage**: Uses localStorage for token storage (configurable)
- **Automatic Token Refresh**: Auth0 handles token refresh automatically
- **Route Protection**: Sensitive routes require valid authentication
- **Logout Cleanup**: Properly clears tokens and redirects on logout

## Development Notes

1. The Auth0Provider wraps the entire application in `App.js`
2. Authentication state is automatically managed by Auth0
3. Protected routes will redirect to Auth0 login when accessed without authentication
4. The tutorial remains public to allow new users to learn the game

## Next Steps (Backend Integration)

For full security, the backend should also validate JWT tokens:
1. Add JWT middleware to FastAPI
2. Protect API endpoints
3. Validate Auth0 tokens on each request
4. Link Auth0 user IDs to internal user profiles

## Testing

The integration can be tested by:
1. Starting the development server: `npm start`
2. Navigating to protected routes (should redirect to Auth0)
3. Logging in with Auth0
4. Verifying user profile displays correctly
5. Testing logout functionality

## Troubleshooting

**Common Issues:**

1. **"Please define REACT_APP_AUTH0_DOMAIN" Error**
   - Ensure environment variables are set in `.env.local`
   - Restart the development server after adding variables

2. **Callback URL Mismatch**
   - Verify callback URLs in Auth0 dashboard match your application URLs
   - Include both development and production URLs

3. **CORS Issues**
   - Ensure Web Origins are configured in Auth0 dashboard
   - Check that your domain is correctly specified

For more information, see the [Auth0 React SDK documentation](https://auth0.com/docs/quickstart/spa/react).