import { useState, useEffect, useCallback } from "react";
import { api } from "../services";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Calendar, TrendingUp, Activity, DollarSign } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import Footer from "../components/Footer";

interface DailyUsage {
  date: string;
  requests: number;
  cost: number;
}

interface AnalyticsData {
  total_requests: number;
  total_cost: number;
  average_latency: number;
  usage_by_day: DailyUsage[];
}

export default function CostDashboard() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dateRange, setDateRange] = useState<{ start: string; end: string }>({
    start: new Date(Date.now() - 30 * 24 * 60 * 1000)
      .toISOString()
      .split("T")[0],
    end: new Date().toISOString().split("T")[0],
  });
  const { logout } = useAuth();
  const navigate = useNavigate();

  const loadAnalyticsData = useCallback(async () => {
    setLoading(true);

    const startDate = new Date(dateRange.start);
    const endDate = new Date(dateRange.end);

    if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
      setError("Please select a valid date range");
      setAnalyticsData(null);
      setLoading(false);
      return;
    }

    if (startDate > endDate) {
      setError("Start date must be before end date");
      setAnalyticsData(null);
      setLoading(false);
      return;
    }

    try {
      setError("");
      const data = await api.getUsageAnalytics(dateRange.start, dateRange.end);
      setAnalyticsData(data);
    } catch (err) {
      setError("Failed to load analytics data");
      console.error("Error loading analytics:", err);
    } finally {
      setLoading(false);
    }
  }, [dateRange]);

  useEffect(() => {
    loadAnalyticsData();
  }, [loadAnalyticsData]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  const handleDateChange = (key: "start" | "end", value: string) => {
    setDateRange((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex flex-col">
      {/* Header */}
      <header className="glass border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 gradient-primary rounded-xl flex items-center justify-center shadow-md">
                <DollarSign className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                Cost Dashboard
              </h1>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-3">
              <button
                onClick={() => navigate("/dashboard")}
                className="btn-ghost"
              >
                Dashboard
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
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* Date Range Selector */}
        <div className="mb-8 p-4 bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <h2 className="text-lg font-semibold text-gray-900">Date Range</h2>
            <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-gray-500" />
                <input
                  type="date"
                  value={dateRange.start}
                  onChange={(e) => handleDateChange("start", e.target.value)}
                  className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <span className="hidden sm:flex items-center text-gray-500 mx-2">
                to
              </span>
              <div className="flex items-center gap-2">
                <input
                  type="date"
                  value={dateRange.end}
                  onChange={(e) => handleDateChange("end", e.target.value)}
                  className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
              <button
                onClick={loadAnalyticsData}
                className="btn-primary px-4 py-2 text-sm whitespace-nowrap"
              >
                Apply
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="alert-error mb-6">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="spinner h-12 w-12 border-indigo-600"></div>
          </div>
        ) : analyticsData ? (
          <div>
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="card p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">
                      Total Spend
                    </p>
                    <p className="text-3xl font-bold text-gray-900 mt-1">
                      {formatCurrency(analyticsData.total_cost)}
                    </p>
                  </div>
                  <div className="p-3 bg-green-100 rounded-full">
                    <DollarSign className="w-6 h-6 text-green-600" />
                  </div>
                </div>
                <div className="mt-4">
                  <p className="text-xs text-gray-500">
                    {analyticsData.total_requests} total requests
                  </p>
                </div>
              </div>

              <div className="card p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">
                      Total Requests
                    </p>
                    <p className="text-3xl font-bold text-gray-900 mt-1">
                      {analyticsData.total_requests.toLocaleString()}
                    </p>
                  </div>
                  <div className="p-3 bg-blue-100 rounded-full">
                    <Activity className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
                <div className="mt-4">
                  <p className="text-xs text-gray-500">Across all models</p>
                </div>
              </div>

              <div className="card p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">
                      Avg Latency
                    </p>
                    <p className="text-3xl font-bold text-gray-900 mt-1">
                      {analyticsData.average_latency.toFixed(2)} ms
                    </p>
                  </div>
                  <div className="p-3 bg-purple-100 rounded-full">
                    <TrendingUp className="w-6 h-6 text-purple-600" />
                  </div>
                </div>
                <div className="mt-4">
                  <p className="text-xs text-gray-500">Average response time</p>
                </div>
              </div>
            </div>

            {/* Daily Spend Chart */}
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-6">
                Daily Spend
              </h3>
              {analyticsData.usage_by_day.length > 0 ? (
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={analyticsData.usage_by_day}
                      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis
                        dataKey="date"
                        tickFormatter={formatDate}
                        tick={{ fontSize: 12 }}
                      />
                      <YAxis
                        tick={{ fontSize: 12 }}
                        tickFormatter={(value) => formatCurrency(Number(value))}
                      />
                      <Tooltip
                        formatter={(value) => [
                          formatCurrency(Number(value)),
                          "Cost",
                        ]}
                        labelFormatter={(label) => `Date: ${formatDate(label)}`}
                      />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="cost"
                        stroke="#4f46e5"
                        strokeWidth={2}
                        activeDot={{ r: 8 }}
                        name="Daily Cost"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="flex items-center justify-center h-64 text-gray-500">
                  <p>No data available for the selected date range</p>
                </div>
              )}
            </div>

            {/* Daily Usage Table */}
            <div className="card p-6 mt-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-6">
                Daily Usage Breakdown
              </h3>
              {analyticsData.usage_by_day.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Requests
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Cost
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {analyticsData.usage_by_day.map((day, index) => (
                        <tr
                          key={index}
                          className={
                            index % 2 === 0 ? "bg-white" : "bg-gray-50"
                          }
                        >
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {formatDate(day.date)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {day.requests.toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatCurrency(day.cost)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <p>No usage data available for the selected date range</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-500">No analytics data available</p>
          </div>
        )}
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}
