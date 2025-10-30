# MCP Bets Authentication System Documentation

## Overview

The MCP Bets application implements a custom Auth0-based authentication system that provides a seamless user experience without redirecting to Auth0's hosted login pages. The system combines direct Auth0 API integration with the Auth0 React SDK for optimal security and user experience.

## Architecture

### Core Components

1. **CustomLogin Component** (`/src/components/CustomLogin.tsx`)
   - Custom login modal with branded UI
   - Direct Auth0 API authentication via Resource Owner Password Grant
   - Multi-connection fallback mechanism
   - Password reset functionality
   - TypeScript interfaces for type safety

2. **App Component** (`/src/App.tsx`)
   - Hybrid authentication state management
   - Token validation and expiration handling
   - Seamless logout functionality
   - Custom authentication state persistence

3. **Authentication Types** (`/src/types/auth.ts`)
   - TypeScript interfaces for Auth0 responses
   - User profile and token data structures
   - Authentication state management types

4. **Authentication Utilities** (`/src/utils/auth.ts`)
   - Token expiration validation
   - Secure data storage management
   - Authentication state validation utilities

## Authentication Flow

### Login Process

1. **User Interface**: Custom login modal collects email/password
2. **API Authentication**: Direct call to Auth0's `/oauth/token` endpoint
3. **Connection Fallback**: Attempts multiple connection types for reliability:
   - Username-Password-Authentication (primary)
   - email
   - database
   - default (no connection specified)
4. **User Profile**: Fetches user data from Auth0's `/userinfo` endpoint
5. **Token Storage**: Stores tokens and user data in localStorage with expiration
6. **State Update**: App recognizes authentication and updates UI

### Token Management

```typescript
// Storage keys for Auth0 SDK compatibility
const STORAGE_KEYS = {
  TOKENS: `@@auth0spajs@@::${CLIENT_ID}::${DOMAIN}::openid profile email`,
  USER: 'custom_auth_user'
}

// Token structure with expiration
interface TokenData {
  access_token: string;
  id_token: string;
  expires_in: number;
  expires_at: number; // Added for validation
  token_type: string;
  scope: string;
}
```

### Password Reset Flow

1. User clicks "Forgot Password" link
2. System calls Auth0's `/dbconnections/change_password` endpoint
3. Auth0 sends password reset email to user
4. User receives email with reset link (external to our app)

## Security Features

### Token Security
- **Expiration Validation**: Automatic token expiration checking
- **Data Validation**: Corrupted token detection and cleanup
- **Secure Storage**: localStorage with Auth0 SDK-compatible format
- **Automatic Cleanup**: Invalid data removal on authentication checks

### Error Handling
- **User-Friendly Messages**: Specific error messages for common scenarios
- **Fallback Mechanisms**: Multiple connection attempts for reliability
- **Configuration Validation**: Auth0 environment variable validation
- **Graceful Degradation**: Proper error states and recovery

## Environment Configuration

### Required Environment Variables

```bash
# Frontend (.env.local)
REACT_APP_AUTH0_DOMAIN=your-domain.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your-client-id
```

### Auth0 Application Settings

1. **Application Type**: Regular Web Application
2. **Grant Types**:
   - Authorization Code
   - Resource Owner Password (enabled for direct API auth)
3. **Allowed Callback URLs**: `http://localhost:3000`
4. **Allowed Logout URLs**: `http://localhost:3000`
5. **Allowed Web Origins**: `http://localhost:3000`

## File Structure

```
frontend/src/
├── components/
│   ├── CustomLogin.tsx          # Main login component
│   └── CustomLogin.css          # Login styling
├── types/
│   └── auth.ts                  # TypeScript interfaces
├── utils/
│   └── auth.ts                  # Authentication utilities
└── App.tsx                      # Main app with auth state
```

## API Endpoints Used

### Auth0 Authentication
- **POST** `https://{domain}/oauth/token` - Direct authentication
- **GET** `https://{domain}/userinfo` - User profile retrieval
- **POST** `https://{domain}/dbconnections/change_password` - Password reset

## Integration Points

### Auth0 React SDK Integration
The system maintains compatibility with Auth0 React SDK while providing custom UI:

```typescript
// Hybrid authentication check
const isUserAuthenticated = isAuthenticated || customAuthUser;
const currentUser = user || customAuthUser;
```

### State Management
- **Auth0 SDK State**: `isAuthenticated`, `user`, `isLoading`
- **Custom State**: `customAuthUser` for direct API authentication
- **Combined Logic**: Seamless fallback between SDK and custom auth

## Error Scenarios & Handling

### Common Error Cases
1. **Invalid Credentials**: User-friendly "Invalid email or password" message
2. **Account Not Found**: Specific message suggesting signup
3. **Service Configuration**: Generic service error for Auth0 issues
4. **Network Issues**: Graceful error handling with retry suggestions

### Recovery Mechanisms
- **Token Expiration**: Automatic cleanup and re-authentication prompt
- **Corrupted Data**: localStorage cleanup and fresh authentication
- **Connection Failures**: Multiple connection type attempts

## Testing Considerations

### Manual Testing Checklist
- [ ] Login with valid credentials
- [ ] Login with invalid credentials
- [ ] Password reset email delivery
- [ ] Token persistence across page reloads
- [ ] Logout functionality
- [ ] Token expiration handling

### Known Limitations
- Requires Resource Owner Password Grant (less secure than PKCE)
- Dependent on localStorage for token storage
- No automatic token refresh implementation

## Future Enhancements

### Security Improvements
- Implement PKCE flow for enhanced security
- Add automatic token refresh
- Implement session timeout warnings

### User Experience
- Remember login state across browser sessions
- Social login integration (Google, GitHub)
- Multi-factor authentication support

### Monitoring
- Authentication metrics and logging
- Failed login attempt tracking
- Security event monitoring

## Troubleshooting

### Common Issues

**Issue**: "Authorization server not configured with default connection"
- **Solution**: Enable Resource Owner Password Grant in Auth0 application settings

**Issue**: Login succeeds but user is not authenticated
- **Solution**: Check localStorage token format and Auth0 SDK compatibility

**Issue**: Password reset email not received
- **Solution**: Verify email delivery settings in Auth0 dashboard

**Issue**: TypeScript compilation errors
- **Solution**: Ensure all interfaces are properly imported from `/types/auth.ts`

## Maintenance Notes

- Review and update Auth0 application settings regularly
- Monitor token expiration patterns for optimal user experience
- Keep Auth0 React SDK updated for security patches
- Regularly audit localStorage usage and cleanup procedures

---

**Last Updated**: October 8, 2025
**Version**: 1.0.0
**Authors**: Development Team