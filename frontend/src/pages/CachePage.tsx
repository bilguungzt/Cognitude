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
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Cache Management
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
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

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Hit Rate */}
          <div className="card group hover:shadow-lg transition-all duration-200">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg group-hover:scale-110 transition-transform">
                <Zap className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Redis
              </span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
              {cacheHitRate.toFixed(1)}%
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Hit Rate
            </p>
            <div className="mt-3 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-purple-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${cacheHitRate}%` }}
              />
            </div>
          </div>

          {/* Total Cached */}
          <div className="card group hover:shadow-lg transition-all duration-200">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg group-hover:scale-110 transition-transform">
                <Database className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                PostgreSQL
              </span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
              {cacheStats.postgresql.total_cached_responses.toLocaleString()}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Cached Responses
            </p>
          </div>

          {/* Memory Usage */}
          <div className="card group hover:shadow-lg transition-all duration-200">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg group-hover:scale-110 transition-transform">
                <HardDrive className="w-6 h-6 text-orange-600 dark:text-orange-400" />
              </div>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Memory
              </span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
              {cacheStats.redis.memory_usage_mb.toFixed(1)} MB
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Redis Usage
            </p>
          </div>

          {/* Cost Savings */}
          <div className="card group hover:shadow-lg transition-all duration-200">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg group-hover:scale-110 transition-transform">
                <DollarSign className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Lifetime
              </span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
              ${cacheStats.lifetime_savings.total_cost_saved.toFixed(2)}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Total Saved
            </p>
          </div>
        </div>

        {/* Cache Details Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Redis Cache */}
          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  Redis Cache
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
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
              <div className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-gray-700 dark:text-gray-300">
                  Cache Hits
                </span>
                <span className="text-lg font-bold text-green-600 dark:text-green-400">
                  {cacheStats.redis.hits.toLocaleString()}
                </span>
              </div>

              <div className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-gray-700 dark:text-gray-300">
                  Cache Misses
                </span>
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {cacheStats.redis.misses.toLocaleString()}
                </span>
              </div>

              <div className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-gray-700 dark:text-gray-300">
                  Total Keys
                </span>
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {cacheStats.redis.total_keys.toLocaleString()}
                </span>
              </div>

              <div className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-gray-700 dark:text-gray-300">
                  Hit Rate
                </span>
                <span className="text-lg font-bold text-purple-600 dark:text-purple-400">
                  {cacheHitRate.toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* PostgreSQL Cache */}
          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  PostgreSQL Cache
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
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
              <div className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-gray-700 dark:text-gray-300">
                  Cached Responses
                </span>
                <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
                  {cacheStats.postgresql.total_cached_responses.toLocaleString()}
                </span>
              </div>

              <div className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-gray-700 dark:text-gray-300">
                  Cost Savings
                </span>
                <span className="text-lg font-bold text-green-600 dark:text-green-400">
                  ${cacheStats.postgresql.cost_savings.toFixed(2)}
                </span>
              </div>

              <div className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <span className="text-gray-700 dark:text-gray-300">
                  Oldest Entry
                </span>
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {new Date(
                    cacheStats.postgresql.oldest_cache_entry
                  ).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Lifetime Impact */}
        <div className="card bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-2 border-green-200 dark:border-green-800">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-green-600 rounded-lg">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Lifetime Cache Impact
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Requests Served from Cache
                  </p>
                  <p className="text-3xl font-bold text-green-600 dark:text-green-400 mt-1">
                    {cacheStats.lifetime_savings.requests_served_from_cache.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Total Cost Saved
                  </p>
                  <p className="text-3xl font-bold text-green-600 dark:text-green-400 mt-1">
                    ${cacheStats.lifetime_savings.total_cost_saved.toFixed(2)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Clear All Button */}
        <div className="card bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-red-900 dark:text-red-300">
                Clear All Cache
              </h3>
              <p className="text-sm text-red-700 dark:text-red-400 mt-1">
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
        <div className="card bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-300 mb-2">
            How Caching Works
          </h3>
          <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-300">
            <li className="flex items-start gap-2">
              <span className="text-blue-600 dark:text-blue-400">•</span>
              <span>
                <strong>Redis:</strong> Fast in-memory cache with 1 hour TTL for
                instant responses
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 dark:text-blue-400">•</span>
              <span>
                <strong>PostgreSQL:</strong> Persistent storage for long-term
                analytics and cost tracking
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 dark:text-blue-400">•</span>
              <span>
                Identical requests (same model + messages) return cached
                responses instantly
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 dark:text-blue-400">•</span>
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
          <div className="flex items-start gap-3 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5" />
            <div>
              <p className="font-semibold text-red-900 dark:text-red-300">
                Are you sure you want to clear the{" "}
                {clearType === "all" ? "entire" : clearType} cache?
              </p>
              <p className="text-sm text-red-700 dark:text-red-400 mt-1">
                This will remove all cached responses and cannot be undone.
                Future requests will need to contact the LLM providers directly
                until the cache rebuilds.
              </p>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setIsConfirmModalOpen(false)}
              className="btn-secondary"
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
