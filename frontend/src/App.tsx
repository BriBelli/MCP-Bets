
import './App.css';
import { useState } from 'react';
import { fetchOpenAI } from './services/openaiApi';
import { useAuth0 } from '@auth0/auth0-react';
import CustomLogin from './components/CustomLogin';

const App: React.FC = () => {
  const [prompt, setPrompt] = useState<string>("");
  const [response, setResponse] = useState<string>("");
  const [showLogin, setShowLogin] = useState<boolean>(false);

  const {
    isLoading, // Loading state, the SDK needs to reach Auth0 on load
    isAuthenticated,
    error,
    logout: auth0Logout, // Starts the logout flow
    user, // User profile
  } = useAuth0();

  const logout = () =>
    auth0Logout({ logoutParams: { returnTo: window.location.origin } });

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setResponse("Loading...");
    const result = await fetchOpenAI(prompt);
    setResponse(result);
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      {isAuthenticated ? (
        <>
          <header style={{ marginBottom: '20px', padding: '10px', borderBottom: '1px solid #ccc' }}>
            <p>Logged in as {user?.email}</p>
            <button onClick={logout}>Logout</button>
          </header>

          <h1>BetAI Predict - OpenAI Prompt</h1>
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
            <h1>Welcome to BetAI Predict</h1>
            {error && <p style={{ color: 'red' }}>Error: {error.message}</p>}
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
