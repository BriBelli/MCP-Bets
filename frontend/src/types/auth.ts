// TypeScript interfaces for Auth0 authentication

export interface Auth0TokenResponse {
  access_token: string;
  id_token: string;
  expires_in: number;
  token_type: string;
  scope: string;
}

export interface Auth0ErrorResponse {
  error: string;
  error_description: string;
}

export interface Auth0UserProfile {
  email: string;
  email_verified: boolean;
  name: string;
  nickname: string;
  picture: string;
  sub: string;
  updated_at: string;
}

export interface CustomAuthUser {
  email: string;
  name: string;
  picture?: string;
  sub: string;
  [key: string]: any;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: Auth0UserProfile | CustomAuthUser | null;
  isLoading: boolean;
  error: string | null;
}