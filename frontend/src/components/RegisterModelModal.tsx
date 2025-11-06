import { useState } from "react";
import type { FormEvent } from "react";
import { api } from "../services/api";
import type { CreateModelRequest } from "../types/api";

interface RegisterModelModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

interface Feature {
  feature_name: string;
  feature_type: "numeric" | "categorical";
  order: number;
}

export default function RegisterModelModal({
  isOpen,
  onClose,
  onSuccess,
}: RegisterModelModalProps) {
  const [modelName, setModelName] = useState("");
  const [version, setVersion] = useState("1.0.0");
  const [description, setDescription] = useState("");
  const [features, setFeatures] = useState<Feature[]>([
    { feature_name: "", feature_type: "numeric", order: 1 },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const addFeature = () => {
    setFeatures([
      ...features,
      { feature_name: "", feature_type: "numeric", order: features.length + 1 },
    ]);
  };

  const removeFeature = (index: number) => {
    const newFeatures = features.filter((_, i) => i !== index);
    // Reorder
    newFeatures.forEach((f, i) => (f.order = i + 1));
    setFeatures(newFeatures);
  };

  const updateFeature = (
    index: number,
    field: keyof Feature,
    value: string
  ) => {
    const newFeatures = [...features];
    if (field === "feature_type") {
      newFeatures[index][field] = value as "numeric" | "categorical";
    } else if (field === "feature_name") {
      newFeatures[index][field] = value;
    }
    setFeatures(newFeatures);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    // Validation
    if (!modelName.trim()) {
      setError("Model name is required");
      return;
    }

    if (!version.trim()) {
      setError("Version is required");
      return;
    }

    if (features.length === 0 || features.some((f) => !f.feature_name.trim())) {
      setError("All features must have names");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const modelData: CreateModelRequest = {
        name: modelName.trim(),
        version: version.trim(),
        description: description.trim() || undefined,
        features: features.map((f) => ({
          feature_name: f.feature_name.trim(),
          feature_type: f.feature_type,
          order: f.order,
        })),
      };

      await api.createModel(modelData);

      // Reset form
      setModelName("");
      setVersion("1.0.0");
      setDescription("");
      setFeatures([{ feature_name: "", feature_type: "numeric", order: 1 }]);

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create model");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative glass rounded-2xl shadow-soft w-full max-w-2xl p-8 border border-white/50">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                Register New Model
              </h2>
              <p className="text-gray-600 mt-1">
                Add a new ML model to monitor for drift
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
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
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="alert-error mb-6">
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit}>
            {/* Model Info */}
            <div className="space-y-4 mb-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Model Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={modelName}
                    onChange={(e) => setModelName(e.target.value)}
                    placeholder="e.g., fraud_detector"
                    className="input"
                    disabled={loading}
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Version <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={version}
                    onChange={(e) => setVersion(e.target.value)}
                    placeholder="e.g., 1.0.0"
                    className="input"
                    disabled={loading}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Brief description of your model"
                  rows={2}
                  className="input resize-none"
                  disabled={loading}
                />
              </div>
            </div>

            {/* Features Section */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Features
                  </h3>
                  <p className="text-sm text-gray-600">
                    Define the features your model monitors
                  </p>
                </div>
                <button
                  type="button"
                  onClick={addFeature}
                  className="btn-ghost text-sm flex items-center gap-2"
                  disabled={loading}
                >
                  <svg
                    className="w-4 h-4"
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
                  Add Feature
                </button>
              </div>

              <div className="space-y-3">
                {features.map((feature, index) => (
                  <div key={index} className="flex gap-3 items-start">
                    <div className="flex-1">
                      <input
                        type="text"
                        value={feature.feature_name}
                        onChange={(e) =>
                          updateFeature(index, "feature_name", e.target.value)
                        }
                        placeholder="Feature name"
                        className="input"
                        disabled={loading}
                      />
                    </div>
                    <div className="w-40">
                      <select
                        value={feature.feature_type}
                        onChange={(e) =>
                          updateFeature(index, "feature_type", e.target.value)
                        }
                        className="input"
                        disabled={loading}
                      >
                        <option value="numeric">Numeric</option>
                        <option value="categorical">Categorical</option>
                      </select>
                    </div>
                    {features.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeFeature(index)}
                        className="p-3 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        disabled={loading}
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
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={onClose}
                className="btn-secondary px-6"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-primary px-6 shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={loading}
              >
                {loading ? "Creating..." : "Create Model"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
