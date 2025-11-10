import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import api from "../services";
import {
  BarChart3,
  Eye,
  EyeOff,
  Loader2,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

export default function LoginPageEnhanced() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [apiKey, setApiKey] = useState("");
  const [orgName, setOrgName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim()) {
      setError("Please enter your API key");
      return;
    }

    setLoading(true);
    setError("");

    try {
      // Test the API key by making a simple API call
      api.setApiKey(apiKey.trim());
      await api.getProviders();

      // If successful, log in and navigate
      login(apiKey.trim());
      setSuccess("Login successful! Redirecting...");
      setTimeout(() => navigate("/dashboard"), 500);
    } catch {
      setError("Invalid API key. Please check and try again.");
      api.clearApiKey();
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: FormEvent) => {
    e.preventDefault();
    if (!orgName.trim()) {
      setError("Please enter your organization name");
      return;
    }

    if (orgName.length < 3) {
      setError("Organization name must be at least 3 characters");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const org = await api.register(orgName.trim());

      if (org.api_key) {
        // Show the API key to the user
        setApiKey(org.api_key);
        setMode("login");
        setShowKey(true);
        setShowApiKey(true);
        setSuccess(
          "Registration successful! Your API key is displayed below. Please save it securely."
        );
        setError("");
      }
    } catch (err: unknown) {
      const error = err as { response?: { status?: number } };
      if (error.response?.status === 409) {
        setError(
          "Organization name already exists. Please choose a different name."
        );
      } else {
        setError("Failed to register. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setApiKey("");
    setOrgName("");
    setError("");
    setSuccess("");
    setShowKey(false);
    setShowApiKey(false);
  };

  return (
    <div className="min-h-screen bg-pattern flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full">
        {/* Logo and Header */}
        <div className="text-center mb-8 animate-fade-in">
          <div className="inline-flex items-center justify-center w-20 h-20 gradient-primary rounded-2xl mb-6 shadow-soft-lg animate-scale-in">
            <BarChart3 className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-gradient-primary mb-2">
            Cognitude AI
          </h1>
          <p className="text-gray-600 text-lg">
            {mode === "login"
              ? "Monitor your ML models for drift"
              : "Create your account to get started"}
          </p>
        </div>

        {/* Main Card */}
        <div className="card shadow-soft-lg animate-slide-up">
          {/* Mode Toggle */}
          <div className="flex gap-2 p-1 bg-gray-100 rounded-lg mb-6">
            <button
              onClick={() => {
                setMode("login");
                resetForm();
              }}
              className={`flex-1 py-2.5 px-4 rounded-lg font-medium transition-all ${
                mode === "login"
                  ? "bg-white text-primary-600 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => {
                setMode("register");
                resetForm();
              }}
              className={`flex-1 py-2.5 px-4 rounded-lg font-medium transition-all ${
                mode === "register"
                  ? "bg-white text-primary-600 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Register
            </button>
          </div>

          {/* Success Message */}
          {success && (
            <div className="alert-success mb-6">
              <CheckCircle className="w-5 h-5" />
              <p>{success}</p>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="alert-error mb-6">
              <AlertCircle className="w-5 h-5" />
              <p>{error}</p>
            </div>
          )}

          {/* Login Form */}
          {mode === "login" && (
            <form onSubmit={handleLogin} className="space-y-5">
              <div>
                <label htmlFor="apiKey" className="label">
                  API Key
                </label>
                <div className="relative">
                  <input
                    id="apiKey"
                    type={showApiKey ? "text" : "password"}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Enter your API key"
                    className="input pr-10"
                    disabled={loading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    {showApiKey ? (
                      <EyeOff className="w-5 h-5" />
                    ) : (
                      <Eye className="w-5 h-5" />
                    )}
                  </button>
                </div>
                {showKey && (
                  <p className="text-sm text-warning-600 mt-2 flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span>
                      Save this API key securely. You won't be able to see it
                      again.
                    </span>
                  </p>
                )}
              </div>

              <button
                type="submit"
                disabled={loading || !apiKey.trim()}
                className="btn-primary w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  "Sign In"
                )}
              </button>
            </form>
          )}

          {/* Register Form */}
          {mode === "register" && (
            <form onSubmit={handleRegister} className="space-y-5">
              <div>
                <label htmlFor="orgName" className="label">
                  Organization Name
                </label>
                <input
                  id="orgName"
                  type="text"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  placeholder="Enter your organization name"
                  className="input"
                  disabled={loading}
                />
                <p className="text-sm text-gray-500 mt-2">
                  Choose a unique name for your organization
                </p>
              </div>

              <button
                type="submit"
                disabled={loading || !orgName.trim()}
                className="btn-primary w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  "Create Account"
                )}
              </button>
            </form>
          )}

          {/* Help Text */}
          <div className="mt-6 pt-6 border-t border-gray-200 text-center">
            <p className="text-sm text-gray-600">
              {mode === "login" ? (
                <>
                  Don't have an account?{" "}
                  <button
                    onClick={() => {
                      setMode("register");
                      resetForm();
                    }}
                    className="text-primary-600 hover:text-primary-700 font-medium"
                  >
                    Register now
                  </button>
                </>
              ) : (
                <>
                  Already have an account?{" "}
                  <button
                    onClick={() => {
                      setMode("login");
                      resetForm();
                    }}
                    className="text-primary-600 hover:text-primary-700 font-medium"
                  >
                    Sign in
                  </button>
                </>
              )}
            </p>
          </div>
        </div>

        {/* Features */}
        <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-6 animate-fade-in">
          <div className="text-center">
            <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mx-auto mb-3">
              <BarChart3 className="w-6 h-6 text-primary-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-1">
              Real-time Monitoring
            </h3>
            <p className="text-sm text-gray-600">
              Track model performance continuously
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-secondary-100 rounded-xl flex items-center justify-center mx-auto mb-3">
              <AlertCircle className="w-6 h-6 text-secondary-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-1">Smart Alerts</h3>
            <p className="text-sm text-gray-600">
              Get notified of drift instantly
            </p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-success-100 rounded-xl flex items-center justify-center mx-auto mb-3">
              <CheckCircle className="w-6 h-6 text-success-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-1">
              Easy Integration
            </h3>
            <p className="text-sm text-gray-600">Simple API to get started</p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>© 2025 Cognitude AI. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}
