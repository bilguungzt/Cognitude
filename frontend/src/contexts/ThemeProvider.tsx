import React, { useEffect, useState } from 'react';
import { ThemeContext, type ThemeContextType } from './ThemeContext';

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<'light' | 'dark'>('light');

 useEffect(() => {
    // Check for saved theme preference or system preference
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme) {
      setThemeState(savedTheme);
    } else if (systemPrefersDark) {
      setThemeState('dark');
    } else {
      setThemeState('light');
    }
 }, []);

  useEffect(() => {
    // Apply theme to document
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [theme]);

  const value: ThemeContextType = {
    theme,
    toggleTheme: () => setThemeState(prev => prev === 'light' ? 'dark' : 'light'),
    setTheme: setThemeState,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};