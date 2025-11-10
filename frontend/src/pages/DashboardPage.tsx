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
      <Layout title="Dashboard">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <LoadingSpinner size="lg" text="Loading dashboard..." />
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout title="Dashboard">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <EmptyState
            icon={AlertTriangle}
            title="Failed to load dashboard"
            description={error}
            action={{
              label: "Retry",
              onClick: loadDashboardData,
            }}
          />
        </div>
      </Layout>
    );
  }

  const hasData = usageStats && usageStats.total_requests > 0;
  const cacheHitRate = cacheStats?.redis.hit_rate || 0;
  const totalSavings =
    (usageStats?.cost_savings || 0) +
    (cacheStats?.lifetime_savings.total_cost_saved || 0);

  return (
    <Layout title="Dashboard">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Dashboard
          </h2>
          <p className="text-gray-600">
            Monitor your LLM usage, costs, and performance in real-time
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Total Requests
                </p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {usageStats?.total_requests.toLocaleString() || 0}
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-full">
                <Activity className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <div className="mt-4">
              <p className="text-xs text-gray-500">Last 7 days</p>
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Total Cost
                </p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  ${(usageStats?.total_cost || 0).toFixed(2)}
                </p>
              </div>
              <div className="p-3 bg-green-100 rounded-full">
                <DollarSign className="w-6 h-6 text-green-600" />
              </div>
            </div>
            <div className="mt-4">
              <p className="text-xs text-gray-500">Last 7 days</p>
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Cache Hit Rate
                </p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {(cacheHitRate * 100).toFixed(1)}%
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

          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">
                  Total Savings
                </p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  ${totalSavings.toFixed(2)}
                </p>
              </div>
              <div className="p-3 bg-emerald-100 rounded-full">
                <TrendingUp className="w-6 h-6 text-emerald-600" />
              </div>
            </div>
            <div className="mt-4">
              <p className="text-xs text-gray-500">Lifetime</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900">
                Provider Status
              </h2>
              <Link
                to="/providers"
                className="btn-ghost btn-sm"
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
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
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
                        <p className="font-medium text-gray-900 capitalize">
                          {provider.provider}
                        </p>
                        <p className="text-sm text-gray-600">
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

          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-yellow-500" />
                <h2 className="text-lg font-semibold text-gray-900">
                  AI Recommendations
                </h2>
              </div>
              <Link
                to="/cost-analytics"
                className="btn-ghost btn-sm"
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
                          ? "border-red-500 bg-red-50"
                          : rec.priority === "medium"
                          ? "border-yellow-500 bg-yellow-50"
                          : "border-blue-500 bg-blue-50"
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="font-semibold text-gray-900">
                          {rec.title}
                        </h3>
                        <span className="text-sm font-semibold text-green-600">
                          Save ${rec.potential_savings.toFixed(2)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">
                        {rec.description}
                      </p>
                    </div>
                  ))}

                {recommendations.total_potential_savings > 0 && (
                  <div className="mt-4 p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
                    <p className="text-sm text-gray-700">
                      <strong>Total potential savings:</strong>{" "}
                      <span className="text-lg font-bold text-green-600">
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
          <div className="card bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-200">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-blue-600 rounded-lg">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Welcome to Cognitude! 🚀
                </h2>
                <p className="text-gray-600 mb-4">
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
                      className="text-blue-600 hover:underline font-medium"
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
                      className="text-blue-600 hover:underline font-medium"
                    >
                      Update your OpenAI SDK to point to Cognitude
                    </Link>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                      3
                    </div>
                    <span className="text-gray-700 font-medium">
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
