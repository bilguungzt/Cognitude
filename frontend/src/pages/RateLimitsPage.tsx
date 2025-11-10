import { useState, useEffect } from "react";
import {
  Shield,
  Save,
  Activity,
  Clock,
  Calendar,
  AlertTriangle,
  TrendingUp,
  CheckCircle,
} from "lucide-react";
import Layout from "../components/Layout";
import LoadingSpinner from "../components/LoadingSpinner";
import api from "../services";
import type { RateLimitConfig } from "../types/api";

export default function RateLimitsPage() {
  const [config, setConfig] = useState<RateLimitConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState<Partial<RateLimitConfig>>({
    enabled: true,
    requests_per_minute: 60,
    requests_per_hour: 1000,
    requests_per_day: 10000,
  });

  // Simulated current usage (in production, this would come from an API)
  const [currentUsage] = useState({
    minute: 45,
    hour: 750,
    day: 7500,
  });

  useEffect(() => {
    loadRateLimits();
  }, []);

  const loadRateLimits = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getRateLimitConfig();
      setConfig(data);
      setFormData(data);
    } catch (err) {
      setError(api.handleError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      await api.updateRateLimitConfig(formData as RateLimitConfig);
      await loadRateLimits();

      setSuccessMessage("Rate limit configuration updated successfully!");
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(api.handleError(err));
    } finally {
      setSaving(false);
    }
  };

  const calculatePercentage = (current: number, limit: number): number => {
    return limit > 0 ? (current / limit) * 100 : 0;
  };

  const getProgressColor = (percentage: number): string => {
    if (percentage >= 90) return "bg-red-600";
    if (percentage >= 75) return "bg-yellow-600";
    return "bg-green-600";
  };

  const getStatusColor = (percentage: number): string => {
    if (percentage >= 90) return "text-red-600 dark:text-red-400";
    if (percentage >= 75) return "text-yellow-600 dark:text-yellow-400";
    return "text-green-600 dark:text-green-400";
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  const minutePercentage = calculatePercentage(
    currentUsage.minute,
    formData.requests_per_minute || 0
  );
  const hourPercentage = calculatePercentage(
    currentUsage.hour,
    formData.requests_per_hour || 0
  );
  const dayPercentage = calculatePercentage(
    currentUsage.day,
    formData.requests_per_day || 0
  );

  return (
    <Layout title="Rate Limits">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Rate Limits
          </h2>
          <p className="text-gray-600">
            Configure API rate limits to protect your infrastructure and control
            costs
          </p>
        </div>

        {/* Success Message */}
        {successMessage && (
          <div className="alert-success mb-6">
            <CheckCircle className="w-5 h-5" />
            <p>{successMessage}</p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="alert-error mb-6">
            <AlertTriangle className="w-5 h-5" />
            <p>{error}</p>
          </div>
        )}

        {/* Status Card */}
        {config && (
          <div className="card mb-8">
            <div className="flex items-center gap-3">
              <div
                className={`p-3 rounded-lg ${
                  config.enabled ? "bg-green-600" : "bg-gray-400"
                }`}
              >
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Rate Limiting {config.enabled ? "Enabled" : "Disabled"}
                </h3>
                <p className="text-sm text-gray-600">
                  {config.enabled
                    ? "Your API is protected by rate limits"
                    : "Rate limiting is currently disabled"}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Current Usage */}
        <div className="card mb-8">
          <div className="flex items-center gap-2 mb-6">
            <Activity className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">
              Current Usage
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Per Minute */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gray-500" />
                  <span className="text-sm font-medium text-gray-700">
                    Per Minute
                  </span>
                </div>
                <span
                  className={`text-sm font-bold ${getStatusColor(
                    minutePercentage
                  )}`}
                >
                  {minutePercentage.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all duration-500 ${getProgressColor(
                    minutePercentage
                  )}`}
                  style={{ width: `${Math.min(minutePercentage, 100)}%` }}
                />
              </div>
              <p className="text-sm text-gray-600">
                {currentUsage.minute.toLocaleString()} /{" "}
                {formData.requests_per_minute?.toLocaleString() || 0} requests
              </p>
            </div>

            {/* Per Hour */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-gray-500" />
                  <span className="text-sm font-medium text-gray-700">
                    Per Hour
                  </span>
                </div>
                <span
                  className={`text-sm font-bold ${getStatusColor(
                    hourPercentage
                  )}`}
                >
                  {hourPercentage.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all duration-500 ${getProgressColor(
                    hourPercentage
                  )}`}
                  style={{ width: `${Math.min(hourPercentage, 100)}%` }}
                />
              </div>
              <p className="text-sm text-gray-600">
                {currentUsage.hour.toLocaleString()} /{" "}
                {formData.requests_per_hour?.toLocaleString() || 0} requests
              </p>
            </div>

            {/* Per Day */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gray-500" />
                  <span className="text-sm font-medium text-gray-700">
                    Per Day
                  </span>
                </div>
                <span
                  className={`text-sm font-bold ${getStatusColor(
                    dayPercentage
                  )}`}
                >
                  {dayPercentage.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all duration-500 ${getProgressColor(
                    dayPercentage
                  )}`}
                  style={{ width: `${Math.min(dayPercentage, 100)}%` }}
                />
              </div>
              <p className="text-sm text-gray-600">
                {currentUsage.day.toLocaleString()} /{" "}
                {formData.requests_per_day?.toLocaleString() || 0} requests
              </p>
            </div>
          </div>

          {/* Warning if approaching limits */}
          {(minutePercentage >= 75 ||
            hourPercentage >= 75 ||
            dayPercentage >= 75) && (
            <div className="alert-warning mt-6">
              <AlertTriangle className="w-5 h-5" />
              <div>
                <h4 className="font-semibold">Approaching Rate Limit</h4>
                <p className="text-sm mt-1">
                  You are approaching one or more rate limits. Consider
                  increasing the limits or optimizing your API usage.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Configuration Form */}
        <div className="card mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">
            Rate Limit Configuration
          </h3>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Enable/Disable */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Enable Rate Limiting
                </label>
                <p className="text-xs text-gray-500 mt-1">
                  Turn on/off API rate limiting for your organization
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.enabled}
                  onChange={(e) =>
                    setFormData({ ...formData, enabled: e.target.checked })
                  }
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            {/* Requests Per Minute */}
            <div>
              <label className="label">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  Requests Per Minute
                </div>
              </label>
              <input
                type="number"
                min="1"
                value={formData.requests_per_minute || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    requests_per_minute: parseInt(e.target.value) || 0,
                  })
                }
                placeholder="60"
                className="input"
                disabled={!formData.enabled}
              />
              <p className="text-sm text-gray-500 mt-1">
                Maximum requests allowed per minute
              </p>
            </div>

            {/* Requests Per Hour */}
            <div>
              <label className="label">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Requests Per Hour
                </div>
              </label>
              <input
                type="number"
                min="1"
                value={formData.requests_per_hour || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    requests_per_hour: parseInt(e.target.value) || 0,
                  })
                }
                placeholder="1000"
                className="input"
                disabled={!formData.enabled}
              />
              <p className="text-sm text-gray-500 mt-1">
                Maximum requests allowed per hour
              </p>
            </div>

            {/* Requests Per Day */}
            <div>
              <label className="label">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  Requests Per Day
                </div>
              </label>
              <input
                type="number"
                min="1"
                value={formData.requests_per_day || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    requests_per_day: parseInt(e.target.value) || 0,
                  })
                }
                placeholder="10000"
                className="input"
                disabled={!formData.enabled}
              />
              <p className="text-sm text-gray-500 mt-1">
                Maximum requests allowed per day
              </p>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-3 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={() => {
                  if (config) {
                    setFormData(config);
                  }
                }}
                className="btn-outline"
                disabled={saving}
              >
                Reset
              </button>
              <button
                type="submit"
                className="btn-primary flex items-center gap-2"
                disabled={saving}
              >
                {saving ? (
                  <>
                    <LoadingSpinner size="sm" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    Save Configuration
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Info Card */}
        <div className="card mb-8">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">
            How Rate Limiting Works
          </h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li className="flex items-start gap-2">
              <span className="text-blue-600">•</span>
              <span>
                <strong>Organization-level:</strong> Limits apply per
                organization, not per user
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600">•</span>
              <span>
                <strong>Sliding window:</strong> Limits reset on a rolling basis
                (not at fixed intervals)
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600">•</span>
              <span>
                <strong>429 responses:</strong> Requests exceeding limits
                receive HTTP 429 (Too Many Requests)
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600">•</span>
              <span>
                <strong>Headers:</strong> Rate limit info is included in
                response headers (X-RateLimit-*)
              </span>
            </li>
          </ul>
        </div>

        {/* Recommended Limits Card */}
        <div className="card">
          <h3 className="text-lg font-semibold text-purple-900 mb-6">
            Recommended Starting Points
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-purple-700 font-medium mb-1">
                Small Team
              </p>
              <p className="text-xs text-purple-600">
                60/min • 1,000/hr • 10,000/day
              </p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-purple-700 font-medium mb-1">
                Medium Team
              </p>
              <p className="text-xs text-purple-600">
                300/min • 10,000/hr • 100,000/day
              </p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-purple-700 font-medium mb-1">
                Enterprise
              </p>
              <p className="text-xs text-purple-600">
                1,000/min • 50,000/hr • 500,000/day
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
