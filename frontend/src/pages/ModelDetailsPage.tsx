import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { api } from "../services";
import type { MLModel, DriftStatus } from "../types/api";

export default function ModelDetailsPage() {
  const { modelId } = useParams<{ modelId: string }>();
  const [model, setModel] = useState<MLModel | null>(null);
  const [currentDrift, setCurrentDrift] = useState<DriftStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [checkingDrift, setCheckingDrift] = useState(false);

  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  useEffect(() => {
    loadModelData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [modelId]);

  const loadModelData = async () => {
    if (!modelId) return;

    try {
      // Load model details
      const modelData = await api.getModel(parseInt(modelId));
      setModel(modelData);

      // Load current drift status
      try {
        const drift = await api.getCurrentDrift(parseInt(modelId));
        setCurrentDrift(drift);
      } catch {
        setCurrentDrift({
          drift_detected: false,
          message: "Baseline not configured",
        });
      }

      setError("");
    } catch {
      setError("Failed to load model data");
    } finally {
      setLoading(false);
    }
  };

  const handleCheckDrift = async () => {
    if (!modelId) return;

    setCheckingDrift(true);
    try {
      const drift = await api.getCurrentDrift(parseInt(modelId));
      setCurrentDrift(drift);
    } catch {
      setError("Failed to check drift");
    } finally {
      setCheckingDrift(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="spinner h-12 w-12 border-indigo-600 mb-4"></div>
          <p className="text-gray-600 font-medium">Loading model details...</p>
        </div>
      </div>
    );
  }

  if (!model) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600">Model not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="glass border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate("/dashboard")}
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {model.name}
                </h1>
                <p className="text-gray-600 text-sm">Version {model.version}</p>
              </div>
            </div>
            <button onClick={handleLogout} className="btn-secondary">
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Message */}
        {error && (
          <div className="alert-error mb-6">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Model Info Card */}
        <div className="card p-6 mb-6">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Model Information
              </h2>
              <p className="text-gray-600">
                {model.description || "No description provided"}
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleCheckDrift}
                disabled={checkingDrift}
                className="btn-primary"
              >
                {checkingDrift ? (
                  <>
                    <span className="spinner h-4 w-4 border-white mr-2"></span>
                    Checking...
                  </>
                ) : (
                  "Check Drift Now"
                )}
              </button>
              <button
                onClick={() => navigate(`/models/${modelId}/drift`)}
                className="btn-ghost"
              >
                View Drift History
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Model ID
              </p>
              <p className="text-xl font-bold text-gray-900">#{model.id}</p>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Features
              </p>
              <p className="text-xl font-bold text-gray-900">
                {model.features.length}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Created
              </p>
              <p className="text-xl font-bold text-gray-900">
                {new Date(model.created_at).toLocaleDateString()}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                Last Updated
              </p>
              <p className="text-xl font-bold text-gray-900">
                {new Date(model.updated_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        {/* Current Drift Status */}
        <div className="card p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Current Drift Status
          </h2>

          {currentDrift?.message ? (
            <div className="text-center py-8 bg-gray-50 rounded-lg">
              <svg
                className="w-12 h-12 text-gray-400 mx-auto mb-3"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p className="text-gray-600">{currentDrift.message}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                  Status
                </p>
                {currentDrift?.drift_detected ? (
                  <span className="badge-error">⚠️ Drift Detected</span>
                ) : (
                  <span className="badge-success">✓ No Drift</span>
                )}
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                  Drift Score
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {currentDrift?.drift_score?.toFixed(3) || "N/A"}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                  P-Value
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {currentDrift?.p_value?.toFixed(4) || "N/A"}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                  Samples
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {currentDrift?.samples || "N/A"}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Features List */}
        <div className="card p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Model Features
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {model.features.map((feature) => (
              <div
                key={feature.id}
                className="p-4 bg-gradient-to-br from-gray-50 to-white rounded-lg border border-gray-200 hover:border-indigo-200 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">
                    {feature.feature_name}
                  </h3>
                  <span className="text-xs px-2 py-1 bg-indigo-50 text-indigo-700 rounded-full capitalize">
                    {feature.feature_type}
                  </span>
                </div>
                <p className="text-sm text-gray-600">Order: {feature.order}</p>
                {feature.baseline_stats ? (
                  <div className="mt-3">
                    <span className="badge-success text-xs">
                      Baseline Configured
                    </span>
                    {feature.baseline_stats.mean !== undefined && (
                      <div className="mt-2 text-xs text-gray-600">
                        <p>Mean: {feature.baseline_stats.mean.toFixed(2)}</p>
                        {feature.baseline_stats.std !== undefined && (
                          <p>Std: {feature.baseline_stats.std.toFixed(2)}</p>
                        )}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="mt-3">
                    <span className="text-xs px-2 py-1 bg-yellow-50 text-yellow-700 rounded-full">
                      No Baseline
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Quick Actions
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => navigate(`/models/${modelId}/drift`)}
              className="p-4 text-left border-2 border-gray-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition-all group"
            >
              <svg
                className="w-8 h-8 text-indigo-600 mb-2"
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
              <h3 className="font-semibold text-gray-900 group-hover:text-indigo-600">
                View Drift History
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                See historical drift trends and charts
              </p>
            </button>

            <button
              onClick={handleCheckDrift}
              disabled={checkingDrift}
              className="p-4 text-left border-2 border-gray-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition-all group disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg
                className="w-8 h-8 text-green-600 mb-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                />
              </svg>
              <h3 className="font-semibold text-gray-900 group-hover:text-green-600">
                Check Drift Now
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Run drift detection immediately
              </p>
            </button>

            <button
              onClick={() => navigate("/dashboard")}
              className="p-4 text-left border-2 border-gray-200 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-all group"
            >
              <svg
                className="w-8 h-8 text-purple-600 mb-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                />
              </svg>
              <h3 className="font-semibold text-gray-900 group-hover:text-purple-600">
                Back to Dashboard
              </h3>
              <p className="text-sm text-gray-600 mt-1">View all your models</p>
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
