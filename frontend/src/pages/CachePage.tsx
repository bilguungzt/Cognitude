import { useState, useEffect } from "react";
import {
  Database,
  Trash2,
  TrendingUp,
  Zap,
  DollarSign,
  HardDrive,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import Layout from "../components/Layout";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import Modal from "../components/Modal";
import api from "../services";
import type { CacheStats } from "../types/api";

export default function CachePage() {
  const [cacheStats, setCacheStats] = useState<CacheStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [clearType, setClearType] = useState<"redis" | "postgresql" | "all">(
    "all"
  );
  const [clearing, setClearing] = useState(false);

  useEffect(() => {
    loadCacheStats();
  }, []);

  const loadCacheStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getCacheStats();
      setCacheStats(data);
    } catch (err) {
      setError(api.handleError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleClearCache = async () => {
    setClearing(true);
    try {
      await api.clearCache({ cache_type: clearType });
      await loadCacheStats();
      setIsConfirmModalOpen(false);
    } catch (err) {
      alert(api.handleError(err));
    } finally {
      setClearing(false);
    }
  };

  const openClearModal = (type: "redis" | "postgresql" | "all") => {
    setClearType(type);
    setIsConfirmModalOpen(true);
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

  if (error) {
    return (
      <Layout>
        <EmptyState
          icon={AlertTriangle}
          title="Failed to load cache statistics"
          description={error}
          action={{
            label: "Retry",
            onClick: loadCacheStats,
          }}
        />
      </Layout>
    );
  }

  if (!cacheStats) {
    return (
      <Layout>
        <EmptyState
          icon={Database}
          title="No cache data available"
          description="Cache statistics will appear once you start using the proxy"
        />
      </Layout>
    );
  }

  const cacheHitRate = cacheStats.redis.hit_rate * 100;

  return (
    <Layout title="Cache Management">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                Cache Management
              </h2>
              <p className="text-gray-600">
                Monitor cache performance and manage cached responses
              </p>
            </div>
            <button
              onClick={loadCacheStats}
              className="btn-secondary flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Hit Rate */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Hit Rate
                </p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {cacheHitRate.toFixed(1)}%
                </p>
              </div>
              <div className="p-3 bg-purple-100 rounded-full">
                <Zap className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <div className="mt-4">
              <p className="text-xs text-gray-500">Redis</p>
            </div>
          </div>

          {/* Total Cached */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Cached Responses
                </p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {cacheStats.postgresql.total_cached_responses.toLocaleString()}
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-full">
                <Database className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <div className="mt-4">
              <p className="text-xs text-gray-500">PostgreSQL</p>
            </div>
          </div>

          {/* Memory Usage */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Memory Usage
                </p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {cacheStats.redis.memory_usage_mb.toFixed(1)} MB
                </p>
              </div>
              <div className="p-3 bg-orange-100 rounded-full">
                <HardDrive className="w-6 h-6 text-orange-600" />
              </div>
            </div>
            <div className="mt-4">
              <p className="text-xs text-gray-500">Memory</p>
            </div>
          </div>

          {/* Cost Savings */}
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Total Saved
                </p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  ${cacheStats.lifetime_savings.total_cost_saved.toFixed(2)}
                </p>
              </div>
              <div className="p-3 bg-green-100 rounded-full">
                <DollarSign className="w-6 h-6 text-green-600" />
              </div>
            </div>
            <div className="mt-4">
              <p className="text-xs text-gray-500">Lifetime</p>
            </div>
          </div>
        </div>

        {/* Cache Details Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Redis Cache */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Redis Cache
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  Fast in-memory cache (1 hour TTL)
                </p>
              </div>
              <button
                onClick={() => openClearModal("redis")}
                className="btn-danger-outline flex items-center gap-2 text-sm"
              >
                <Trash2 className="w-4 h-4" />
                Clear
              </button>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <span className="text-gray-700">
                  Cache Hits
                </span>
                <span className="text-lg font-bold text-green-600">
                  {cacheStats.redis.hits.toLocaleString()}
                </span>
              </div>

              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <span className="text-gray-700">
                  Cache Misses
                </span>
                <span className="text-lg font-bold text-gray-900">
                  {cacheStats.redis.misses.toLocaleString()}
                </span>
              </div>

              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <span className="text-gray-700">
                  Total Keys
                </span>
                <span className="text-lg font-bold text-gray-900">
                  {cacheStats.redis.total_keys.toLocaleString()}
                </span>
              </div>

              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <span className="text-gray-700">
                  Hit Rate
                </span>
                <span className="text-lg font-bold text-purple-600">
                  {cacheHitRate.toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* PostgreSQL Cache */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  PostgreSQL Cache
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  Persistent long-term cache
                </p>
              </div>
              <button
                onClick={() => openClearModal("postgresql")}
                className="btn-danger-outline flex items-center gap-2 text-sm"
              >
                <Trash2 className="w-4 h-4" />
                Clear
              </button>
            </div>

            <div className="space-y-4">
              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <span className="text-gray-700">
                  Cached Responses
                </span>
                <span className="text-lg font-bold text-blue-600">
                  {cacheStats.postgresql.total_cached_responses.toLocaleString()}
                </span>
              </div>

              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <span className="text-gray-700">
                  Cost Savings
                </span>
                <span className="text-lg font-bold text-green-600">
                  ${cacheStats.postgresql.cost_savings.toFixed(2)}
                </span>
              </div>

              <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
                <span className="text-gray-700">
                  Oldest Entry
                </span>
                <span className="text-lg font-bold text-gray-900">
                  {new Date(
                    cacheStats.postgresql.oldest_cache_entry
                  ).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Lifetime Impact */}
        <div className="card bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 mb-8">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-green-600 rounded-lg">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Lifetime Cache Impact
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                <div>
                  <p className="text-sm text-gray-600">
                    Requests Served from Cache
                  </p>
                  <p className="text-3xl font-bold text-green-600 mt-1">
                    {cacheStats.lifetime_savings.requests_served_from_cache.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">
                    Total Cost Saved
                  </p>
                  <p className="text-3xl font-bold text-green-600 mt-1">
                    ${cacheStats.lifetime_savings.total_cost_saved.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Clear All Button */}
        <div className="card mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-red-900">
                Clear All Cache
              </h3>
              <p className="text-sm text-red-700 mt-1">
                Remove all cached responses from both Redis and PostgreSQL. This
                action cannot be undone.
              </p>
            </div>
            <button
              onClick={() => openClearModal("all")}
              className="btn-danger flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              Clear All Cache
            </button>
          </div>
        </div>

        {/* Info Card */}
        <div className="card">
          <h3 className="text-lg font-semibold text-blue-900 mb-6">
            How Caching Works
          </h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li className="flex items-start gap-2">
              <span className="text-blue-600">•</span>
              <span>
                <strong>Redis:</strong> Fast in-memory cache with 1 hour TTL for
                instant responses
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600">•</span>
              <span>
                <strong>PostgreSQL:</strong> Persistent storage for long-term
                analytics and cost tracking
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600">•</span>
              <span>
                Identical requests (same model + messages) return cached
                responses instantly
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600">•</span>
              <span>Cached responses cost $0 and have ~0ms latency</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Confirm Clear Modal */}
      <Modal
        isOpen={isConfirmModalOpen}
        onClose={() => setIsConfirmModalOpen(false)}
        title="Confirm Cache Clear"
      >
        <div className="space-y-4">
          <div className="alert-error">
            <AlertTriangle className="w-5 h-5" />
            <div>
              <p className="font-semibold">
                Are you sure you want to clear the{" "}
                {clearType === "all" ? "entire" : clearType} cache?
              </p>
              <p className="text-sm mt-1">
                This will remove all cached responses and cannot be undone.
                Future requests will need to contact the LLM providers directly
                until the cache rebuilds.
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-6 border-t border-gray-200">
            <button
              onClick={() => setIsConfirmModalOpen(false)}
              className="btn-outline"
              disabled={clearing}
            >
              Cancel
            </button>
            <button
              onClick={handleClearCache}
              className="btn-danger flex items-center gap-2"
              disabled={clearing}
            >
              {clearing ? (
                <>
                  <LoadingSpinner size="sm" />
                  Clearing...
                </>
              ) : (
                <>
                  <Trash2 className="w-4 h-4" />
                  Clear Cache
                </>
              )}
            </button>
          </div>
        </div>
      </Modal>
    </Layout>
  );
}
