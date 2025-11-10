import { useState, useEffect, useMemo } from "react";
import { api } from "../services";
import type { MLModel, DriftStatus } from "../types/api";
import { useNavigate } from "react-router-dom";
import Layout from "../components/Layout";
import Modal from "../components/Modal";
import RegisterModelModal from "../components/RegisterModelModal";
import EmptyState from "../components/EmptyState";
import LoadingSpinner from "../components/LoadingSpinner";
import { SkeletonCard } from "../components/Skeleton";
import {
  LayoutGrid,
  LayoutList,
  Search,
  Filter,
  RefreshCw,
  Package,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Activity,
  Clock,
} from "lucide-react";

type ViewMode = "grid" | "list";
type FilterMode = "all" | "drift" | "no-drift" | "not-configured";

export default function DashboardPageEnhanced() {
  const [models, setModels] = useState<MLModel[]>([]);
  const [driftStatuses, setDriftStatuses] = useState<
    Record<number, DriftStatus>
  >({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [lastChecked, setLastChecked] = useState<Date>(new Date());
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [searchQuery, setSearchQuery] = useState("");
  const [filterMode, setFilterMode] = useState<FilterMode>("all");
  const navigate = useNavigate();

  useEffect(() => {
    loadModels();
    // Poll for updates every 30 seconds
    const interval = setInterval(() => {
      loadModels(true);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const getRelativeTime = (date: Date): string => {
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 10) return "Just now";
    if (diffInSeconds < 60) return `${diffInSeconds}s ago`;

    const diffInMinutes = Math.floor(diffInSeconds / 60);
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;

    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;

    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays}d ago`;
  };

  const loadModels = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setLastChecked(new Date());
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
      setRefreshing(false);
    }
  };

  // Filtered and searched models
  const filteredModels = useMemo(() => {
    let filtered = models;

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (model) =>
          model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          model.version.toLowerCase().includes(searchQuery.toLowerCase()) ||
          model.description?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply drift filter
    if (filterMode !== "all") {
      filtered = filtered.filter((model) => {
        const status = driftStatuses[model.id];
        if (filterMode === "drift") return status?.drift_detected;
        if (filterMode === "no-drift")
          return status && !status.drift_detected && !status.message;
        if (filterMode === "not-configured") return status?.message;
        return true;
      });
    }

    return filtered;
  }, [models, driftStatuses, searchQuery, filterMode]);

  // Stats
  const stats = useMemo(() => {
    const total = models.length;
    const withDrift = Object.values(driftStatuses).filter(
      (s) => s?.drift_detected
    ).length;
    const noDrift = Object.values(driftStatuses).filter(
      (s) => s && !s.drift_detected && !s.message
    ).length;
    const notConfigured = Object.values(driftStatuses).filter(
      (s) => s?.message
    ).length;

    return { total, withDrift, noDrift, notConfigured };
  }, [models, driftStatuses]);

  const getDriftBadge = (status: DriftStatus | undefined) => {
    if (!status) {
      return <span className="badge-neutral">Loading...</span>;
    }

    if (status.message) {
      return (
        <span className="badge-neutral flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {status.message}
        </span>
      );
    }

    if (status.drift_detected) {
      return (
        <span className="badge-error flex items-center gap-1">
          <AlertTriangle className="w-3 h-3" />
          Drift Detected
        </span>
      );
    }

    return (
      <span className="badge-success flex items-center gap-1">
        <CheckCircle className="w-3 h-3" />
        No Drift
      </span>
    );
  };

  const getDriftDetails = (status: DriftStatus | undefined) => {
    if (!status || status.message) return null;

    return (
      <div className="flex items-center gap-3 text-sm text-gray-600 mt-2">
        {status.drift_score !== undefined && (
          <span>
            Score:{" "}
            <strong className="text-gray-900">
              {status.drift_score.toFixed(3)}
            </strong>
          </span>
        )}
        {status.p_value !== undefined && (
          <span>
            p-value:{" "}
            <strong className="text-gray-900">
              {status.p_value.toFixed(4)}
            </strong>
          </span>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <Layout title="Dashboard">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <div className="h-8 w-48 skeleton mb-2" />
            <div className="h-5 w-64 skeleton" />
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Monitor Your ML Models">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Your ML Models
          </h2>
          <p className="text-gray-600">
            Monitor drift and performance across all registered models
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <div className="card hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center">
                <Package className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Total Models</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats.total}
                </p>
              </div>
            </div>
          </div>

          <div className="card hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-danger-100 rounded-xl flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-danger-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">With Drift</p>
                <p className="text-2xl font-bold text-danger-600">
                  {stats.withDrift}
                </p>
              </div>
            </div>
          </div>

          <div className="card hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-success-100 rounded-xl flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-success-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">No Drift</p>
                <p className="text-2xl font-bold text-success-600">
                  {stats.noDrift}
                </p>
              </div>
            </div>
          </div>

          <div className="card hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center">
                <Activity className="w-6 h-6 text-gray-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Not Configured</p>
                <p className="text-2xl font-bold text-gray-600">
                  {stats.notConfigured}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Action Bar */}
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 mb-6">
          {/* Search and Filter */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 flex-1 w-full lg:w-auto">
            {/* Search */}
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search models..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input pl-10"
              />
            </div>

            {/* Filter */}
            <select
              value={filterMode}
              onChange={(e) => setFilterMode(e.target.value as FilterMode)}
              className="select w-full sm:w-auto"
            >
              <option value="all">All Models</option>
              <option value="drift">With Drift</option>
              <option value="no-drift">No Drift</option>
              <option value="not-configured">Not Configured</option>
            </select>
          </div>

          {/* View Controls and Actions */}
          <div className="flex items-center gap-2 w-full lg:w-auto">
            {/* View Mode Toggle */}
            <div className="flex items-center gap-1 p-1 bg-gray-100 rounded-lg">
              <button
                onClick={() => setViewMode("grid")}
                className={`p-2 rounded transition-colors ${
                  viewMode === "grid"
                    ? "bg-white text-primary-600 shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                <LayoutGrid className="w-5 h-5" />
              </button>
              <button
                onClick={() => setViewMode("list")}
                className={`p-2 rounded transition-colors ${
                  viewMode === "list"
                    ? "bg-white text-primary-600 shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                <LayoutList className="w-5 h-5" />
              </button>
            </div>

            {/* Refresh Button */}
            <button
              onClick={() => loadModels(true)}
              disabled={refreshing}
              className="btn-outline p-2.5"
              title="Refresh models"
            >
              <RefreshCw
                className={`w-5 h-5 ${refreshing ? "animate-spin" : ""}`}
              />
            </button>

            {/* Register Model Button */}
            <button
              onClick={() => setShowRegisterModal(true)}
              className="btn-primary whitespace-nowrap"
            >
              <span className="hidden sm:inline">Register Model</span>
              <span className="sm:hidden">Register</span>
            </button>
          </div>
        </div>

        {/* Last Updated */}
        <div className="flex items-center justify-between mb-6 text-sm text-gray-600">
          <span>
            Last updated: <strong>{getRelativeTime(lastChecked)}</strong>
          </span>
          {filteredModels.length !== models.length && (
            <span>
              Showing <strong>{filteredModels.length}</strong> of{" "}
              <strong>{models.length}</strong> models
            </span>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="alert-error mb-6">
            <AlertTriangle className="w-5 h-5" />
            <p>{error}</p>
          </div>
        )}

        {/* Models Display */}
        {filteredModels.length === 0 ? (
          models.length === 0 ? (
            <EmptyState
              icon={Package}
              title="No models yet"
              description="Get started by registering your first ML model and start monitoring for drift"
              action={{
                label: "Register Your First Model",
                onClick: () => setShowRegisterModal(true),
              }}
            />
          ) : (
            <EmptyState
              icon={Search}
              title="No models found"
              description="Try adjusting your search or filter criteria"
            />
          )
        ) : (
          <div
            className={
              viewMode === "grid"
                ? "grid gap-6 md:grid-cols-2 lg:grid-cols-3"
                : "flex flex-col gap-4"
            }
          >
            {filteredModels.map((model) => (
              <div
                key={model.id}
                className={`card-interactive ${
                  viewMode === "list" ? "hover:border-primary-200" : ""
                }`}
                onClick={() => navigate(`/models/${model.id}`)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-gray-900 mb-1">
                      {model.name}
                    </h3>
                    <p className="text-sm text-gray-600">
                      Version {model.version}
                    </p>
                  </div>
                  {getDriftBadge(driftStatuses[model.id])}
                </div>

                {model.description && (
                  <p className="text-sm text-gray-600 mb-4">
                    {model.description}
                  </p>
                )}

                {getDriftDetails(driftStatuses[model.id])}

                <div className="divider" />

                <div className="grid grid-cols-2 gap-4 mb-4">
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
                      Status
                    </p>
                    <p className="font-semibold text-success-600 mt-1">
                      Active
                    </p>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/models/${model.id}`);
                    }}
                    className="btn-primary flex-1 btn-sm"
                  >
                    View Details
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/models/${model.id}/drift`);
                    }}
                    className="btn-ghost flex-1 btn-sm"
                  >
                    <TrendingUp className="w-4 h-4" />
                    Drift History
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Register Model Modal */}
      <RegisterModelModal
        isOpen={showRegisterModal}
        onClose={() => setShowRegisterModal(false)}
        onSuccess={() => {
          loadModels();
          setShowRegisterModal(false);
        }}
      />
    </Layout>
  );
}
