import { useState, useEffect } from "react";
import {
  Bell,
  Plus,
  Edit2,
  Trash2,
  Save,
  Mail,
  MessageSquare,
  Webhook,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";
import Layout from "../components/Layout";
import Modal from "../components/Modal";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import api from "../services";
import type {
  AlertChannel,
  AlertChannelCreate,
  AlertConfig,
  AlertChannelType,
} from "../types/api";

export default function AlertsPage() {
  const [channels, setChannels] = useState<AlertChannel[]>([]);
  const [config, setConfig] = useState<AlertConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isChannelModalOpen, setIsChannelModalOpen] = useState(false);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);

  // Form state for channels
  const [channelForm, setChannelForm] = useState<AlertChannelCreate>({
    channel_type: "email",
    configuration: {},
  });

  // Form state for config
  const [configForm, setConfigForm] = useState<AlertConfig>({
    enabled: true,
    cost_threshold_daily: 100,
    cost_threshold_monthly: 2000,
    rate_limit_warning: 0.8,
    cache_hit_rate_warning: 0.3,
  });

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      setError(null);
      const [channelsData, configData] = await Promise.all([
        api.getAlertChannels().catch(() => []),
        api.getAlertConfig().catch(() => null),
      ]);
      setChannels(channelsData);
      setConfig(configData);
      if (configData) {
        setConfigForm(configData);
      }
    } catch (err) {
      setError(api.handleError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateChannel = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createAlertChannel(channelForm);
      await loadAlerts();
      setIsChannelModalOpen(false);
      resetChannelForm();
    } catch (err) {
      alert(api.handleError(err));
    }
  };

  const handleDeleteChannel = async (channelId: number) => {
    if (!confirm("Are you sure you want to delete this alert channel?")) {
      return;
    }
    try {
      await api.deleteAlertChannel(channelId);
      await loadAlerts();
    } catch (err) {
      alert(api.handleError(err));
    }
  };

  const handleUpdateConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.updateAlertConfig(configForm);
      await loadAlerts();
      setIsConfigModalOpen(false);
    } catch (err) {
      alert(api.handleError(err));
    }
  };

  const resetChannelForm = () => {
    setChannelForm({
      channel_type: "email",
      configuration: {},
    });
  };

  const getChannelIcon = (type: AlertChannelType) => {
    switch (type) {
      case "email":
        return <Mail className="w-5 h-5" />;
      case "slack":
        return <MessageSquare className="w-5 h-5" />;
      case "webhook":
        return <Webhook className="w-5 h-5" />;
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

  return (
    <Layout title="Alert Configuration">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                Alert Configuration
              </h2>
              <p className="text-gray-600">
                Configure notification channels and alert thresholds
              </p>
            </div>
            <button
              onClick={() => setIsChannelModalOpen(true)}
              className="btn-primary flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Channel
            </button>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="alert-error mb-6">
            <AlertTriangle className="w-5 h-5" />
            <p>{error}</p>
          </div>
        )}

        {/* Alert Status Card */}
        {config && (
          <div className="card mb-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div
                  className={`p-3 rounded-lg ${
                    config.enabled ? "bg-green-600" : "bg-gray-400"
                  }`}
                >
                  <Bell className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Alerts {config.enabled ? "Enabled" : "Disabled"}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {config.enabled
                      ? "Notifications are active and will be sent when thresholds are exceeded"
                      : "Notifications are disabled"}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsConfigModalOpen(true)}
                className="btn-secondary flex items-center gap-2"
              >
                <Edit2 className="w-4 h-4" />
                Configure
              </button>
            </div>
          </div>
        )}

        {/* Alert Channels */}
        <div className="card mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">
            Notification Channels
          </h3>

          {channels.length === 0 ? (
            <EmptyState
              icon={Bell}
              title="No notification channels"
              description="Add your first notification channel to receive alerts"
              action={{
                label: "Add Channel",
                onClick: () => setIsChannelModalOpen(true),
              }}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {channels.map((channel) => (
                <div
                  key={channel.id}
                  className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-all"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-100 rounded-lg">
                        {getChannelIcon(channel.channel_type)}
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900 capitalize">
                          {channel.channel_type}
                        </h3>
                        {channel.enabled ? (
                          <span className="text-xs text-green-600 flex items-center gap-1">
                            <CheckCircle className="w-3 h-3" />
                            Active
                          </span>
                        ) : (
                          <span className="text-xs text-gray-500">
                            Inactive
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => handleDeleteChannel(channel.id)}
                      className="text-gray-400 hover:text-red-600 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="text-sm text-gray-600 space-y-1">
                    {channel.channel_type === "email" &&
                      channel.configuration.email && (
                        <p>Email: {channel.configuration.email}</p>
                      )}
                    {channel.channel_type === "slack" &&
                      channel.configuration.webhook_url && (
                        <p>Webhook configured</p>
                      )}
                    {channel.channel_type === "webhook" &&
                      channel.configuration.url && (
                        <p>URL: {channel.configuration.url}</p>
                      )}
                    <p className="text-xs text-gray-500">
                      Added: {new Date(channel.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Threshold Preview */}
        {config && (
          <div className="card mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">
              Current Thresholds
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">
                  Daily Cost Threshold
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  ${config.cost_threshold_daily?.toFixed(2) || "—"}
                </p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">
                  Monthly Cost Threshold
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  ${config.cost_threshold_monthly?.toFixed(2) || "—"}
                </p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">
                  Rate Limit Warning
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {((config.rate_limit_warning || 0) * 100).toFixed(0)}%
                </p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">
                  Cache Hit Rate Warning
                </p>
                <p className="text-2xl font-bold text-gray-900">
                  {((config.cache_hit_rate_warning || 0) * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Info Card */}
        <div className="card">
          <h3 className="text-lg font-semibold text-blue-900 mb-6">
            Alert Types
          </h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li className="flex items-start gap-2">
              <span className="text-blue-600">•</span>
              <span>
                <strong>Cost Alerts:</strong> Triggered when daily or monthly
                costs exceed thresholds
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600">•</span>
              <span>
                <strong>Rate Limit Warnings:</strong> Alert when approaching
                rate limits (e.g., 80% usage)
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600">•</span>
              <span>
                <strong>Cache Performance:</strong> Notify when cache hit rate
                drops below threshold
              </span>
            </li>
          </ul>
        </div>
      </div>

      {/* Add Channel Modal */}
      <Modal
        isOpen={isChannelModalOpen}
        onClose={() => {
          setIsChannelModalOpen(false);
          resetChannelForm();
        }}
        title="Add Notification Channel"
      >
        <form onSubmit={handleCreateChannel} className="space-y-4">
          {/* Channel Type */}
          <div>
            <label className="label">Channel Type</label>
            <select
              value={channelForm.channel_type}
              onChange={(e) => {
                setChannelForm({
                  channel_type: e.target.value as AlertChannelType,
                  configuration: {},
                });
              }}
              className="input"
            >
              <option value="email">Email</option>
              <option value="slack">Slack</option>
              <option value="webhook">Webhook</option>
            </select>
          </div>

          {/* Email Configuration */}
          {channelForm.channel_type === "email" && (
            <div>
              <label className="label">Email Address</label>
              <input
                type="email"
                value={channelForm.configuration.email || ""}
                onChange={(e) =>
                  setChannelForm({
                    ...channelForm,
                    configuration: { email: e.target.value },
                  })
                }
                placeholder="alerts@company.com"
                className="input"
                required
              />
            </div>
          )}

          {/* Slack Configuration */}
          {channelForm.channel_type === "slack" && (
            <div>
              <label className="label">Slack Webhook URL</label>
              <input
                type="url"
                value={channelForm.configuration.webhook_url || ""}
                onChange={(e) =>
                  setChannelForm({
                    ...channelForm,
                    configuration: { webhook_url: e.target.value },
                  })
                }
                placeholder="https://hooks.slack.com/services/YOUR/WEBHOOK"
                className="input"
                required
              />
              <p className="text-sm text-gray-500 mt-1">
                Get your webhook URL from Slack's Incoming Webhooks app
              </p>
            </div>
          )}

          {/* Webhook Configuration */}
          {channelForm.channel_type === "webhook" && (
            <>
              <div>
                <label className="label">Webhook URL</label>
                <input
                  type="url"
                  value={channelForm.configuration.url || ""}
                  onChange={(e) =>
                    setChannelForm({
                      ...channelForm,
                      configuration: {
                        ...channelForm.configuration,
                        url: e.target.value,
                      },
                    })
                  }
                  placeholder="https://your-api.com/webhooks/cognitude"
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="label">HTTP Method</label>
                <select
                  value={channelForm.configuration.method || "POST"}
                  onChange={(e) =>
                    setChannelForm({
                      ...channelForm,
                      configuration: {
                        ...channelForm.configuration,
                        method: e.target.value,
                      },
                    })
                  }
                  className="input"
                >
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                </select>
              </div>
            </>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={() => {
                setIsChannelModalOpen(false);
                resetChannelForm();
              }}
              className="btn-outline"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              Add Channel
            </button>
          </div>
        </form>
      </Modal>

      {/* Configure Thresholds Modal */}
      <Modal
        isOpen={isConfigModalOpen}
        onClose={() => setIsConfigModalOpen(false)}
        title="Configure Alert Thresholds"
      >
        <form onSubmit={handleUpdateConfig} className="space-y-4">
          {/* Enable/Disable */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Enable Alerts
              </label>
              <p className="text-xs text-gray-500 mt-1">
                Turn on/off all alert notifications
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={configForm.enabled}
                onChange={(e) =>
                  setConfigForm({ ...configForm, enabled: e.target.checked })
                }
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {/* Daily Cost Threshold */}
          <div>
            <label className="label">Daily Cost Threshold ($)</label>
            <input
              type="number"
              step="0.01"
              value={configForm.cost_threshold_daily || ""}
              onChange={(e) =>
                setConfigForm({
                  ...configForm,
                  cost_threshold_daily: parseFloat(e.target.value),
                })
              }
              placeholder="100.00"
              className="input"
            />
            <p className="text-sm text-gray-500 mt-1">
              Alert when daily cost exceeds this amount
            </p>
          </div>

          {/* Monthly Cost Threshold */}
          <div>
            <label className="label">Monthly Cost Threshold ($)</label>
            <input
              type="number"
              step="0.01"
              value={configForm.cost_threshold_monthly || ""}
              onChange={(e) =>
                setConfigForm({
                  ...configForm,
                  cost_threshold_monthly: parseFloat(e.target.value),
                })
              }
              placeholder="2000.00"
              className="input"
            />
            <p className="text-sm text-gray-500 mt-1">
              Alert when monthly cost exceeds this amount
            </p>
          </div>

          {/* Rate Limit Warning */}
          <div>
            <label className="label">Rate Limit Warning (%)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={configForm.rate_limit_warning || ""}
              onChange={(e) =>
                setConfigForm({
                  ...configForm,
                  rate_limit_warning: parseFloat(e.target.value),
                })
              }
              placeholder="0.80"
              className="input"
            />
            <p className="text-sm text-gray-500 mt-1">
              Alert at this % of rate limit (0.8 = 80%)
            </p>
          </div>

          {/* Cache Hit Rate Warning */}
          <div>
            <label className="label">Cache Hit Rate Warning (%)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={configForm.cache_hit_rate_warning || ""}
              onChange={(e) =>
                setConfigForm({
                  ...configForm,
                  cache_hit_rate_warning: parseFloat(e.target.value),
                })
              }
              placeholder="0.30"
              className="input"
            />
            <p className="text-sm text-gray-500 mt-1">
              Alert when cache hit rate drops below this (0.3 = 30%)
            </p>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={() => setIsConfigModalOpen(false)}
              className="btn-outline"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              Save Configuration
            </button>
          </div>
        </form>
      </Modal>
    </Layout>
  );
}
