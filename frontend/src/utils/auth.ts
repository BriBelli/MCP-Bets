// Utility functions for authentication management

export const STORAGE_KEYS = {
  TOKENS: `@@auth0spajs@@::${process.env.REACT_APP_AUTH0_CLIENT_ID}::${process.env.REACT_APP_AUTH0_DOMAIN}::openid profile email`,
  USER: 'custom_auth_user'
} as const;

/**
 * Check if stored tokens are expired
 */
export const isTokenExpired = (): boolean => {
  try {
    const storedTokens = localStorage.getItem(STORAGE_KEYS.TOKENS);
    if (!storedTokens) return true;

    const tokens = JSON.parse(storedTokens);
    const expirationTime = tokens.expires_at || 
      (Date.now() + (tokens.expires_in * 1000));
    
    return Date.now() >= expirationTime;
  } catch {
    return true;
  }
};

/**
 * Clear all authentication data
 */
export const clearAuthData = (): void => {
  localStorage.removeItem(STORAGE_KEYS.TOKENS);
  localStorage.removeItem(STORAGE_KEYS.USER);
};

/**
 * Get stored user data with validation
 */
export const getStoredUser = (): any => {
  try {
    const storedUser = localStorage.getItem(STORAGE_KEYS.USER);
    return storedUser ? JSON.parse(storedUser) : null;
  } catch {
    clearAuthData();
    return null;
  }
};

/**
 * Validate stored authentication data
 */
export const isValidAuthData = (): boolean => {
  const tokens = localStorage.getItem(STORAGE_KEYS.TOKENS);
  const user = localStorage.getItem(STORAGE_KEYS.USER);
  
  return !!(tokens && user && !isTokenExpired());
};