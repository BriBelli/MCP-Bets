import React, { useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import './CustomLogin.css';

interface CustomLoginProps {
  onClose: () => void;
}

const CustomLogin: React.FC<CustomLoginProps> = ({ onClose }) => {
  const { loginWithRedirect } = useAuth0();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSignUp, setIsSignUp] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // For now, we'll redirect to Auth0's hosted login
    // Later we can implement direct API authentication
    if (isSignUp) {
      await loginWithRedirect({
        authorizationParams: {
          screen_hint: 'signup',
          login_hint: email
        }
      });
    } else {
      await loginWithRedirect({
        authorizationParams: {
          login_hint: email
        }
      });
    }
  };

  return (
    <div className="login-overlay">
      <div className="login-modal">
        <button className="close-button" onClick={onClose}>×</button>
        
        <div className="login-header">
          <h2>{isSignUp ? 'Create Account' : 'Welcome Back'}</h2>
          <p>{isSignUp ? 'Sign up to start making predictions' : 'Sign in to your account'}</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>

          <button type="submit" className="login-button">
            {isSignUp ? 'Create Account' : 'Sign In'}
          </button>
        </form>

        <div className="login-footer">
          <p>
            {isSignUp ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button 
              type="button" 
              className="toggle-button"
              onClick={() => setIsSignUp(!isSignUp)}
            >
              {isSignUp ? 'Sign In' : 'Sign Up'}
            </button>
          </p>
        </div>

        <div className="divider">
          <span>or</span>
        </div>

        <div className="social-login">
          <button type="button" className="google-button">
            Continue with Google
          </button>
        </div>
      </div>
    </div>
  );
};

export default CustomLogin;
