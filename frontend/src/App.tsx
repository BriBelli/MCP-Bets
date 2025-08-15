
import './App.css';
import { useState } from 'react';
import { fetchOpenAI } from './services/openaiApi';
import { useAuth0 } from '@auth0/auth0-react';

const App: React.FC = () => {
  const [prompt, setPrompt] = useState<string>("");
  const [response, setResponse] = useState<string>("");

  const {
    isLoading, // Loading state, the SDK needs to reach Auth0 on load
    isAuthenticated,
    error,
    loginWithRedirect: login, // Starts the login flow
    logout: auth0Logout, // Starts the logout flow
    user, // User profile
  } = useAuth0();

  const signup = () =>
    login({ authorizationParams: { screen_hint: "signup" } });

  const logout = () =>
    auth0Logout({ logoutParams: { returnTo: window.location.origin } });

  const handleLogin = () => login();
  const handleSignup = () => signup();

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
        <div style={{ textAlign: 'center', marginTop: '50px' }}>
          <h1>Welcome to BetAI Predict</h1>
          {error && <p style={{ color: 'red' }}>Error: {error.message}</p>}
          <div>
            <button onClick={handleSignup} style={{ margin: '10px' }}>Sign Up</button>
            <button onClick={handleLogin} style={{ margin: '10px' }}>Login</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
