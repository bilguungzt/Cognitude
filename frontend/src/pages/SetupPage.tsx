import { useState, useEffect } from "react";
import { api } from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";

type Language = "python" | "nodejs" | "curl";

export default function SetupPage() {
  const [selectedLang, setSelectedLang] = useState<Language>("python");
  const [apiKey, setApiKey] = useState<string>("");
  const [testModelId, setTestModelId] = useState<string>("");
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState<string>("");
  const [newModelName, setNewModelName] = useState<string>("");
  const [creatingModel, setCreatingModel] = useState(false);
  const [modelCreateResult, setModelCreateResult] = useState<{
    success: boolean;
    message: string;
    modelId?: number;
  } | null>(null);
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const key = localStorage.getItem("driftassure_api_key") || "";
    setApiKey(key);
  }, []);

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopied(label);
    setTimeout(() => setCopied(""), 2000);
  };

  const handleTestPrediction = async () => {
    if (!testModelId) {
      setTestResult({ success: false, message: "Please enter a Model ID" });
      return;
    }

    setLoading(true);
    setTestResult(null); // Clear previous result

    try {
      await api.logPredictions(Number(testModelId), [
        {
          prediction_value: 0.75,
          features: {
            feature_1: 100,
            feature_2: 0.5,
            feature_3: "category_a",
            source: "driftassure_setup_page",
            test: true,
          },
          timestamp: new Date().toISOString(),
        },
      ]);
      setTestResult({
        success: true,
        message:
          "✅ Prediction logged successfully! Check your model's dashboard.",
      });
    } catch (error: unknown) {
      console.error("Test prediction error:", error);

      const err = error as {
        response?: {
          data?: {
            detail?: string | { msg?: string; type?: string; loc?: string[] }[];
          };
          status?: number;
          statusText?: string;
        };
        message?: string;
      };

      let errorMessage = "Unknown error";

      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (typeof detail === "string") {
          errorMessage = detail;
        } else if (Array.isArray(detail)) {
          // Handle FastAPI validation errors
          errorMessage = detail
            .map((e) => {
              const location = e.loc ? e.loc.join(" -> ") : "unknown";
              return `${location}: ${e.msg || "validation error"}`;
            })
            .join("; ");
        } else if (typeof detail === "object") {
          errorMessage = JSON.stringify(detail);
        }
      } else if (err.response?.status) {
        // HTTP error without detail
        errorMessage = `HTTP ${err.response.status}: ${
          err.response.statusText || "Request failed"
        }`;
      } else if (err.message) {
        errorMessage = err.message;
      }

      // Add helpful context based on error
      if (errorMessage.includes("Could not validate credentials")) {
        errorMessage += " (Check that you are logged in with a valid API key)";
      } else if (
        errorMessage.includes("404") ||
        errorMessage.includes("Not Found")
      ) {
        errorMessage += ` (Model ID ${testModelId} may not exist or you don't have access)`;
      }

      setTestResult({
        success: false,
        message: `❌ ${errorMessage}`,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleCreateModel = async () => {
    if (!newModelName.trim()) {
      setModelCreateResult({
        success: false,
        message: "Please enter a model name",
      });
      return;
    }

    setCreatingModel(true);
    setModelCreateResult(null);

    try {
      const model = await api.createModel({
        name: newModelName,
        version: "1.0.0",
        description: `Created from Setup page`,
        features: [
          { feature_name: "feature_1", feature_type: "numeric", order: 1 },
          { feature_name: "feature_2", feature_type: "numeric", order: 2 },
          { feature_name: "feature_3", feature_type: "categorical", order: 3 },
        ],
      });

      setModelCreateResult({
        success: true,
        message: `✅ Model "${model.name}" created! (ID: ${model.id})`,
        modelId: model.id,
      });

      // Auto-fill the model ID in the test section
      setTestModelId(String(model.id));
      setNewModelName("");
    } catch (error: unknown) {
      const err = error as {
        response?: { data?: { detail?: string } };
        message?: string;
      };

      setModelCreateResult({
        success: false,
        message: `❌ Error: ${
          err.response?.data?.detail || err.message || "Failed to create model"
        }`,
      });
    } finally {
      setCreatingModel(false);
    }
  };

  const API_BASE_URL =
    import.meta.env.VITE_API_URL || "https://api.driftassure.com"; // Production URL by default

  const codeSnippets: Record<Language, { code: string; install: string }> = {
    python: {
      code: `import requests
import json

API_KEY = "${apiKey ? "••••••••" : "your-api-key-here"}"  # Copy from Step 1
MODEL_ID = "your-model-id"  # From Step 2 below
BASE_URL = "${API_BASE_URL}"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Log a prediction
response = requests.post(
    f"{BASE_URL}/predictions/{MODEL_ID}",
    headers=headers,
    json={
        "prediction": 0.85,  # Your model's prediction
        "features": {
            "age": 35,
            "income": 75000,
            "category": "premium"
        },
        "metadata": {
            "model_version": "v1.2.3",
            "inference_time_ms": 45
        }
    }
)

if response.status_code == 200:
    print("✅ Prediction logged successfully!")
    print(json.dumps(response.json(), indent=2))
else:
    print(f"❌ Error: {response.text}")`,
      install: "pip install requests",
    },
    nodejs: {
      code: `const axios = require('axios');

const API_KEY = '${
        apiKey ? "••••••••" : "your-api-key-here"
      }';  // Copy from Step 1
const MODEL_ID = 'your-model-id'; // From Step 2 below
const BASE_URL = '${API_BASE_URL}';

const headers = {
  'X-API-Key': API_KEY,
  'Content-Type': 'application/json'
};

// Log a prediction
async function logPrediction() {
  try {
    const response = await axios.post(
      \`\${BASE_URL}/predictions/\${MODEL_ID}\`,
      {
        prediction: 0.85, // Your model's prediction
        features: {
          age: 35,
          income: 75000,
          category: 'premium'
        },
        metadata: {
          model_version: 'v1.2.3',
          inference_time_ms: 45
        }
      },
      { headers }
    );
    
    console.log('✅ Prediction logged successfully!');
    console.log(JSON.stringify(response.data, null, 2));
  } catch (error) {
    console.error('❌ Error:', error.response?.data || error.message);
  }
}

logPrediction();`,
      install: "npm install axios",
    },
    curl: {
      code: `curl -X POST "${API_BASE_URL}/predictions/your-model-id" \\
  -H "X-API-Key: ${apiKey ? "••••••••" : "your-api-key-here"}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "prediction": 0.85,
    "features": {
      "age": 35,
      "income": 75000,
      "category": "premium"
    },
    "metadata": {
      "model_version": "v1.2.3",
      "inference_time_ms": 45
    }
  }'`,
      install: "No installation needed (built-in)",
    },
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate("/dashboard")}
                className="text-gray-600 hover:text-gray-900"
              >
                ← Back to Dashboard
              </button>
              <h1 className="text-2xl font-bold text-gray-900">
                Setup & Integration
              </h1>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg p-8 mb-8 text-white">
          <div className="flex items-center gap-3 mb-3">
            <svg
              className="w-10 h-10"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            <h2 className="text-3xl font-bold">Get Started in 5 Minutes</h2>
          </div>
          <p className="text-blue-100 text-lg">
            Log your first prediction and start monitoring for drift. Copy-paste
            the code below and you're done.
          </p>
        </div>

        {/* Quick Start Steps */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-6">
            🚀 Quick Start Guide
          </h3>

          {/* Step 1: API Key */}
          <div className="mb-6 pb-6 border-b border-gray-200">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white font-bold bg-green-500">
                {apiKey ? "✓" : "1"}
              </div>
              <div className="flex-1">
                <h4 className="text-lg font-semibold text-gray-900 mb-2">
                  Get Your API Key
                </h4>
                <p className="text-gray-600 mb-3">
                  Your API key authenticates all requests to DriftAssure.
                </p>
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2">
                    <code className="flex-1 text-sm font-mono text-gray-800">
                      {apiKey
                        ? "••••••••••••••••••••••••••••••••"
                        : "No API key found. Please log in."}
                    </code>
                    <button
                      onClick={() => handleCopy(apiKey, "apiKey")}
                      disabled={!apiKey}
                      className={`px-3 py-1.5 text-sm rounded whitespace-nowrap ${
                        apiKey
                          ? "bg-blue-600 text-white hover:bg-blue-700"
                          : "bg-gray-300 text-gray-500 cursor-not-allowed"
                      }`}
                    >
                      {copied === "apiKey" ? "✓ Copied!" : "Copy to Clipboard"}
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    🔒 Your API key is hidden for security. Click "Copy to
                    Clipboard" to use it.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Step 2: Register Model - IMPROVED WITH INLINE WIDGET */}
          <div className="mb-6 pb-6 border-b border-gray-200">
            <div className="flex items-start gap-4">
              <div
                className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white font-bold ${
                  modelCreateResult?.success ? "bg-green-500" : "bg-gray-300"
                }`}
              >
                {modelCreateResult?.success ? "✓" : "2"}
              </div>
              <div className="flex-1">
                <h4 className="text-lg font-semibold text-gray-900 mb-2">
                  Register Your First Model
                </h4>
                <p className="text-gray-600 mb-3">
                  Create a model to track predictions and detect drift.
                </p>

                {/* Inline Model Creation Form */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex gap-4 items-start">
                    <div className="flex-1">
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Model Name
                      </label>
                      <input
                        type="text"
                        value={newModelName}
                        onChange={(e) => setNewModelName(e.target.value)}
                        placeholder="e.g., My Production Model"
                        disabled={creatingModel}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                      />
                    </div>
                    <div className="pt-7">
                      <button
                        onClick={handleCreateModel}
                        disabled={creatingModel || !newModelName.trim()}
                        className={`px-6 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
                          creatingModel || !newModelName.trim()
                            ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                            : "bg-green-600 text-white hover:bg-green-700"
                        }`}
                      >
                        {creatingModel ? "Creating..." : "✨ Create Model"}
                      </button>
                    </div>
                  </div>

                  {modelCreateResult && (
                    <div
                      className={`mt-3 p-3 rounded-lg ${
                        modelCreateResult.success
                          ? "bg-green-100 border border-green-300 text-green-800"
                          : "bg-red-100 border border-red-300 text-red-800"
                      }`}
                    >
                      <p className="text-sm font-medium">
                        {modelCreateResult.message}
                      </p>
                      {modelCreateResult.success &&
                        modelCreateResult.modelId && (
                          <p className="text-xs mt-1">
                            Model ID{" "}
                            <code className="bg-green-200 px-2 py-0.5 rounded">
                              {modelCreateResult.modelId}
                            </code>{" "}
                            auto-filled below!
                          </p>
                        )}
                    </div>
                  )}
                </div>

                <p className="text-xs text-gray-500 mt-2">
                  Or{" "}
                  <button
                    onClick={() => navigate("/dashboard")}
                    className="text-blue-600 hover:underline"
                  >
                    go to the Models page
                  </button>{" "}
                  to create manually
                </p>
              </div>
            </div>
          </div>

          {/* Step 3: Log Predictions */}
          <div>
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white font-bold bg-gray-300">
                3
              </div>
              <div className="flex-1">
                <h4 className="text-lg font-semibold text-gray-900 mb-2">
                  Log Your First Prediction
                </h4>
                <p className="text-gray-600">
                  Use the code snippets below to send predictions from your
                  application.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Code Examples */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8">
          {/* Tab Navigation */}
          <div className="border-b border-gray-200">
            <nav className="flex">
              {(["python", "nodejs", "curl"] as Language[]).map((lang) => (
                <button
                  key={lang}
                  onClick={() => setSelectedLang(lang)}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    selectedLang === lang
                      ? "border-blue-600 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }`}
                >
                  {lang === "nodejs"
                    ? "Node.js"
                    : lang === "curl"
                    ? "cURL"
                    : "Python"}
                </button>
              ))}
            </nav>
          </div>

          {/* Code Display */}
          <div className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h4 className="text-lg font-semibold text-gray-900">
                {selectedLang === "nodejs"
                  ? "Node.js"
                  : selectedLang === "curl"
                  ? "cURL"
                  : "Python"}{" "}
                Integration
              </h4>
              <button
                onClick={() =>
                  handleCopy(codeSnippets[selectedLang].code, selectedLang)
                }
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium flex items-center gap-2"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
                {copied === selectedLang ? "✓ Copied!" : "Copy Code"}
              </button>
            </div>
            <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto text-sm">
              <code>{codeSnippets[selectedLang].code}</code>
            </pre>
            <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-900">
                <strong>Install dependencies:</strong>{" "}
                <code className="bg-blue-100 px-2 py-1 rounded">
                  {codeSnippets[selectedLang].install}
                </code>
              </p>
            </div>
          </div>
        </div>

        {/* Live Test */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-2">
            🧪 Test Your Integration
          </h3>
          <p className="text-gray-600 mb-4">
            Send a test prediction directly from this page to verify your setup.
          </p>
          <div className="flex gap-4 items-start">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Model ID
              </label>
              <input
                type="text"
                value={testModelId}
                onChange={(e) => setTestModelId(e.target.value)}
                placeholder="e.g., 1"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">
                {testModelId
                  ? "✓ Model ID ready to test"
                  : "Create a model in Step 2 above, or enter an existing Model ID"}
              </p>
            </div>
            <div className="pt-7">
              <button
                onClick={handleTestPrediction}
                disabled={loading || !apiKey || !testModelId}
                className={`px-6 py-2 rounded-lg font-medium whitespace-nowrap transition-colors ${
                  loading || !apiKey || !testModelId
                    ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                    : "bg-blue-600 text-white hover:bg-blue-700"
                }`}
              >
                {loading ? "Sending..." : "Send Test Prediction"}
              </button>
            </div>
          </div>
          {testResult && (
            <div
              className={`mt-4 p-4 rounded-lg ${
                testResult.success
                  ? "bg-green-50 border border-green-200"
                  : "bg-red-50 border border-red-200"
              }`}
            >
              <p
                className={
                  testResult.success ? "text-green-800" : "text-red-800"
                }
              >
                {testResult.message}
              </p>
            </div>
          )}
        </div>

        {/* Troubleshooting */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-4">
            ⚠️ Troubleshooting
          </h3>
          <div className="space-y-6">
            <div className="border-l-4 border-red-500 pl-4">
              <h4 className="font-semibold text-gray-900 mb-2">
                403 Forbidden
              </h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Check that your API key is correct and not expired</li>
                <li>
                  • Ensure the{" "}
                  <code className="bg-gray-100 px-1 rounded">X-API-Key</code>{" "}
                  header is included in every request
                </li>
                <li>
                  • API keys are tied to organizations - verify you're using the
                  right key
                </li>
              </ul>
            </div>
            <div className="border-l-4 border-red-500 pl-4">
              <h4 className="font-semibold text-gray-900 mb-2">
                404 Not Found
              </h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Verify your Model ID exists (check the Models page)</li>
                <li>
                  • Ensure the endpoint URL is correct:{" "}
                  <code className="bg-gray-100 px-1 rounded">
                    /predictions/&#123;model_id&#125;
                  </code>
                </li>
                <li>• Check that your base URL matches your deployment</li>
              </ul>
            </div>
            <div className="border-l-4 border-red-500 pl-4">
              <h4 className="font-semibold text-gray-900 mb-2">
                422 Validation Error
              </h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>
                  • The{" "}
                  <code className="bg-gray-100 px-1 rounded">prediction</code>{" "}
                  field must be a number (float)
                </li>
                <li>
                  • The{" "}
                  <code className="bg-gray-100 px-1 rounded">features</code>{" "}
                  field must be an object/dict
                </li>
                <li>
                  • Feature keys must match your model's registered features
                  exactly
                </li>
              </ul>
            </div>
            <div className="border-l-4 border-yellow-500 pl-4">
              <h4 className="font-semibold text-gray-900 mb-2">
                Drift Not Detected
              </h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>
                  • You need at least 50 predictions to establish a baseline
                </li>
                <li>
                  • Drift detection runs every 15 minutes (check back soon)
                </li>
                <li>
                  • Set baseline manually via:{" "}
                  <code className="bg-gray-100 px-1 rounded">
                    POST /models/&#123;id&#125;/baseline
                  </code>
                </li>
                <li>• Check the Drift page for historical detection results</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Best Practices */}
        <div className="bg-gradient-to-r from-green-50 to-blue-50 border-l-4 border-blue-600 rounded-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">
            💡 Best Practices
          </h3>
          <div className="space-y-2 text-gray-700">
            <p>
              ✅ <strong>Log every prediction</strong> - Don't sample, log 100%
              for accurate drift detection
            </p>
            <p>
              ✅ <strong>Include metadata</strong> - Add model version, latency,
              and other context
            </p>
            <p>
              ✅ <strong>Use consistent feature names</strong> - Feature drift
              requires exact key matches
            </p>
            <p>
              ✅ <strong>Set baselines early</strong> - Generate baseline after
              50+ predictions or set manually
            </p>
            <p>
              ✅ <strong>Monitor alerts</strong> - Configure email/Slack
              notifications for critical models
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
