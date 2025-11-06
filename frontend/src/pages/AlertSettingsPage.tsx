import { useState, useEffect } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { api } from "../services/api";
import type { AlertChannel, CreateAlertChannelRequest } from "../types/api";

export default function AlertSettingsPage() {
  const [channels, setChannels] = useState<AlertChannel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAddForm, setShowAddForm] = useState(false);

  // Form state
  const [channelType, setChannelType] = useState<"email" | "slack">("email");
  const [email, setEmail] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  useEffect(() => {
    loadChannels();
  }, []);

  const loadChannels = async () => {
    try {
      const data = await api.getAlertChannels();
      setChannels(data);
      setError("");
    } catch (error) {
      console.error("Error loading channels:", error);
      setError("Failed to load alert channels");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    // Validation
    if (channelType === "email" && !email.trim()) {
      setError("Email is required");
      return;
    }
    if (channelType === "slack" && !webhookUrl.trim()) {
      setError("Webhook URL is required");
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      const channelData: CreateAlertChannelRequest = {
        channel_type: channelType,
        configuration:
          channelType === "email"
            ? { email: email.trim() }
            : { webhook_url: webhookUrl.trim() },
      };

      console.log("Creating alert channel:", channelData);
      await api.createAlertChannel(channelData);

      // Reset form
      setEmail("");
      setWebhookUrl("");
      setShowAddForm(false);

      await loadChannels();
    } catch (error: unknown) {
      console.error("Error creating alert channel:", error);
      const err = error as {
        response?: { data?: { detail?: string } };
        message?: string;
      };
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Failed to create alert channel"
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (channelId: number) => {
    if (!confirm("Are you sure you want to delete this alert channel?")) {
      return;
    }

    try {
      await api.deleteAlertChannel(channelId);
      await loadChannels();
    } catch (error) {
      console.error("Error deleting channel:", error);
      setError("Failed to delete alert channel");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="spinner h-12 w-12 border-indigo-600 mb-4"></div>
          <p className="text-gray-600 font-medium">Loading alert settings...</p>
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
                      d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                    />
                  </svg>
                </div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  Alert Settings
                </h1>
              </div>
            </div>
            <button onClick={handleLogout} className="btn-secondary">
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <p className="text-gray-600 text-lg">
            Configure where you want to receive drift detection alerts
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="alert-error mb-6">
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Add Channel Button */}
        {!showAddForm && (
          <button
            onClick={() => setShowAddForm(true)}
            className="btn-primary px-6 py-3 shadow-md hover:shadow-lg flex items-center gap-2 mb-6"
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
            Add Alert Channel
          </button>
        )}

        {/* Add Form */}
        {showAddForm && (
          <div className="card p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Add New Alert Channel
            </h3>

            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                {/* Channel Type */}
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Channel Type
                  </label>
                  <div className="flex gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        value="email"
                        checked={channelType === "email"}
                        onChange={(e) =>
                          setChannelType(e.target.value as "email")
                        }
                        className="w-4 h-4 text-indigo-600"
                      />
                      <span className="text-gray-700">Email</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        value="slack"
                        checked={channelType === "slack"}
                        onChange={(e) =>
                          setChannelType(e.target.value as "slack")
                        }
                        className="w-4 h-4 text-indigo-600"
                      />
                      <span className="text-gray-700">Slack</span>
                    </label>
                  </div>
                </div>

                {/* Email Input */}
                {channelType === "email" && (
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="alerts@company.com"
                      className="input"
                      required
                      disabled={submitting}
                    />
                  </div>
                )}

                {/* Slack Webhook Input */}
                {channelType === "slack" && (
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Slack Webhook URL
                    </label>
                    <input
                      type="url"
                      value={webhookUrl}
                      onChange={(e) => setWebhookUrl(e.target.value)}
                      placeholder="https://hooks.slack.com/services/..."
                      className="input"
                      required
                      disabled={submitting}
                    />
                    <p className="text-sm text-gray-500 mt-2">
                      <a
                        href="https://api.slack.com/messaging/webhooks"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-indigo-600 hover:text-indigo-700 underline"
                      >
                        Learn how to create a Slack webhook
                      </a>
                    </p>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-3 justify-end mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddForm(false);
                    setEmail("");
                    setWebhookUrl("");
                    setError("");
                  }}
                  className="btn-secondary"
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={submitting}
                >
                  {submitting ? "Adding..." : "Add Channel"}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Channels List */}
        <div className="space-y-4">
          {channels.length === 0 ? (
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
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                No alert channels configured
              </h3>
              <p className="text-gray-600 text-lg mb-8">
                Add an email or Slack channel to receive drift detection alerts
              </p>
            </div>
          ) : (
            channels.map((channel) => (
              <div key={channel.id} className="card-hover p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div
                      className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                        channel.channel_type === "email"
                          ? "bg-blue-50 text-blue-600"
                          : "bg-purple-50 text-purple-600"
                      }`}
                    >
                      {channel.channel_type === "email" ? (
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
                            d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                          />
                        </svg>
                      ) : (
                        <svg
                          className="w-6 h-6"
                          fill="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z" />
                        </svg>
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-semibold text-gray-900 capitalize">
                          {channel.channel_type}
                        </h3>
                        {channel.is_active && (
                          <span className="badge-success">Active</span>
                        )}
                      </div>
                      <p className="text-gray-600 text-sm mt-1">
                        {channel.configuration &&
                        "email" in channel.configuration
                          ? channel.configuration.email
                          : channel.configuration &&
                            "webhook_url" in channel.configuration
                          ? "Webhook configured"
                          : "Configuration unavailable"}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Added{" "}
                        {new Date(channel.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(channel.id)}
                    className="btn-danger px-4 py-2"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </main>
    </div>
  );
}
