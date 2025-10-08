# GitHub Copilot Instructions for MCP Bets

## Project Overview

MCP Bets is a React/TypeScript frontend with Python backend application for AI-powered betting predictions. The application features custom Auth0 authentication and integrates with OpenAI for intelligent betting analysis.

## Code Style & Standards

### TypeScript/React Guidelines
- Use functional components with hooks (no class components)
- Implement proper TypeScript interfaces - avoid `any` types
- Use explicit return types for functions
- Follow React best practices for state management
- Implement proper error boundaries and loading states

### Authentication System
- **CRITICAL**: Never modify the authentication flow without understanding the hybrid Auth0 approach
- Use existing interfaces from `/src/types/auth.ts`
- Leverage utility functions from `/src/utils/auth.ts` for auth operations
- Maintain compatibility with Auth0 React SDK while supporting custom UI

### File Structure Conventions
```
frontend/src/
├── components/          # Reusable UI components
├── pages/              # Page-level components (future)
├── services/           # API integration layers
├── types/              # TypeScript interfaces and types
├── utils/              # Utility functions and helpers
├── hooks/              # Custom React hooks (future)
└── styles/             # Global styles and themes (future)
```

## Authentication System Architecture

### Critical Implementation Details
The authentication system uses a **hybrid approach**:

1. **Custom UI**: `CustomLogin.tsx` provides branded login experience
2. **Direct API**: Uses Auth0's Resource Owner Password Grant for authentication
3. **Token Management**: Stores tokens in Auth0 SDK-compatible localStorage format
4. **State Management**: Combines Auth0 SDK state with custom authentication state

### Key Components to Understand
- `CustomLogin.tsx`: Main authentication interface
- `App.tsx`: Authentication state management
- `/types/auth.ts`: TypeScript interfaces for auth data
- `/utils/auth.ts`: Authentication utility functions

### Authentication Flow Preservation
- **DO NOT** change token storage keys or format
- **MAINTAIN** compatibility with Auth0 React SDK
- **PRESERVE** multi-connection fallback logic
- **KEEP** expiration time tracking in token storage

## Development Guidelines

### When Working on Authentication
1. **Read Documentation First**: Review `/docs/authentication-system.md`
2. **Test Thoroughly**: Authentication changes require extensive testing
3. **Maintain Backward Compatibility**: Don't break existing auth flow
4. **Use Existing Utilities**: Leverage functions from `/utils/auth.ts`

### Error Handling Standards
- Provide user-friendly error messages
- Implement proper loading states
- Use TypeScript for compile-time error prevention
- Log errors appropriately (avoid sensitive data in logs)

### Code Quality Requirements
- All new code must include proper TypeScript types
- Components should be properly documented with JSDoc
- Implement proper error boundaries for new features
- Follow existing naming conventions and patterns

## API Integration Patterns

### Frontend-Backend Communication
- Use `/services/` directory for API integration
- Implement proper error handling for API calls
- Use TypeScript interfaces for API responses
- Include loading states for async operations

### OpenAI Integration
- Backend handles OpenAI API calls for security
- Frontend sends prompts via backend API
- Implement proper response formatting and error handling

## Security Considerations

### Authentication Security
- Never expose Auth0 client secrets in frontend
- Validate tokens on both frontend and backend
- Implement proper token expiration handling
- Use HTTPS in production environments

### Data Protection
- Sanitize user inputs
- Implement proper CORS configuration
- Avoid storing sensitive data in localStorage
- Use environment variables for configuration

## Testing Strategy

### Authentication Testing
- Test login/logout flows thoroughly
- Verify token persistence across page reloads
- Test password reset functionality
- Validate error handling for various scenarios

### Component Testing
- Write unit tests for utility functions
- Test component rendering and user interactions
- Mock API calls in tests
- Test error states and edge cases

## Common Patterns

### State Management
```typescript
// Preferred state pattern
const [data, setData] = useState<TypeName | null>(null);
const [loading, setLoading] = useState<boolean>(false);
const [error, setError] = useState<string | null>(null);
```

### API Call Pattern
```typescript
// Preferred async pattern
const handleApiCall = async (): Promise<void> => {
  setLoading(true);
  setError(null);
  
  try {
    const result = await apiFunction();
    setData(result);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    setError(errorMessage);
  } finally {
    setLoading(false);
  }
};
```

### Component Structure
```typescript
// Preferred component pattern
interface ComponentProps {
  // Define props with proper types
}

const Component: React.FC<ComponentProps> = ({ prop1, prop2 }) => {
  // State and hooks
  // Event handlers
  // Render logic
  
  return (
    // JSX with proper TypeScript
  );
};

export default Component;
```

## Debugging Guidelines

### Authentication Issues
1. Check browser localStorage for token data
2. Verify Auth0 application configuration
3. Test API endpoints independently
4. Review network tab for failed requests
5. Check console for TypeScript/JavaScript errors

### Common Debug Points
- Token expiration and refresh logic
- Auth0 SDK state vs custom auth state
- API response parsing and error handling
- Component re-rendering and state updates

## Environment Setup

### Required Environment Variables
```bash
# Frontend (.env.local)
REACT_APP_AUTH0_DOMAIN=your-domain.auth0.com
REACT_APP_AUTH0_CLIENT_ID=your-client-id

# Backend (configure as needed)
OPENAI_API_KEY=your-openai-key
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_SECRET=your-client-secret
```

## Documentation Maintenance

### When Adding New Features
1. Update relevant documentation in `/docs/`
2. Add TypeScript interfaces to appropriate files
3. Update this copilot-instructions.md if patterns change
4. Include JSDoc comments for complex functions

### Documentation Standards
- Keep documentation current with code changes
- Use clear, concise language
- Include code examples for complex patterns
- Document breaking changes and migration paths

## Migration Considerations

### Future Auth0 Updates
- Monitor Auth0 SDK updates for breaking changes
- Test authentication flow after any Auth0 library updates
- Consider migrating to PKCE flow for enhanced security
- Plan for deprecation of Resource Owner Password Grant

### React/TypeScript Updates
- Keep dependencies updated regularly
- Test thoroughly after major version updates
- Update TypeScript types as needed
- Maintain backward compatibility where possible

---

**Note**: This document should be updated as the project evolves. Always refer to the latest version in the repository and update it when implementing significant changes or new patterns.

**Last Updated**: October 8, 2025