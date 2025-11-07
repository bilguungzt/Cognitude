import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { api } from "../services/api";
import type { MLModel, DriftStatus } from "../types/api";
import { useNavigate } from "react-router-dom";
import RegisterModelModal from "../components/RegisterModelModal";

export default function DashboardPage() {
  const [models, setModels] = useState<MLModel[]>([]);
  const [driftStatuses, setDriftStatuses] = useState<
    Record<number, DriftStatus>
  >({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadModels();
    // Poll for updates every 30 seconds
    const interval = setInterval(loadModels, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadModels = async () => {
    try {
      const data = await api.getModels();
      setModels(data);

      // Load drift status for each model
      const statuses: Record<number, DriftStatus> = {};
      await Promise.all(
        data.map(async (model) => {
          try {
            const drift = await api.getCurrentDrift(model.id);
            statuses[model.id] = drift;
          } catch (err) {
            // Model may not have baseline set yet
            statuses[model.id] = {
              drift_detected: false,
              message: "Baseline not configured",
            };
          }
        })
      );
      setDriftStatuses(statuses);
      setError("");
    } catch (err) {
      setError("Failed to load models");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const getDriftBadge = (status: DriftStatus | undefined) => {
    if (!status) {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
          Loading...
        </span>
      );
    }

    if (status.message) {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
          {status.message}
        </span>
      );
    }

    if (status.drift_detected) {
      return (
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">
            ⚠️ Drift Detected
          </span>
          <span className="text-sm text-gray-600">
            Score: {status.drift_score?.toFixed(3)} | p-value:{" "}
            {status.p_value?.toFixed(4)}
          </span>
        </div>
      );
    }

    return (
      <div className="flex items-center gap-2">
        <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
          ✓ No Drift
        </span>
        <span className="text-sm text-gray-600">
          Score: {status.drift_score?.toFixed(3)}
        </span>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="spinner h-12 w-12 border-indigo-600 mb-4"></div>
          <p className="text-gray-600 font-medium">Loading your models...</p>
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
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 gradient-primary rounded-xl flex items-center justify-center shadow-md">
                <svg
                  className="w-6 h-6 text-white"
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
              <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                DriftAssure AI
              </h1>
            </div>
            <div className="flex items-center gap-3">
              <button onClick={() => navigate("/setup")} className="btn-ghost">
                📖 Setup Guide
              </button>
              <button onClick={() => navigate("/alerts")} className="btn-ghost">
                Alert Settings
              </button>
              <button onClick={handleLogout} className="btn-secondary">
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Action Bar */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-gray-900">Your ML Models</h2>
            <p className="text-gray-600 mt-2">
              Monitor drift and performance across all registered models
            </p>
          </div>
          <button
            onClick={() => setShowRegisterModal(true)}
            className="btn-primary px-6 py-3 shadow-md hover:shadow-lg flex items-center gap-2"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            Register New Model
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="alert-error mb-6">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Models Grid */}
        {models.length === 0 ? (
          <div className="card p-12 text-center">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-indigo-50 to-purple-50 rounded-2xl mb-6">
              <svg
                className="w-10 h-10 text-indigo-500"
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
            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              No models yet
            </h3>
            <p className="text-gray-600 text-lg mb-8 max-w-md mx-auto">
              Get started by registering your first ML model and start
              monitoring for drift
            </p>
            <button
              onClick={() => setShowRegisterModal(true)}
              className="btn-primary px-6 py-3 shadow-md hover:shadow-lg inline-flex items-center gap-2"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              Register Your First Model
            </button>
          </div>
        ) : (
          <div className="grid gap-6">
            {models.map((model) => (
              <div key={model.id} className="card-hover">
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">
                        {model.name}
                      </h3>
                      <p className="text-gray-600 mt-1.5">
                        Version {model.version}
                        {model.description && ` • ${model.description}`}
                      </p>
                    </div>
                    {getDriftBadge(driftStatuses[model.id])}
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Model ID
                      </p>
                      <p className="font-semibold text-gray-900 mt-1">
                        #{model.id}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Features
                      </p>
                      <p className="font-semibold text-gray-900 mt-1">
                        {model.features.length}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Created
                      </p>
                      <p className="font-semibold text-gray-900 mt-1">
                        {new Date(model.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Last Checked
                      </p>
                      <p className="font-semibold text-gray-900 mt-1">
                        Recently
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={() => navigate(`/models/${model.id}`)}
                      className="btn-primary px-5 py-2.5"
                    >
                      View Details
                    </button>
                    <button
                      onClick={() => navigate(`/models/${model.id}/drift`)}
                      className="btn-ghost px-5 py-2.5"
                    >
                      Drift History
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Register Model Modal */}
      <RegisterModelModal
        isOpen={showRegisterModal}
        onClose={() => setShowRegisterModal(false)}
        onSuccess={() => loadModels()}
      />
    </div>
  );
}
