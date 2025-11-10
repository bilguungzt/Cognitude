import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useTheme } from "../contexts/useTheme";
import {
  Menu,
  X,
  Settings,
  LogOut,
  AlertCircle,
  BookOpen,
  DollarSign,
  LayoutDashboard,
  Database,
  Zap,
  Shield,
  Sun,
  Moon,
} from "lucide-react";
import { useState } from "react";

interface LayoutProps {
  children: ReactNode;
  title?: string;
}

export default function Layout({ children, title }: LayoutProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { logout } = useAuth();
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const navItems = [
    { icon: LayoutDashboard, label: "Dashboard", path: "/dashboard" },
    { icon: Database, label: "Providers", path: "/providers" },
    { icon: Zap, label: "Cache", path: "/cache" },
    { icon: DollarSign, label: "Cost Analytics", path: "/cost" },
    { icon: AlertCircle, label: "Alerts", path: "/alerts" },
    { icon: Shield, label: "Rate Limits", path: "/rate-limits" },
    { icon: BookOpen, label: "Setup", path: "/setup" },
    { icon: Settings, label: "API Docs", path: "/docs" },
  ];

  return (
    <div className="min-h-screen bg-pattern flex flex-col">
      {/* Header */}
      <header className="glass sticky top-0 z-50 border-b border-gray-200/50 shadow-sm dark:border-gray-700/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* Brand (logo removed) */}
              <div
                className="flex items-center cursor-pointer"
                onClick={() => navigate("/dashboard")}
              >
                <h1 className="text-xl sm:text-2xl font-bold text-gradient-primary">
                  Cognitude AI
                </h1>
                {title && (
                  <p className="ml-3 text-xs text-gray-500 dark:text-gray-400 hidden sm:block">
                    {title}
                  </p>
                )}
              </div>

              {/* Desktop Navigation */}
              <nav className="hidden lg:flex items-center gap-2">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = window.location.pathname === item.path;
                  return (
                    <button
                      key={item.path}
                      onClick={() => navigate(item.path)}
                      className={`flex items-center gap-2 px-2 py-1.5 rounded-md text-sm font-medium transition-all ${
                        isActive
                          ? "bg-primary-50 dark:bg-primary-90/30 text-primary-700 dark:text-primary-300 shadow-sm"
                          : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      <span className="hidden xl:inline">{item.label}</span>
                    </button>
                  );
                })}
                <button
                  onClick={toggleTheme}
                  className="p-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                  title={`Switch to ${
                    theme === "light" ? "dark" : "light"
                  } mode`}
                >
                  {theme === "light" ? (
                    <Moon className="w-5 h-5" />
                  ) : (
                    <Sun className="w-5 h-5" />
                  )}
                </button>
                <div className="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-2" />
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 px-2 py-1.5 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-danger-50 dark:hover:bg-danger-900/30 hover:text-danger-700 dark:hover:text-danger-300 transition-all"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden xl:inline">Logout</span>
                </button>
              </nav>
            </div>

            {/* Mobile Menu Button */}
            <div className="flex items-center gap-2">
              <button
                onClick={toggleTheme}
                className="p-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors lg:hidden"
                title={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
              >
                {theme === "light" ? (
                  <Moon className="w-5 h-5" />
                ) : (
                  <Sun className="w-5 h-5" />
                )}
              </button>
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="lg:hidden p-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                {mobileMenuOpen ? (
                  <X className="w-6 h-6" />
                ) : (
                  <Menu className="w-6 h-6" />
                )}
              </button>
            </div>
          </div>

          {/* Mobile Navigation Menu */}
          {mobileMenuOpen && (
            <nav className="lg:hidden mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 animate-slide-down">
              <div className="flex flex-col gap-2">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = window.location.pathname === item.path;
                  return (
                    <button
                      key={item.path}
                      onClick={() => {
                        navigate(item.path);
                        setMobileMenuOpen(false);
                      }}
                      className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all text-left ${
                        isActive
                          ? "bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300"
                          : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      {item.label}
                    </button>
                  );
                })}
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg font-medium text-gray-700 dark:text-gray-300 hover:bg-danger-50 dark:hover:bg-danger-900/30 hover:text-danger-700 dark:hover:text-danger-300 transition-all text-left"
                >
                  <LogOut className="w-5 h-5" />
                  Logout
                </button>
              </div>
            </nav>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">{children}</main>

      {/* Footer */}
      <footer className="border-t border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              © 2025 Cognitude AI. All rights reserved.
            </p>
            <div className="flex items-center gap-6">
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
              >
                GitHub
              </a>
              <a
                href="/docs"
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-40 transition-colors"
              >
                Documentation
              </a>
              <a
                href="mailto:support@cognitude.ai"
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
              >
                Support
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
