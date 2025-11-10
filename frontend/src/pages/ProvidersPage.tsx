import { useState, useEffect } from "react";
import {
  Plus,
  Edit2,
  Trash2,
  Save,
  Eye,
  EyeOff,
  AlertTriangle,
  Database,
} from "lucide-react";
import Layout from "../components/Layout";
import Modal from "../components/Modal";
import LoadingSpinner from "../components/LoadingSpinner";
import EmptyState from "../components/EmptyState";
import api from "../services";
import type { Provider, ProviderCreate, ProviderType } from "../types/api";

export default function ProvidersPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProvider, setEditingProvider] = useState<Provider | null>(null);
  const [showApiKey, setShowApiKey] = useState<Record<number, boolean>>({});

  // Form state
  const [formData, setFormData] = useState<ProviderCreate>({
    provider: "openai",
    api_key: "",
    priority: 1,
    enabled: true,
  });

  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getProviders();
      setProviders(data.sort((a, b) => a.priority - b.priority));
    } catch (err) {
      setError(api.handleError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (provider?: Provider) => {
    if (provider) {
      setEditingProvider(provider);
      setFormData({
        provider: provider.provider,
        api_key: provider.api_key,
        priority: provider.priority,
        enabled: provider.enabled,
      });
    } else {
      setEditingProvider(null);
      setFormData({
        provider: "openai",
        api_key: "",
        priority: providers.length + 1,
        enabled: true,
      });
    }
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingProvider(null);
    setFormData({
      provider: "openai",
      api_key: "",
      priority: 1,
      enabled: true,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (editingProvider) {
        await api.updateProvider(editingProvider.id, {
          priority: formData.priority,
          enabled: formData.enabled,
        });
      } else {
        await api.createProvider(formData);
      }
      await loadProviders();
      handleCloseModal();
    } catch (err) {
      alert(api.handleError(err));
    }
  };

  const handleDelete = async (provider: Provider) => {
    if (
      !confirm(
        `Are you sure you want to delete the ${provider.provider} provider?`
      )
    ) {
      return;
    }

    try {
      await api.deleteProvider(provider.id);
      await loadProviders();
    } catch (err) {
      alert(api.handleError(err));
    }
  };

  const toggleApiKeyVisibility = (providerId: number) => {
    setShowApiKey((prev) => ({
      ...prev,
      [providerId]: !prev[providerId],
    }));
  };

  const maskApiKey = (key: string) => {
    if (key.length <= 8) return "********";
    return `${key.substring(0, 4)}...${key.substring(key.length - 4)}`;
  };

  const providerOptions: {
    value: ProviderType;
    label: string;
    description: string;
  }[] = [
    { value: "openai", label: "OpenAI", description: "GPT-4, GPT-3.5, etc." },
    {
      value: "anthropic",
      label: "Anthropic",
      description: "Claude 3 Opus, Sonnet, Haiku",
    },
    {
      value: "mistral",
      label: "Mistral AI",
      description: "Mistral Large, Medium",
    },
    {
      value: "groq",
      label: "Groq",
      description: "Fast inference with Llama, Mixtral",
    },
  ];

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
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              LLM Providers
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Configure your LLM provider API keys and routing priorities
            </p>
          </div>
          <button
            onClick={() => handleOpenModal()}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Provider
          </button>
        </div>

        {/* Error State */}
        {error && (
          <div className="card bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
              <p className="text-red-900 dark:text-red-300">{error}</p>
            </div>
          </div>
        )}

        {/* Empty State */}
        {providers.length === 0 ? (
          <EmptyState
            icon={Database}
            title="No providers configured"
            description="Add your first LLM provider to start using the proxy. You'll need an API key from OpenAI, Anthropic, Mistral, or Groq."
            action={{
              label: "Add Provider",
              onClick: () => handleOpenModal(),
            }}
          />
        ) : (
          /* Providers List */
          <div className="grid grid-cols-1 gap-4">
            {providers.map((provider) => (
              <div
                key={provider.id}
                className="card hover:shadow-md transition-all duration-200"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4 flex-1">
                    {/* Status Indicator */}
                    <div className="pt-1">
                      <div
                        className={`w-3 h-3 rounded-full ${
                          provider.enabled
                            ? "bg-green-500 animate-pulse"
                            : "bg-gray-400"
                        }`}
                      />
                    </div>

                    {/* Provider Info */}
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-xl font-semibold text-gray-900 dark:text-white capitalize">
                          {provider.provider}
                        </h3>
                        {provider.enabled ? (
                          <span className="px-2 py-1 text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded-full">
                            Active
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300 rounded-full">
                            Inactive
                          </span>
                        )}
                      </div>

                      <div className="space-y-2">
                        {/* API Key */}
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-600 dark:text-gray-400">
                            API Key:
                          </span>
                          <code className="text-sm font-mono bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
                            {showApiKey[provider.id]
                              ? provider.api_key
                              : maskApiKey(provider.api_key)}
                          </code>
                          <button
                            onClick={() => toggleApiKeyVisibility(provider.id)}
                            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                          >
                            {showApiKey[provider.id] ? (
                              <EyeOff className="w-4 h-4" />
                            ) : (
                              <Eye className="w-4 h-4" />
                            )}
                          </button>
                        </div>

                        {/* Priority */}
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-600 dark:text-gray-400">
                            Priority:
                          </span>
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {provider.priority}{" "}
                            {provider.priority === 1 && "(Primary)"}
                          </span>
                        </div>

                        {/* Created Date */}
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-600 dark:text-gray-400">
                            Added:
                          </span>
                          <span className="text-sm text-gray-900 dark:text-white">
                            {new Date(provider.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleOpenModal(provider)}
                      className="p-2 text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 transition-colors"
                      title="Edit provider"
                    >
                      <Edit2 className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => handleDelete(provider)}
                      className="p-2 text-gray-600 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 transition-colors"
                      title="Delete provider"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Info Card */}
        <div className="card bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-300 mb-2">
            How Provider Priority Works
          </h3>
          <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-300">
            <li className="flex items-start gap-2">
              <span className="text-blue-600 dark:text-blue-400">•</span>
              <span>
                Lower priority numbers are tried first (1 is highest priority)
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 dark:text-blue-400">•</span>
              <span>
                If a provider fails, the next priority provider is automatically
                used
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 dark:text-blue-400">•</span>
              <span>Disabled providers are skipped in the routing logic</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-600 dark:text-blue-400">•</span>
              <span>
                Smart routing automatically selects the best model across all
                enabled providers
              </span>
            </li>
          </ul>
        </div>
      </div>

      {/* Add/Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={editingProvider ? "Edit Provider" : "Add Provider"}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Provider Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Provider
            </label>
            <select
              value={formData.provider}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  provider: e.target.value as ProviderType,
                })
              }
              disabled={!!editingProvider}
              className="input"
            >
              {providerOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label} - {option.description}
                </option>
              ))}
            </select>
            {editingProvider && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Provider type cannot be changed after creation
              </p>
            )}
          </div>

          {/* API Key */}
          {!editingProvider && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                API Key
              </label>
              <input
                type="password"
                value={formData.api_key}
                onChange={(e) =>
                  setFormData({ ...formData, api_key: e.target.value })
                }
                placeholder="sk-..."
                className="input"
                required
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Your API key is encrypted and stored securely
              </p>
            </div>
          )}

          {/* Priority */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Priority
            </label>
            <input
              type="number"
              value={formData.priority}
              onChange={(e) =>
                setFormData({ ...formData, priority: parseInt(e.target.value) })
              }
              min="1"
              className="input"
              required
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Lower numbers = higher priority (1 is highest)
            </p>
          </div>

          {/* Enabled Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Status
              </label>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Enable or disable this provider
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
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={handleCloseModal}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              {editingProvider ? "Update Provider" : "Add Provider"}
            </button>
          </div>
        </form>
      </Modal>
    </Layout>
  );
}
