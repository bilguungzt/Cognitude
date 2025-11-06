import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { useAuth } from "../contexts/AuthContext";
import { api } from "../services/api";
import type { MLModel, DriftStatus, DriftHistoryPoint } from "../types/api";

export default function ModelDriftPage() {
  const { modelId } = useParams<{ modelId: string }>();
  const [model, setModel] = useState<MLModel | null>(null);
  const [currentDrift, setCurrentDrift] = useState<DriftStatus | null>(null);
  const [driftHistory, setDriftHistory] = useState<DriftHistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  // Format timestamp for chart display
  const formatChartData = (data: DriftHistoryPoint[]) => {
    return data.map((point) => ({
      ...point,
      timestamp: new Date(point.timestamp).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      }),
    }));
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

      // Load drift history from API
      try {
        const history = await api.getDriftHistory(parseInt(modelId));
        setDriftHistory(history);
      } catch {
        // If no history exists, set empty array
        setDriftHistory([]);
      }

      setError("");
    } catch {
      setError("Failed to load model data");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="spinner h-12 w-12 border-indigo-600 mb-4"></div>
          <p className="text-gray-600 font-medium">Loading drift data...</p>
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

        {/* Current Drift Status */}
        <div className="card p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Current Drift Status
          </h2>

          {currentDrift?.message ? (
            <div className="text-center py-8">
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

        {/* Drift History Chart */}
        <div className="card p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">
            Drift Score Over Time
          </h2>

          {driftHistory.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600">
                No drift history available yet. Run drift detection to see
                results here.
              </p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={formatChartData(driftHistory)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="timestamp"
                  stroke="#6b7280"
                  style={{ fontSize: "12px" }}
                />
                <YAxis
                  stroke="#6b7280"
                  style={{ fontSize: "12px" }}
                  domain={[0, 1]}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "white",
                    border: "1px solid #e5e7eb",
                    borderRadius: "8px",
                    boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                  }}
                  formatter={(value: number) => value.toFixed(4)}
                />
                <Legend />
                <ReferenceLine
                  y={0.5}
                  stroke="#ef4444"
                  strokeDasharray="5 5"
                  label={{
                    value: "Drift Threshold",
                    position: "right",
                    fill: "#ef4444",
                    fontSize: 12,
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="drift_score"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={{ fill: "#6366f1", r: 4 }}
                  activeDot={{ r: 6 }}
                  name="Drift Score"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* P-Value Chart */}
        {driftHistory.length > 0 && (
          <div className="card p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">
              P-Value Over Time
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={formatChartData(driftHistory)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="timestamp"
                  stroke="#6b7280"
                  style={{ fontSize: "12px" }}
                />
                <YAxis
                  stroke="#6b7280"
                  style={{ fontSize: "12px" }}
                  domain={[0, 1]}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "white",
                    border: "1px solid #e5e7eb",
                    borderRadius: "8px",
                    boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                  }}
                  formatter={(value: number) => value.toFixed(4)}
                />
                <Legend />
                <ReferenceLine
                  y={0.05}
                  stroke="#ef4444"
                  strokeDasharray="5 5"
                  label={{
                    value: "Significance Level (α = 0.05)",
                    position: "right",
                    fill: "#ef4444",
                    fontSize: 12,
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="p_value"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={{ fill: "#10b981", r: 4 }}
                  activeDot={{ r: 6 }}
                  name="P-Value"
                />
              </LineChart>
            </ResponsiveContainer>
            <p className="text-xs text-gray-500 mt-4">
              Values below 0.05 indicate statistical significance (drift
              detected)
            </p>
          </div>
        )}

        {/* Drift History Table */}
        {driftHistory.length > 0 && (
          <div className="card p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Drift Detection History
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Drift Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      P-Value
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Samples
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {driftHistory.map((point, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(point.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {point.drift_detected ? (
                          <span className="badge-error">🔴 Drift</span>
                        ) : (
                          <span className="badge-success">🟢 OK</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {point.drift_score.toFixed(4)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {point.p_value.toFixed(4)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {point.samples}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Model Features */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Model Features
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {model.features.map((feature) => (
              <div
                key={feature.id}
                className="p-4 bg-gray-50 rounded-lg border border-gray-100"
              >
                <h3 className="font-semibold text-gray-900">
                  {feature.feature_name}
                </h3>
                <p className="text-sm text-gray-600 mt-1 capitalize">
                  {feature.feature_type}
                </p>
                {feature.baseline_stats && (
                  <span className="inline-block mt-2 badge-success text-xs">
                    Baseline Set
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
