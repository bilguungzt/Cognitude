import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { api } from "../services/api";

export default function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [apiKey, setApiKey] = useState("");
  const [orgName, setOrgName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showKey, setShowKey] = useState(false);

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
      // Test the API key by making a health check
      api.setApiKey(apiKey.trim());
      await api.getModels();

      // If successful, log in and navigate
      login(apiKey.trim());
      navigate("/dashboard");
    } catch (err) {
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

    setLoading(true);
    setError("");

    try {
      const org = await api.register(orgName.trim());

      if (org.api_key) {
        // Show the API key to the user
        setApiKey(org.api_key);
        setMode("login");
        setShowKey(true);
        setError(""); // Clear any previous errors
      }
    } catch (err: any) {
      if (err.response?.status === 409) {
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 gradient-primary rounded-2xl mb-4 shadow-lg">
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
            DriftAssure AI
          </h1>
          <p className="text-gray-600 mt-2 text-lg">
            ML Model Drift Detection & Monitoring
          </p>
        </div>

        {/* Card */}
        <div className="glass rounded-2xl shadow-soft p-8 border border-white/50">
          {/* Mode Toggle */}
          <div className="flex gap-2 mb-6 p-1.5 bg-gray-50/80 rounded-xl border border-gray-100">
            <button
              onClick={() => setMode("login")}
              className={`flex-1 py-2.5 px-4 rounded-lg font-medium transition-all ${
                mode === "login"
                  ? "bg-white text-indigo-600 shadow-sm border border-gray-100"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setMode("register")}
              className={`flex-1 py-2.5 px-4 rounded-lg font-medium transition-all ${
                mode === "register"
                  ? "bg-white text-indigo-600 shadow-sm border border-gray-100"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Register
            </button>
          </div>

          {/* Success Message for API Key */}
          {showKey && mode === "login" && apiKey && (
            <div className="alert-success mb-6">
              <div className="flex items-start gap-3">
                <svg
                  className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <div className="flex-1">
                  <h3 className="text-sm font-semibold">
                    Registration successful!
                  </h3>
                  <p className="text-sm mt-1 mb-3">
                    Your API key has been generated. Please save it securely -
                    you won't see it again!
                  </p>
                  <div className="bg-white rounded-lg p-3 border border-green-200">
                    <code className="text-xs font-mono text-gray-900 break-all">
                      {apiKey}
                    </code>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      navigator.clipboard.writeText(apiKey);
                      alert("API key copied to clipboard!");
                    }}
                    className="mt-3 text-sm font-medium text-green-700 hover:text-green-800 underline"
                  >
                    Copy to Clipboard
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Error Message */}
          {/* Error Message */}
          {error && (
            <div className="alert-error mb-6">
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Forms */}
          {mode === "login" ? (
            <form onSubmit={handleLogin}>
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  API Key
                </label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter your API key"
                  className="input"
                  disabled={loading}
                />
                <p className="mt-2 text-sm text-gray-500">
                  Don't have an API key? Switch to Register tab.
                </p>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full btn-primary py-3 text-base shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Logging in..." : "Login"}
              </button>
            </form>
          ) : (
            <form onSubmit={handleRegister}>
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Organization Name
                </label>
                <input
                  type="text"
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  placeholder="e.g., Acme Corp"
                  className="input"
                  disabled={loading}
                />
                <p className="mt-2 text-sm text-gray-500">
                  Choose a unique name for your organization
                </p>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full btn-primary py-3 text-base shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "Creating account..." : "Create Account"}
              </button>
            </form>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-gray-600 mt-6">
          Need help? Check out the{" "}
          <a
            href="https://api.driftassure.com/redoc"
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-600 hover:text-indigo-700 font-medium"
          >
            API Documentation
          </a>
        </p>
      </div>
    </div>
  );
}
