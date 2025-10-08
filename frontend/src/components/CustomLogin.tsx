import React, { useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { Auth0TokenResponse, Auth0ErrorResponse, Auth0UserProfile, LoginCredentials } from '../types/auth';
import './CustomLogin.css';

interface CustomLoginProps {
  onClose: () => void;
}

type ViewMode = 'login' | 'signup' | 'forgot-password';

const STORAGE_KEYS = {
  TOKENS: `@@auth0spajs@@::${process.env.REACT_APP_AUTH0_CLIENT_ID}::${process.env.REACT_APP_AUTH0_DOMAIN}::openid profile email`,
  USER: 'custom_auth_user'
} as const;

const CustomLogin: React.FC<CustomLoginProps> = ({ onClose }) => {
  const { loginWithRedirect } = useAuth0();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [viewMode, setViewMode] = useState<ViewMode>('login');
  const [resetEmailSent, setResetEmailSent] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null); // Clear any previous errors
    
    try {
      if (viewMode === 'login') {
        await handleDirectLogin();
      } else if (viewMode === 'signup') {
        // For signup, we still redirect to Auth0's hosted page for security
        await loginWithRedirect({
          authorizationParams: {
            screen_hint: 'signup',
            login_hint: email
          }
        });
      } else if (viewMode === 'forgot-password') {
        await handlePasswordReset();
      }
    } catch (error) {
      console.error('Authentication error:', error);
      setIsLoading(false);
    }
  };

  const handleDirectLogin = async () => {
    try {
      const auth0Domain = process.env.REACT_APP_AUTH0_DOMAIN;
      const clientId = process.env.REACT_APP_AUTH0_CLIENT_ID;

      console.log('Attempting direct login with:', { auth0Domain, clientId, email });

      // Step 1: Try different connection names
      const connectionNames = [
        'Username-Password-Authentication',
        'email', 
        'database',
        null // no connection parameter
      ];

      let authResponse;
      let authData;
      let lastError;

      for (const connectionName of connectionNames) {
        console.log(`Trying connection: ${connectionName || 'default'}`);
        
        const requestBody: any = {
          grant_type: 'password',
          username: email,
          password: password,
          client_id: clientId,
          scope: 'openid profile email'
        };

        if (connectionName) {
          requestBody.connection = connectionName;
        }

        authResponse = await fetch(`https://${auth0Domain}/oauth/token`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestBody),
        });

        authData = await authResponse.json();
        console.log(`Auth response (${connectionName || 'default'}):`, authResponse.status, authData);

        if (authResponse.ok) {
          console.log('✅ Success with connection:', connectionName || 'default');
          break; // Success! Exit the loop
        } else {
          lastError = authData;
          console.log(`❌ Failed with connection: ${connectionName || 'default'} - ${authData.error_description}`);
        }
      }

      if (!authResponse || !authResponse.ok) {
        throw new Error(lastError?.error_description || 'All connection attempts failed');
      }

      // Step 2: Get user profile
      const userResponse = await fetch(`https://${auth0Domain}/userinfo`, {
        headers: {
          'Authorization': `Bearer ${authData.access_token}`,
        },
      });

      if (!userResponse.ok) {
        throw new Error('Failed to fetch user profile');
      }

      const userData = await userResponse.json();
      console.log('User data:', userData);
      
      // Step 3: Authentication successful! Store tokens and user data
      console.log('✅ Direct authentication successful!');
      
      // Store the tokens in localStorage (Auth0 SDK compatible format)
      const tokenKey = `@@auth0spajs@@::${process.env.REACT_APP_AUTH0_CLIENT_ID}::${process.env.REACT_APP_AUTH0_DOMAIN}::openid profile email`;
      const tokenData = {
        access_token: authData.access_token,
        id_token: authData.id_token,
        expires_in: authData.expires_in,
        token_type: authData.token_type,
        scope: authData.scope
      };
      
      localStorage.setItem(tokenKey, JSON.stringify(tokenData));
      
      // Store user data separately for our custom auth check
      localStorage.setItem('custom_auth_user', JSON.stringify(userData));
      
      // Close modal and let the app detect the authentication
      onClose();
      
      // Trigger a page reload to let the app pick up the stored tokens and user data
      window.location.reload();
      
    } catch (error) {
      console.error('Direct login error:', error);
      
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      
      // Only show custom error messages - NO fallback to Auth0 hosted login
      if (errorMessage.includes('Wrong email or password') || errorMessage.includes('invalid_grant')) {
        setError('Invalid email or password. Please check your credentials and try again.');
      } else if (errorMessage.includes('user_not_found')) {
        setError('Account not found. Please check your email or sign up for a new account.');
      } else if (errorMessage.includes('not configured')) {
        setError('Authentication service configuration error. Please try again later.');
      } else {
        setError(`Login failed: ${errorMessage}`);
      }
      
      setIsLoading(false);
    }
  };

  const handlePasswordReset = async () => {
    try {
      // Use Auth0's password reset API
      const auth0Domain = process.env.REACT_APP_AUTH0_DOMAIN;
      const clientId = process.env.REACT_APP_AUTH0_CLIENT_ID;
      
      const response = await fetch(`https://${auth0Domain}/dbconnections/change_password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          client_id: clientId,
          email: email,
          connection: 'Username-Password-Authentication', // Default Auth0 database connection
        }),
      });

      if (response.ok) {
        setResetEmailSent(true);
      } else {
        throw new Error('Failed to send reset email');
      }
    } catch (error) {
      console.error('Password reset error:', error);
      // You might want to show an error message to the user here
    }
  };

  const renderContent = () => {
    if (viewMode === 'forgot-password' && resetEmailSent) {
      return (
        <div className="reset-success">
          <div className="success-icon">✉️</div>
          <h2>Check your email</h2>
          <p>
            We've sent a password reset link to <strong>{email}</strong>
          </p>
          <p className="helper-text">
            Didn't receive the email? Check your spam folder or try again.
          </p>
          <button 
            type="button" 
            className="login-button"
            onClick={() => {
              setResetEmailSent(false);
              setViewMode('login');
              setEmail('');
            }}
          >
            Back to Login
          </button>
          <button 
            type="button" 
            className="resend-button"
            onClick={handlePasswordReset}
            disabled={isLoading}
          >
            {isLoading ? 'Sending...' : 'Resend Email'}
          </button>
        </div>
      );
    }

    return (
      <>
        <div className="login-header">
          <h2>
            {viewMode === 'login' && 'Welcome back'}
            {viewMode === 'signup' && 'Create your account'}
            {viewMode === 'forgot-password' && 'Reset your password'}
          </h2>
          <p>
            {viewMode === 'login' && 'Sign in to your MCP Bets account'}
            {viewMode === 'signup' && 'Get started with MCP Bets'}
            {viewMode === 'forgot-password' && 'Enter your email to receive a reset link'}
          </p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              {error}
            </div>
          )}
          
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
              disabled={isLoading}
            />
          </div>

          {(viewMode === 'login' || viewMode === 'signup') && (
            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                disabled={isLoading}
              />
            </div>
          )}

          {viewMode === 'login' && (
            <div className="forgot-password-link">
              <button
                type="button"
                className="link-button"
                onClick={() => setViewMode('forgot-password')}
                disabled={isLoading}
              >
                Forgot your password?
              </button>
            </div>
          )}

          <button type="submit" className="login-button" disabled={isLoading}>
            {isLoading && '⏳ '}
            {viewMode === 'login' && (isLoading ? 'Signing In...' : 'Sign In')}
            {viewMode === 'signup' && (isLoading ? 'Creating Account...' : 'Create Account')}
            {viewMode === 'forgot-password' && (isLoading ? 'Sending...' : 'Send Reset Link')}
          </button>
        </form>

        <div className="login-footer">
          {viewMode === 'login' && (
            <p>
              Don't have an account?{' '}
              <button
                type="button"
                className="toggle-button"
                onClick={() => setViewMode('signup')}
                disabled={isLoading}
              >
                Sign up
              </button>
            </p>
          )}
          {viewMode === 'signup' && (
            <p>
              Already have an account?{' '}
              <button
                type="button"
                className="toggle-button"
                onClick={() => setViewMode('login')}
                disabled={isLoading}
              >
                Sign in
              </button>
            </p>
          )}
          {viewMode === 'forgot-password' && (
            <p>
              Remember your password?{' '}
              <button
                type="button"
                className="toggle-button"
                onClick={() => setViewMode('login')}
                disabled={isLoading}
              >
                Back to Sign In
              </button>
            </p>
          )}
        </div>

        {viewMode !== 'forgot-password' && (
          <>
            <div className="divider">
              <span>or</span>
            </div>

            <div className="social-login">
              <button type="button" className="google-button" disabled={isLoading}>
                Continue with Google
              </button>
            </div>
          </>
        )}
      </>
    );
  };

  return (
    <div className="login-overlay" onClick={onClose}>
      <div className="login-modal" onClick={(e) => e.stopPropagation()}>
        <button className="close-button" onClick={onClose}>
          ×
        </button>
        {renderContent()}
      </div>
    </div>
  );
};

export default CustomLogin;
