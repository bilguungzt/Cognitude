import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";

type ProviderType = "OpenAI" | "Anthropic" | "Mistral" | "Google AI" | "Cohere";
type IntegrationOption = "python" | "nodejs" | "curl" | "rest";

export default function SetupPage() {
  const { apiKey } = useAuth();
  const cognitudeApiKey = apiKey || "da_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
  const [providerApiKey, setProviderApiKey] = useState<string>("");
  const [selectedProvider, setSelectedProvider] = useState<ProviderType>("OpenAI");
  const [monthlyBudget, setMonthlyBudget] = useState<string>("500.00");
  const [priority, setPriority] = useState<"High" | "Medium" | "Low">("High");
  const [testProvider, setTestProvider] = useState<ProviderType>("OpenAI");
  const [testModel, setTestModel] = useState<string>("gpt-3.5-turbo");
  const [testMessage, setTestMessage] = useState<string>("Hello! This is a test from Cognitude.");
  const [testTemperature, setTestTemperature] = useState<number>(0);
  const [testLoading, setTestLoading] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<string>("⏳ Waiting for test request...");
  const [copied, setCopied] = useState<string>("");
  const [selectedIntegration, setSelectedIntegration] = useState<IntegrationOption>("python");
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopied(label);
    setTimeout(() => setCopied(""), 2000);
  };

  const handleTestRequest = async () => {
    setTestLoading(true);
    setTestResult("⏳ Sending test request...");
    
    // Simulate API call
    setTimeout(() => {
      setTestResult(`✅ Success! Test completed on ${testProvider} using ${testModel}.\nRequest: "${testMessage}"\nTemperature: ${testTemperature}\n\nResponse: "Hello! This is a simulated response from Cognitude."`);
      setTestLoading(false);
    }, 2000);
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const providerOptions: ProviderType[] = ["OpenAI", "Anthropic", "Mistral", "Google AI", "Cohere"];

  const pythonCodeExamples = {
    dropIn: `from openai import OpenAI

client = OpenAI(
    api_key="sk-proj-...", # Your OpenAI key
    base_url="https://api.cognitude.com/v1", # ← Add this line
    default_headers={"X-API-Key": "${cognitudeApiKey.substring(0, 8)}••••••••"} # ← Your Cognitude key
)

# Use exactly as before - no other changes needed!
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Hello, world!"}
    ]
)

print(response.choices[0].message.content)`,
    
    sdk: `from cognitude import Cognitude

# Initialize Cognitude
da = Cognitude(api_key="${cognitudeApiKey.substring(0, 8)}••••••••")

# Get optimized OpenAI client
client = da.OpenAI(api_key="sk-proj-...")

# Use exactly like OpenAI SDK
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Check your savings in real-time
savings = da.get_savings()
print(f"💰 You've saved \${savings['total_saved']:.2f} this month!")`,
    
    smartRouting: `from cognitude import Cognitude

da = Cognitude(api_key="${cognitudeApiKey.substring(0, 8)}••••••••")

# Configure providers
da.add_provider("openai", api_key="sk-proj-...")
da.add_provider("anthropic", api_key="sk-ant-...")
da.add_provider("mistral", api_key="...")

# Smart routing - auto-selects cheapest model
response = da.smart_completion(
    messages=[{"role": "user", "content": "Classify this email: ..."}],
    optimize_for="cost", # or "latency" or "quality"
    task_type="classification" # helps routing decision
)

print(f"Used: {response.model} from {response.provider}")
print(f"Cost: \${response.cost_usd:.4f}")
print(f"Saved: \${response.savings_usd:.4f} vs GPT-4")`
  };

  const nodeCodeExamples = {
    dropIn: `import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: 'sk-proj-...', // Your OpenAI key
  baseURL: 'https://api.cognitude.com/v1', // ← Add this
  defaultHeaders: {
    'X-API-Key': '${cognitudeApiKey.substring(0, 8)}••••••••' // ← Your Cognitude key
  }
});

// Use exactly as before
const response = await client.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'Hello!' }]
});

console.log(response.choices[0].message.content);`,
    
    sdk: `import { Cognitude } from 'cognitude';

const da = new Cognitude({ apiKey: '${cognitudeApiKey.substring(0, 8)}••••••••' });

// Get optimized client
const client = da.createOpenAI({ apiKey: 'sk-proj-...' });

const response = await client.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'Hello!' }]
});

// Check savings
const savings = await da.getSavings();
console.log(\`💰 Saved \$\${savings.totalSaved} this month\`);`
  };

  const curlExample = `curl -X POST https://api.cognitude.com/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: ${cognitudeApiKey.substring(0, 8)}••••••••" \\
  -H "Authorization: Bearer sk-proj-..." \\
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0
  }'`;

  const restExample = `{
  "url": "https://api.cognitude.com/v1/chat/completions",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer sk-proj-...",
    "X-API-Key": "${cognitudeApiKey.substring(0, 8)}••••••••",
    "Content-Type": "application/json"
  },
  "body": {
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0
  }
}`

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="glass border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 gradient-primary rounded-xl flex items-center justify-center shadow-md">
                <svg
                  className="w-5 h-5 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
                  />
                </svg>
              </div>
              <h1 className="text-lg sm:text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                Setup & Integration
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
              <button onClick={handleLogout} className="btn-secondary">
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">
                Cognitude Setup & Integration
              </h2>
              <p className="text-gray-600">
                Get started with Cognitude in 60 seconds and start saving on LLM costs.
              </p>
            </div>
          </div>
        </div>

        {/* Hero Section */}
        <div className="card mb-8">
          <div className="px-6 py-6 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl text-white mb-4">
            <div className="flex items-center gap-3 mb-3">
              <svg
                className="w-8 h-8"
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
              <h2 className="text-xl sm:text-2xl font-bold">
                Get Started in 60 Seconds
              </h2>
            </div>
            <p className="text-blue-100 text-sm sm:text-base">
              Monitor your LLM costs and automatically optimize spending. Simply replace your OpenAI base URL and you're done.
            </p>
          </div>
        </div>

        {/* Step 1: Get Your API Key */}
        <div className="card mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-6">
            Step 1: Get Your API Key
          </h3>
          <p className="text-gray-600 mb-4">
            Your API key authenticates all requests to Cognitude and tracks your usage.
          </p>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2">
              <code className="flex-1 text-sm font-mono text-gray-800 break-all bg-gray-100 p-3 rounded">
                {cognitudeApiKey.replace(/.(?=.{8})/g, "•")}
              </code>
              <button
                onClick={() => handleCopy(cognitudeApiKey, "cognitudeApiKey")}
                className="px-4 py-2 text-sm rounded whitespace-nowrap w-full sm:w-auto shadow-md hover:shadow-lg transition-all bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700"
              >
                {copied === "cognitudeApiKey" ? "✓ Copied!" : "Copy to Clipboard"}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              🔒 Your API key is hidden for security. Click "Copy to Clipboard" to use it.
            </p>
          </div>
        </div>

        {/* Step 2: Connect Your LLM Provider */}
        <div className="card mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-6">
            Step 2: Connect Your LLM Provider
          </h3>
          <p className="text-gray-600 mb-4">
            Add your OpenAI, Anthropic, or Mistral API keys so Cognitude can proxy and optimize your requests.
          </p>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex flex-wrap gap-4 mb-4">
              {providerOptions.map(provider => (
                <button
                  key={provider}
                  onClick={() => setSelectedProvider(provider)}
                  className={`px-4 py-2 rounded-lg ${
                    selectedProvider === provider
                      ? "bg-blue-600 text-white"
                      : "bg-white text-gray-700 border border-gray-300"
                  }`}
                >
                  {provider}
                </button>
              ))}
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Provider: {selectedProvider} API Key
              </label>
              <input
                type="password"
                value={providerApiKey}
                onChange={(e) => setProviderApiKey(e.target.value)}
                placeholder={`Paste Your ${selectedProvider} Key`}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div className="flex flex-col sm:flex-row gap-4 mb-4">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Monthly Budget (optional)
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-2.5 text-gray-500">$</span>
                  <input
                    type="number"
                    value={monthlyBudget}
                    onChange={(e) => setMonthlyBudget(e.target.value)}
                    className="w-full pl-8 pr-12 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <span className="absolute right-3 top-2.5 text-gray-500">USD</span>
                </div>
              </div>

              <div className="w-full sm:w-48">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority:
                </label>
                <div className="flex gap-2">
                  {(["High", "Medium", "Low"] as const).map((p) => (
                    <button
                      key={p}
                      onClick={() => setPriority(p)}
                      className={`flex-1 px-3 py-2 text-sm rounded-lg ${
                        priority === p
                          ? "bg-blue-600 text-white"
                          : "bg-white text-gray-700 border border-gray-300"
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                ✓ Test Connection
              </button>
              <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                Save Provider
              </button>
            </div>
          </div>
        </div>

        {/* Step 3: Integrate Cognitude */}
        <div className="card mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-6">
            Step 3: Integrate Cognitude (One-Line Change!)
          </h3>
          <p className="text-gray-600 mb-4">
            Choose your integration method below. All methods are 100% compatible with existing OpenAI code.
          </p>

          {/* Tab Navigation */}
          <div className="border-b border-gray-200 mb-6">
            <nav className="flex flex-wrap">
              {(["python", "nodejs", "curl", "rest"] as IntegrationOption[]).map((lang) => (
                <button
                  key={lang}
                  onClick={() => setSelectedIntegration(lang)}
                  className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                    selectedIntegration === lang
                      ? "border-blue-600 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }`}
                >
                  {lang === "nodejs"
                    ? "Node.js"
                    : lang === "curl"
                    ? "cURL"
                    : lang === "rest"
                    ? "REST API"
                    : "Python"}
                </button>
              ))}
            </nav>
          </div>

          {/* Code Display */}
          <div className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h4 className="text-lg font-semibold text-gray-900">
                {selectedIntegration === "nodejs"
                  ? "Node.js"
                  : selectedIntegration === "curl"
                  ? "cURL"
                  : selectedIntegration === "rest"
                  ? "REST API"
                  : "Python"}{" "}
                Integration
              </h4>
              <button
                onClick={() => {
                  let codeToCopy = "";
                  switch(selectedIntegration) {
                    case "python":
                      codeToCopy = pythonCodeExamples.dropIn;
                      break;
                    case "nodejs":
                      codeToCopy = nodeCodeExamples.dropIn;
                      break;
                    case "curl":
                      codeToCopy = curlExample;
                      break;
                    case "rest":
                      codeToCopy = restExample;
                      break;
                  }
                  handleCopy(codeToCopy, selectedIntegration);
                }}
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
                {copied === selectedIntegration ? "✓ Copied!" : "Copy Code"}
              </button>
            </div>

            {selectedIntegration === "python" && (
              <div>
                <h5 className="font-semibold text-gray-900 mb-3">Python Integration (Recommended)</h5>

                {/* Option A */}
                <div className="mb-6">
                  <h6 className="font-semibold text-gray-900 mb-2">Option A: Drop-in Replacement (Easiest)</h6>
                  <p className="text-gray-600 mb-2">Replace your OpenAI client initialization:</p>
                  <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto text-sm mb-3">
                    <code>{pythonCodeExamples.dropIn}</code>
                  </pre>
                  <p className="text-green-600 font-semibold">That's it! All requests now go through Cognitude for monitoring and optimization.</p>
                </div>

                {/* Option B */}
                <div className="mb-6">
                  <h6 className="font-semibold text-gray-900 mb-2">Option B: Cognitude SDK (More Features)</h6>
                  <div className="mb-3">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                      <p className="text-sm text-blue-900">
                        <strong>Install the SDK for advanced features:</strong>{" "}
                        <code className="bg-blue-100 px-2 py-1 rounded">pip install cognitude</code>
                      </p>
                    </div>
                  </div>
                  <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto text-sm mb-3">
                    <code>{pythonCodeExamples.sdk}</code>
                  </pre>
                </div>

                {/* Option C */}
                <div>
                  <h6 className="font-semibold text-gray-900 mb-2">Option C: Smart Routing (Auto-Optimize Costs)</h6>
                  <div className="mb-3">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                      <p className="text-sm text-blue-900">
                        <strong>Install the SDK:</strong>{" "}
                        <code className="bg-blue-100 px-2 py-1 rounded">pip install cognitude</code>
                      </p>
                    </div>
                  </div>
                  <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto text-sm">
                    <code>{pythonCodeExamples.smartRouting}</code>
                  </pre>
                </div>
              </div>
            )}

            {selectedIntegration === "nodejs" && (
              <div>
                <h5 className="font-semibold text-gray-900 mb-3">Node.js Integration</h5>

                {/* Option A */}
                <div className="mb-6">
                  <h6 className="font-semibold text-gray-900 mb-2">Option A: Drop-in Replacement</h6>
                  <div className="mb-3">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                      <p className="text-sm text-blue-900">
                        <strong>Install the OpenAI package:</strong>{" "}
                        <code className="bg-blue-100 px-2 py-1 rounded">npm install openai</code>
                      </p>
                    </div>
                  </div>
                  <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto text-sm mb-3">
                    <code>{nodeCodeExamples.dropIn}</code>
                  </pre>
                </div>

                {/* Option B */}
                <div>
                  <h6 className="font-semibold text-gray-900 mb-2">Option B: Cognitude SDK</h6>
                  <div className="mb-3">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                      <p className="text-sm text-blue-900">
                        <strong>Install the SDK:</strong>{" "}
                        <code className="bg-blue-100 px-2 py-1 rounded">npm install cognitude</code>
                      </p>
                    </div>
                  </div>
                  <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto text-sm">
                    <code>{nodeCodeExamples.sdk}</code>
                  </pre>
                </div>
              </div>
            )}

            {selectedIntegration === "curl" && (
              <div>
                <h5 className="font-semibold text-gray-900 mb-3">cURL Integration</h5>
                <p className="text-gray-600 mb-4">Test directly from command line:</p>
                <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto text-sm">
                  <code>{curlExample}</code>
                </pre>
                <div className="mt-4">
                  <h6 className="font-semibold text-gray-900 mb-2">Response includes cost tracking:</h6>
                  <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto text-sm">
                    <code>{`{
  "id": "chatcmpl-...",
  "choices": [...],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  },
  "x_cognitude": {
    "cost_usd": 0.00180,
    "cache_hit": false,
    "latency_ms": 842,
    "request_id": "550e8400-..."
  }
}`}</code>
                  </pre>
                </div>
              </div>
            )}

            {selectedIntegration === "rest" && (
              <div>
                <h5 className="font-semibold text-gray-900 mb-3">REST API Integration</h5>
                <p className="text-gray-600 mb-4">Use the REST API directly in any language:</p>
                <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto text-sm">
                  <code>{restExample}</code>
                </pre>
              </div>
            )}
          </div>
        </div>

        {/* Test Integration */}
        <div className="card mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-6">🧪 Test Your Integration</h3>
          <p className="text-gray-600 mb-4">
            Send a test request directly from this page to verify your setup.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
              <div className="relative">
                <select
                  value={testProvider}
                  onChange={(e) => setTestProvider(e.target.value as ProviderType)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white"
                >
                  {providerOptions.map(provider => (
                    <option key={provider} value={provider}>{provider}</option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                  <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
              <input
                type="text"
                value={testModel}
                onChange={(e) => setTestModel(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., gpt-3.5-turbo"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Test Message</label>
              <input
                type="text"
                value={testMessage}
                onChange={(e) => setTestMessage(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., Hello! This is a test from Cognitude."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Temperature</label>
              <div className="relative">
                <input
                  type="number"
                  value={testTemperature}
                  onChange={(e) => setTestTemperature(Number(e.target.value))}
                  min="0"
                  max="2"
                  step="0.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <span className="absolute right-3 top-2.5 text-gray-500">0 (for caching test)</span>
              </div>
            </div>
          </div>

          <div className="mb-4">
            <button
              onClick={handleTestRequest}
              disabled={testLoading}
              className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-colors disabled:opacity-50"
            >
              {testLoading ? "Sending Test Request..." : "Send Test Request"}
            </button>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 mb-2">Test Result:</h4>
            <p className={`${testResult.includes("Success") ? "text-green-600" : "text-gray-600"}`}>
              {testResult}
            </p>
          </div>
        </div>

        {/* Cost-Saving Features */}
        <div className="mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-6">⚡ Enable Cost-Saving Features</h3>

          <div className="card mb-6">
            <div className="flex items-start gap-4">
              <div className="bg-yellow-100 p-3 rounded-lg">
                <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="flex-1">
                <h4 className="font-bold text-lg text-gray-900 mb-2">🎯 Automatic Caching (15-30% savings)</h4>
                <p className="text-gray-600 mb-3">Cognitude automatically caches responses for identical requests.</p>
                <p className="text-gray-600 mb-2">How it works:</p>
                <ul className="list-disc list-inside text-gray-600 mb-3 space-y-1">
                  <li>Set temperature=0 for deterministic queries</li>
                  <li>We cache the response with 24-hour TTL</li>
                  <li>Future identical requests return instantly from cache</li>
                  <li>No cost charged for cache hits!</li>
                </ul>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                  <pre className="bg-gray-900 text-gray-100 rounded-lg p-3 text-sm overflow-x-auto">
                    <code>{`# This request will be cached
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    temperature=0 # ← Required for caching
)

# Second identical request = instant + free!
response2 = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    temperature=0
)`}</code>
                  </pre>
                </div>
                <div className="flex flex-wrap items-center gap-4">
                  <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">✓ Enabled</span>
                  <span className="text-sm">Cache Hit Rate: <span className="font-semibold">18.5%</span> (last 7 days)</span>
                  <span className="text-sm">Estimated Savings: <span className="font-semibold">$28.32/month</span></span>
                  <button className="text-blue-600 hover:underline text-sm font-medium">Configure Cache Settings</button>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-start gap-4">
              <div className="bg-green-100 p-3 rounded-lg">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="flex-1">
                <h4 className="font-bold text-lg text-gray-900 mb-2">🚀 Smart Routing (20-40% savings)</h4>
                <p className="text-gray-600 mb-3">Automatically route requests to the cheapest model that meets your quality requirements.</p>
                <p className="text-gray-600 mb-2">How it works:</p>
                <ul className="list-disc list-inside text-gray-600 mb-3 space-y-1">
                  <li>Analyses each prompt's complexity</li>
                  <li>Routes simple tasks to GPT-3.5, complex to GPT-4</li>
                  <li>Compares costs across OpenAI, Anthropic, Mistral</li>
                  <li>Selects optimal provider based on your priority</li>
                </ul>
                <div className="flex flex-wrap items-center gap-4">
                  <span className="px-3 py-1 bg-gray-100 text-gray-800 rounded-full text-sm font-medium">○ Not Configured</span>
                  <span className="text-sm">To enable:</span>
                  <ol className="list-decimal list-inside text-sm text-gray-600">
                    <li>Add at least 2 providers above (Step 2)</li>
                    <li>Use <code className="bg-gray-100 px-1 rounded">/v1/smart/completions</code> endpoint or Cognitude SDK</li>
                    <li>Set <code className="bg-gray-100 px-1 rounded">optimize_for="cost"</code> in requests</li>
                  </ol>
                  <button className="text-blue-600 hover:underline text-sm font-medium">Configure Smart Routing</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Cost Alerts */}
        <div className="card mb-8">
          <div className="flex items-start gap-4">
            <div className="bg-red-100 p-3 rounded-lg">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
            </div>
            <div className="flex-1">
              <h4 className="font-bold text-lg text-gray-900 mb-2">📊 Cost Alerts (Prevent surprises)</h4>
              <p className="text-gray-600 mb-4">Get notified when spending exceeds your thresholds.</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Alert Type</label>
                  <div className="text-gray-900">Daily Cost Threshold</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Threshold</label>
                  <div className="flex items-center">
                    <span className="text-gray-900 mr-2">$</span>
                    <span className="text-gray-900">50.00 USD/day</span>
                  </div>
                </div>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Notify via:</label>
                <div className="space-y-2">
                  <div className="flex items-center">
                    <input type="checkbox" id="email-alert" defaultChecked className="mr-2" />
                    <label htmlFor="email-alert" className="text-gray-700">Email: founder@startup.com</label>
                  </div>
                  <div className="flex items-center">
                    <input type="checkbox" id="slack-alert" defaultChecked className="mr-2" />
                    <label htmlFor="slack-alert" className="text-gray-700">Slack: #engineering-alerts</label>
                  </div>
                  <div className="flex items-center">
                    <input type="checkbox" id="webhook-alert" className="mr-2" />
                    <label htmlFor="webhook-alert" className="text-gray-700">Webhook: https://...</label>
                  </div>
                </div>
              </div>

              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">Configure Alerts</button>

              <div className="mt-4">
                <h5 className="font-semibold text-gray-900 mb-2">Current Alerts:</h5>
                <ul className="space-y-2">
                  <li className="flex items-center">
                    <span className="text-green-600 mr-2">✓</span>
                    <span>Daily cost {'>'} $50 {'→'} Slack + Email</span>
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-600 mr-2">✓</span>
                    <span>Monthly cost {'>'} 80% of plan limit {'→'} Email</span>
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-600 mr-2">✓</span>
                    <span>Error rate {'>'} 5% {'→'} Slack</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Troubleshooting */}
        <div className="card mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-6">⚠️ Troubleshooting</h3>
          
          <div className="space-y-6">
            {/* 401 Unauthorized */}
            <div className="border-l-4 border-red-500 pl-4">
              <h4 className="font-semibold text-gray-900 mb-2">401 Unauthorized</h4>
              <p className="text-gray-600 mb-2"><strong>Symptoms:</strong> {"{detail: \"Invalid API key\"}"}</p>
              <p className="text-gray-600 mb-2"><strong>Solutions:</strong></p>
              <ul className="list-disc list-inside text-gray-600 space-y-1">
                <li>✓ Check that your Cognitude API key is correct (Step 1)</li>
                <li>✓ Ensure X-API-Key header is included in every request</li>
                <li>✓ Verify you're using the production API URL: https://api.cognitude.com</li>
                <li>✓ API keys start with da_ - if not, regenerate in Settings</li>
              </ul>
            </div>

            {/* 403 Forbidden */}
            <div className="border-l-4 border-red-500 pl-4">
              <h4 className="font-semibold text-gray-900 mb-2">403 Forbidden - OpenAI Authentication Failed</h4>
              <p className="text-gray-600 mb-2"><strong>Symptoms:</strong> {"{detail: \"OpenAI API authentication failed\"}"}</p>
              <p className="text-gray-600 mb-2"><strong>Solutions:</strong></p>
              <ul className="list-disc list-inside text-gray-600 space-y-1">
                <li>✓ Verify your OpenAI API key is correct (starts with sk-proj- or sk-)</li>
                <li>✓ Check OpenAI key is in Authorization: Bearer {'<'}key{'>'} header</li>
                <li>✓ Confirm OpenAI key has sufficient credits at platform.openai.com</li>
                <li>✓ Test OpenAI key directly: curl https://api.openai.com/v1/models -H "Authorization: Bearer sk-..."</li>
              </ul>
            </div>

            {/* 429 Rate Limited */}
            <div className="border-l-4 border-red-500 pl-4">
              <h4 className="font-semibold text-gray-900 mb-2">429 Rate Limited</h4>
              <p className="text-gray-600 mb-2"><strong>Symptoms:</strong> {"{detail: \"Rate limit exceeded\"}"}</p>
              <p className="text-gray-600 mb-2"><strong>Solutions:</strong></p>
              <ul className="list-disc list-inside text-gray-600 space-y-1">
                <li>✓ Free tier: 100 requests/hour. Upgrade to Starter for 1,000/hour</li>
                <li>✓ Check your current usage: Dashboard {'→'} Usage tab</li>
                <li>✓ Implement exponential backoff in your application</li>
                <li>✓ Contact support for temporary limit increase</li>
              </ul>
            </div>

            {/* Caching Not Working */}
            <div className="border-l-4 border-red-500 pl-4">
              <h4 className="font-semibold text-gray-900 mb-2">Caching Not Working</h4>
              <p className="text-gray-600 mb-2"><strong>Symptoms:</strong> All requests show cache_hit: false</p>
              <p className="text-gray-600 mb-2"><strong>Solutions:</strong></p>
              <ul className="list-disc list-inside text-gray-600 space-y-1">
                <li>✓ Ensure temperature=0 (caching only works for deterministic requests)</li>
                <li>✓ Requests must be identical (same model, messages, max_tokens)</li>
                <li>✓ Cache TTL is 24 hours - requests older than 24h won't hit cache</li>
                <li>✓ Check cache stats: Dashboard {'→'} Analytics {'→'} Cache Hit Rate</li>
                <li>✓ Try test: Send same request twice within 1 minute</li>
              </ul>
            </div>

            {/* Costs Higher Than Expected */}
            <div className="border-l-4 border-red-500 pl-4">
              <h4 className="font-semibold text-gray-900 mb-2">Costs Higher Than Expected</h4>
              <p className="text-gray-600 mb-2"><strong>Symptoms:</strong> Dashboard shows more cost than OpenAI invoice</p>
              <p className="text-gray-600 mb-2"><strong>Solutions:</strong></p>
              <ul className="list-disc list-inside text-gray-600 space-y-1">
                <li>✓ Cognitude adds zero markup - costs are pass-through from OpenAI</li>
                <li>✓ Check if you're tracking all API keys (some requests bypassing proxy?)</li>
                <li>✓ Verify token counting: Dashboard {'→'} Requests {'→'} Compare our count vs OpenAI's</li>
                <li>✓ Email support@cognitude.com with request IDs for audit</li>
                <li>✓ We offer billing accuracy guarantee (see Terms)</li>
              </ul>
            </div>

            {/* Smart Routing Not Triggering */}
            <div className="border-l-4 border-red-500 pl-4">
              <h4 className="font-semibold text-gray-900 mb-2">Smart Routing Not Triggering</h4>
              <p className="text-gray-600 mb-2"><strong>Symptoms:</strong> All requests use same model despite smart routing enabled</p>
              <p className="text-gray-600 mb-2"><strong>Solutions:</strong></p>
              <ul className="list-disc list-inside text-gray-600 space-y-1">
                <li>✓ Confirm you're using /v1/smart/completions endpoint (not /v1/chat/completions)</li>
                <li>✓ Check you've added multiple providers in Step 2</li>
                <li>✓ Verify providers are enabled: Settings {'→'} Providers {'→'} Status</li>
                <li>✓ Some prompts may only have one suitable model (check routing explanation in response)</li>
                <li>✓ Test with clear cost difference: Compare GPT-4 vs GPT-3.5 for simple task</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Best Practices */}
        <div className="card mb-8">
          <h3 className="text-xl font-bold text-gray-900 mb-6">💡 Best Practices</h3>
          
          <div className="space-y-6">
            {/* Temperature=0 */}
            <div className="border-l-4 border-blue-500 pl-4">
              <h4 className="font-semibold text-gray-900 mb-2">✅ Use Temperature=0 for Deterministic Tasks</h4>
              <p className="text-gray-600 mb-2"><strong>Why:</strong> Enables automatic caching (15-30% savings)</p>
              <p className="text-gray-600 mb-2"><strong>When to use:</strong></p>
              <ul className="list-disc list-inside text-gray-600 space-y-1 mb-3">
                <li>Classification ("Is this spam?")</li>
                <li>Extraction ("Extract email from text")</li>
                <li>Structured output (JSON generation)</li>
                <li>Translation</li>
                <li>Summarization (when consistency matters)</li>
              </ul>
              <p className="text-gray-600 mb-2"><strong>When NOT to use:</strong></p>
              <ul className="list-disc list-inside text-gray-600 space-y-1 mb-3">
                <li>Creative writing</li>
                <li>Conversational AI</li>
                <li>Content generation</li>
                <li>Brainstorming</li>
              </ul>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <pre className="bg-gray-900 text-gray-100 rounded-lg p-3 text-sm overflow-x-auto">
                  <code>{`# Good - will be cached
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Classify: ..."}],
    temperature=0 # ← Deterministic
)

# Bad - won't be cached
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Classify: ..."}],
    temperature=0.7 # ← Random, can't cache
)`}</code>
                </pre>
              </div>
            </div>

            {/* Track Costs */}
            <div className="border-l-4 border-blue-500 pl-4">
              <h4 className="font-semibold text-gray-900 mb-2">✅ Track Costs by User/Feature</h4>
              <p className="text-gray-600 mb-2"><strong>Why:</strong> Identify which features/users drive costs</p>
              <p className="text-gray-600 mb-3"><strong>How:</strong> Add user field or custom tags</p>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <pre className="bg-gray-900 text-gray-100 rounded-lg p-3 text-sm overflow-x-auto">
                  <code>{`# Track by end-user
response = client.chat.completions.create(
    model="gpt-4",
    messages=[...],
    user="user_abc123" # ← OpenAI native field
)

# Or use custom metadata (Cognitude SDK)
response = da.chat.completions.create(
    model="gpt-4",
    messages=[...],
    metadata={
        "feature": "email_assistant",
        "team": "growth",
        "environment": "production"
    }
)`}</code>
                </pre>
                <p className="mt-2 text-sm text-gray-600">View breakdown: Dashboard {'→'} Analytics {'→'} By User/Tag</p>
              </div>
            </div>

            {/* Set Budget Alerts */}
            <div className="border-l-4 border-blue-500 pl-4">
              <h4 className="font-semibold text-gray-900 mb-2">✅ Set Budget Alerts Early</h4>
              <p className="text-gray-600 mb-2"><strong>Why:</strong> Prevent surprise bills during traffic spikes</p>
              <p className="text-gray-600 mb-3"><strong>Recommended thresholds:</strong></p>
              <ul className="list-disc list-inside text-gray-600 space-y-1">
                <li>Daily: 2x your average daily spend</li>
                <li>Monthly: 110% of your typical monthly spend</li>
                <li>Per-feature: Track expensive features separately</li>
              </ul>
            </div>

            {/* Use Smart Routing */}
            <div className="border-l-4 border-blue-500 pl-4">
              <h4 className="font-semibold text-gray-900 mb-2">✅ Use Smart Routing for Variable Workloads</h4>
              <p className="text-gray-600 mb-2"><strong>Why:</strong> Automatically optimize cost/latency per request</p>
              <p className="text-gray-600 mb-3"><strong>Best for:</strong></p>
              <ul className="list-disc list-inside text-gray-600 space-y-1 mb-3">
                <li>Mixed complexity workloads (simple + complex queries)</li>
                <li>Multi-tenant apps (different users need different quality)</li>
                <li>Cost-sensitive production apps</li>
              </ul>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <pre className="bg-gray-900 text-gray-100 rounded-lg p-3 text-sm overflow-x-auto">
                  <code>{`# Let Cognitude choose optimal model
response = da.smart_completion(
    messages=[{"role": "user", "content": prompt}],
    optimize_for="cost", # Prioritize cost savings
    max_latency_ms=3000, # But not slower than 3s
    task_type="classification" # Hint for routing
)

# Response includes routing explanation
print(f"Used {response.model} - saved \${response.savings_usd:.4f}")
)`}</code>
                </pre>
              </div>
            </div>

            {/* Monitor Weekly */}
            <div className="border-l-4 border-blue-500 pl-4">
              <h4 className="font-semibold text-gray-900 mb-2">✅ Monitor Weekly Recommendations</h4>
              <p className="text-gray-600 mb-2"><strong>Why:</strong> We analyze your usage and suggest specific optimizations</p>
              <p className="text-gray-600 mb-3"><strong>Where:</strong> Dashboard {'→'} Recommendations tab</p>
              <p className="text-gray-600 mb-2"><strong>Example suggestions:</strong></p>
              <ul className="list-disc list-inside text-gray-600 space-y-1 mb-3">
                <li>"Switch 3,840 simple queries from GPT-4 {'→'} GPT-3.5 (save $186/mo)"</li>
                <li>"Enable caching for 42% of requests (save $124/mo)"</li>
                <li>"Reduce max_tokens from 2000 {'→'} 500 for short responses (save $43/mo)"</li>
              </ul>
              <p className="text-gray-600"><strong>Action:</strong> Review weekly, implement top 2-3 recommendations</p>
            </div>
          </div>
        </div>

        {/* Next Steps */}
        <div className="card">
          <h3 className="text-xl font-bold text-gray-900 mb-6">🎯 Next Steps</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="flex items-center">
                <div className="bg-blue-100 p-2 rounded-lg mr-3">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">View Your Dashboard</h4>
                  <p className="text-sm text-gray-600">See real-time costs, cache hit rates, and savings projections.</p>
                </div>
              </div>
              <span className="text-blue-600 font-medium">Go to Dashboard {'→'}</span>
            </button>
            
            <button className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="flex items-center">
                <div className="bg-green-100 p-2 rounded-lg mr-3">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">Configure Multiple Providers</h4>
                  <p className="text-sm text-gray-600">Set up Anthropic Claude and Mistral for automatic failover and cost optimization.</p>
                </div>
              </div>
              <span className="text-blue-600 font-medium">Add Providers {'→'}</span>
            </button>
            
            <button className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="flex items-center">
                <div className="bg-yellow-100 p-2 rounded-lg mr-3">
                  <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">Set Up Alerts</h4>
                  <p className="text-sm text-gray-600">Get notified via Slack/email when costs exceed thresholds.</p>
                </div>
              </div>
              <span className="text-blue-600 font-medium">Configure Alerts {'→'}</span>
            </button>
            
            <button className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="flex items-center">
                <div className="bg-purple-100 p-2 rounded-lg mr-3">
                  <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">Review Recommendations</h4>
                  <p className="text-sm text-gray-600">See personalized suggestions to reduce costs based on your usage patterns.</p>
                </div>
              </div>
              <span className="text-blue-600 font-medium">View Recommendations {'→'}</span>
            </button>
          </div>
        </div>

        {/* Footer Note */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Your API key and provider credentials are encrypted at rest and never logged or shared. See our Security & Privacy Policy.</p>
        </div>
      </main>
    </div>
  );
}