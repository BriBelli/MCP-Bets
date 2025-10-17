
import './App.css';
import { useState, useEffect } from 'react';
import { fetchOpenAI } from './services/openaiApi';
import { useAuth0 } from '@auth0/auth0-react';
import { CustomAuthUser } from './types/auth';
import { isValidAuthData, getStoredUser, clearAuthData } from './utils/auth';
import CustomLogin from './components/CustomLogin';

const App: React.FC = () => {
  const [prompt, setPrompt] = useState<string>("");
  const [response, setResponse] = useState<string>("");
  const [showLogin, setShowLogin] = useState<boolean>(false);
  const [customAuthUser, setCustomAuthUser] = useState<CustomAuthUser | null>(null);

  const {
    isLoading, // Loading state, the SDK needs to reach Auth0 on load
    isAuthenticated,
    error,
    logout: auth0Logout, // Starts the logout flow
    user, // User profile
  } = useAuth0();

  // Check for custom authentication tokens on app load
  useEffect(() => {
    const checkCustomAuth = (): void => {
      if (isValidAuthData()) {
        const user = getStoredUser();
        if (user) {
          setCustomAuthUser(user);
        }
      } else {
        // Clear invalid or expired data
        clearAuthData();
        setCustomAuthUser(null);
      }
    };

    checkCustomAuth();
  }, []);

  // Combined authentication check
  const isUserAuthenticated = isAuthenticated || customAuthUser;
  const currentUser = user || customAuthUser;

  const logout = (): void => {
    // Clear custom auth data
    clearAuthData();
    setCustomAuthUser(null);
    
    // Also logout from Auth0 SDK if applicable
    if (isAuthenticated) {
      auth0Logout({ logoutParams: { returnTo: window.location.origin } });
    } else {
      // Just reload the page to reset state
      window.location.reload();
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setResponse("Loading...");
    const result = await fetchOpenAI(prompt);
    setResponse(result);
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      {isUserAuthenticated ? (
        <>
          <header style={{ marginBottom: '20px', padding: '10px', borderBottom: '1px solid #ccc' }}>
            <p>Logged in as {currentUser?.email}</p>
            <button onClick={logout}>Logout</button>
          </header>

          <h1>MCP Bets - AI Betting Intelligence</h1>
          <form onSubmit={handleSubmit}>
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your prompt"
            />
            <button type="submit">Send</button>
          </form>
          <div>
            <strong>Response:</strong>
            <div>{response}</div>
          </div>

          <details style={{ marginTop: '20px' }}>
            <summary>User Profile</summary>
            <pre>{JSON.stringify(user, null, 2)}</pre>
          </details>
        </>
      ) : (
        <>
          <div style={{ textAlign: 'center', marginTop: '50px' }}>
            <h1>Welcome to MCP Bets</h1>
            <div>
              <button onClick={() => setShowLogin(true)} style={{ 
                margin: '10px', 
                padding: '12px 24px',
                fontSize: '16px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer'
              }}>
                Get Started
              </button>
            </div>
          </div>

          {showLogin && (
            <CustomLogin onClose={() => setShowLogin(false)} />
          )}
        </>
      )}
    </div>
  );
};

export default App;
