import { createContext, useContext, useState, useEffect } from "react";
import type { ReactNode } from "react";
import { api } from "../services/api";

interface AuthContextType {
  apiKey: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (apiKey: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Load API key from localStorage on mount
    const storedKey = api.getApiKey();
    if (storedKey) {
      setApiKey(storedKey);
    }
    setIsLoading(false);
  }, []);

  const login = (key: string) => {
    api.setApiKey(key);
    setApiKey(key);
  };

  const logout = () => {
    api.clearApiKey();
    setApiKey(null);
  };

  const isAuthenticated = !!apiKey;

  return (
    <AuthContext.Provider
      value={{ apiKey, isAuthenticated, isLoading, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
