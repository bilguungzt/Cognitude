import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Zap,
  TrendingUp,
  DollarSign,
  Database,
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import Layout from "../components/Layout";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import api from "../services";
import type {
  UsageStats,
  CacheStats,
  Provider,
  RecommendationsResponse,
} from "../types/api";

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [cacheStats, setCacheStats] = useState<CacheStats | null>(null);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [recommendations, setRecommendations] =
    useState<RecommendationsResponse | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [usage, cache, providerList, recs] = await Promise.all([
        api.getUsageStats({ group_by: "day" }).catch(() => null),
        api.getCacheStats().catch(() => null),
        api.getProviders().catch(() => []),
        api.getRecommendations().catch(() => null),
      ]);

      setUsageStats(usage);
      setCacheStats(cache);
      setProviders(providerList);
      setRecommendations(recs);
    } catch (err) {
      setError(api.handleError(err));
    } finally {
      setLoading(false);
    }
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
          title="Failed to load dashboard"
          description={error}
          action={{
            label: "Retry",
            onClick: loadDashboardData,
          }}
        />
      </Layout>
    );
  }

  const hasData = usageStats && usageStats.total_requests > 0;
  const cacheHitRate = cacheStats?.redis.hit_rate || 0;
  const totalSavings =
    (usageStats?.cost_savings || 0) +
    (cacheStats?.lifetime_savings.total_cost_saved || 0);

  return (
    <Layout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Dashboard
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Monitor your LLM usage, costs, and performance in real-time
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="card group hover:shadow-lg transition-all duration-200">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg group-hover:scale-110 transition-transform">
                <Activity className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Last 7 days
              </span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
              {usageStats?.total_requests.toLocaleString() || 0}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Total Requests
            </p>
          </div>

          <div className="card group hover:shadow-lg transition-all duration-200">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg group-hover:scale-110 transition-transform">
                <DollarSign className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Last 7 days
              </span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
              ${(usageStats?.total_cost || 0).toFixed(2)}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Total Cost
            </p>
          </div>

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
              {(cacheHitRate * 100).toFixed(1)}%
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Cache Hit Rate
            </p>
            <div className="mt-3 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-purple-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${cacheHitRate * 100}%` }}
              />
            </div>
          </div>

          <div className="card group hover:shadow-lg transition-all duration-200">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg group-hover:scale-110 transition-transform">
                <TrendingUp className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
              </div>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Lifetime
              </span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
              ${totalSavings.toFixed(2)}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Total Savings
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Provider Status
              </h2>
              <Link
                to="/providers"
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
              >
                Manage
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {providers.length === 0 ? (
              <EmptyState
                icon={Database}
                title="No providers configured"
                description="Add your first LLM provider to start using the proxy"
                action={{
                  label: "Add Provider",
                  onClick: () => (window.location.href = "/providers"),
                }}
              />
            ) : (
              <div className="space-y-3">
                {providers.map((provider) => (
                  <div
                    key={provider.id}
                    className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-750 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-2 h-2 rounded-full ${
                          provider.enabled
                            ? "bg-green-500 animate-pulse"
                            : "bg-gray-400"
                        }`}
                      />
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white capitalize">
                          {provider.provider}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Priority: {provider.priority}
                        </p>
                      </div>
                    </div>
                    {provider.enabled ? (
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    ) : (
                      <XCircle className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-yellow-500" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  AI Recommendations
                </h2>
              </div>
              <Link
                to="/cost-analytics"
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
              >
                View All
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {!recommendations ||
            recommendations.recommendations.length === 0 ? (
              <EmptyState
                icon={Sparkles}
                title="No recommendations yet"
                description="We need more usage data to generate personalized recommendations"
              />
            ) : (
              <div className="space-y-3">
                {recommendations.recommendations
                  .slice(0, 3)
                  .map((rec, index) => (
                    <div
                      key={index}
                      className={`p-4 border-l-4 rounded-lg ${
                        rec.priority === "high"
                          ? "border-red-500 bg-red-50 dark:bg-red-900/10"
                          : rec.priority === "medium"
                          ? "border-yellow-500 bg-yellow-50 dark:bg-yellow-900/10"
                          : "border-blue-500 bg-blue-50 dark:bg-blue-900/10"
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="font-semibold text-gray-900 dark:text-white">
                          {rec.title}
                        </h3>
                        <span className="text-sm font-semibold text-green-600 dark:text-green-400">
                          Save ${rec.potential_savings.toFixed(2)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {rec.description}
                      </p>
                    </div>
                  ))}

                {recommendations.total_potential_savings > 0 && (
                  <div className="mt-4 p-4 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg border border-green-200 dark:border-green-800">
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      <strong>Total potential savings:</strong>{" "}
                      <span className="text-lg font-bold text-green-600 dark:text-green-400">
                        ${recommendations.total_potential_savings.toFixed(2)}
                        /month
                      </span>
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {!hasData && providers.length === 0 && (
          <div className="card bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border-2 border-blue-200 dark:border-blue-800">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-blue-600 rounded-lg">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  Welcome to Cognitude! 🚀
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  Get started in 3 easy steps to start saving 30-85% on your LLM
                  costs
                </p>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                      1
                    </div>
                    <Link
                      to="/providers"
                      className="text-blue-600 dark:text-blue-400 hover:underline font-medium"
                    >
                      Configure your LLM providers (OpenAI, Anthropic, etc.)
                    </Link>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                      2
                    </div>
                    <Link
                      to="/docs"
                      className="text-blue-600 dark:text-blue-400 hover:underline font-medium"
                    >
                      Update your OpenAI SDK to point to Cognitude
                    </Link>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                      3
                    </div>
                    <span className="text-gray-700 dark:text-gray-300 font-medium">
                      Start saving money automatically! 💰
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
