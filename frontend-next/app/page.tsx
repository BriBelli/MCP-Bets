'use client';

import { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { CustomAuthUser } from '@/types/auth';
import { isValidAuthData, getStoredUser, clearAuthData } from '@/utils/auth';
import CustomLogin from '@/components/CustomLogin';

export default function Home() {
  const [showLogin, setShowLogin] = useState(false);
  const [customAuthUser, setCustomAuthUser] = useState<CustomAuthUser | null>(null);
  const [prompt, setPrompt] = useState<string>("");
  const [response, setResponse] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const {
    isLoading,
    isAuthenticated,
    logout: auth0Logout,
    user,
  } = useAuth0();

  useEffect(() => {
    if (isValidAuthData()) {
      const storedUser = getStoredUser();
      if (storedUser) {
        setCustomAuthUser(storedUser);
      }
    } else {
      clearAuthData();
    }
  }, []);

  const isUserAuthenticated = isAuthenticated || customAuthUser;
  const currentUser = user || customAuthUser;

  const logout = () => {
    clearAuthData();
    setCustomAuthUser(null);
    if (isAuthenticated) {
      auth0Logout({ logoutParams: { returnTo: window.location.origin } });
    } else {
      window.location.reload();
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsSubmitting(true);
    setResponse("Loading...");
    
    try {
      const result = await fetch('/api/openai', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      });
      
      if (!result.ok) {
        throw new Error('Failed to get response from API');
      }

      const data = await result.json();
      setResponse(data.response || data.message || 'No response received');
    } catch (error) {
      console.error('Error:', error);
      setResponse('Error: ' + (error instanceof Error ? error.message : 'Failed to connect to AI service'));
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen p-8 bg-gradient-to-br from-gray-50 to-gray-100">
      {isUserAuthenticated ? (
        <div>
          <header className="mb-8 pb-4 border-b bg-white rounded-lg p-6 shadow">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-3xl font-bold">MCP Bets</h1>
                <p className="text-gray-600">AI-Powered Betting Intelligence</p>
              </div>
              <div className="flex items-center gap-4">
                <p className="text-sm">Logged in as <span className="font-semibold">{currentUser?.email}</span></p>
                <button onClick={logout} className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600">
                  Logout
                </button>
              </div>
            </div>
          </header>
          <main className="max-w-4xl mx-auto">
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-2xl font-bold mb-6 text-gray-900">MCP Bets - AI Betting Intelligence</h2>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
                    Enter your prompt
                  </label>
                  <input
                    id="prompt"
                    type="text"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="Ask me anything about sports betting..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-400"
                    disabled={isSubmitting}
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={isSubmitting || !prompt.trim()}
                  className="w-full px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Sending...' : 'Send'}
                </button>
              </form>

              {response && (
                <div className="mt-6">
                  <h3 className="font-semibold mb-2 text-gray-900">Response:</h3>
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-gray-700 whitespace-pre-wrap">{response}</p>
                  </div>
                </div>
              )}
            </div>
          </main>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center min-h-screen">
          <div className="text-center">
            <h1 className="text-6xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Welcome to MCP Bets
            </h1>
            <p className="text-xl text-gray-600 mb-8">AI-Powered Betting Intelligence</p>
            <button 
              onClick={() => setShowLogin(true)}
              className="px-8 py-4 bg-blue-500 text-white text-lg rounded-lg hover:bg-blue-600 font-semibold shadow-lg"
            >
              Get Started
            </button>
          </div>
        </div>
      )}
      {showLogin && <CustomLogin onClose={() => setShowLogin(false)} />}
    </div>
  );
}
