import { useNavigate } from "react-router-dom";
import { BookOpen, ArrowLeft, ExternalLink } from "lucide-react";
import Footer from "../components/Footer";

export default function DocsPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex flex-col">
      {/* Header */}
      <header className="glass border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 gradient-primary rounded-xl flex items-center justify-center shadow-md">
                <BookOpen className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                API Documentation
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
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 flex flex-col">
        {/* Page Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            API Documentation
          </h2>
          <p className="text-gray-600">
            Comprehensive documentation for the Cognitude API
          </p>
        </div>
        
        {/* Quick Links Section */}
        <div className="card mb-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Getting Started */}
            <div className="card-hover p-6">
              <h3 className="font-semibold text-gray-900 mb-2">
                🚀 Getting Started
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                Learn how to authenticate and make your first API call in
                minutes.
              </p>
              <button
                onClick={() => navigate("/setup")}
                className="btn-ghost text-sm"
              >
                View Setup Guide →
              </button>
            </div>

            {/* Interactive Docs */}
            <div className="card-hover p-6">
              <h3 className="font-semibold text-gray-900 mb-2">
                🧪 Try API (Swagger)
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                Test endpoints interactively with the Swagger UI interface.
              </p>
              <a
                href="https://api.cognitude.com/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="btn-ghost text-sm inline-flex items-center gap-1"
              >
                Open Swagger UI <ExternalLink className="w-3 h-3" />
              </a>
            </div>

            {/* Code Examples */}
            <div className="card-hover p-6">
              <h3 className="font-semibold text-gray-900 mb-2">
                📚 Code Examples
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                Copy-paste code snippets in Python, Node.js, cURL, and more.
              </p>
              <button
                onClick={() => navigate("/setup")}
                className="btn-ghost text-sm"
              >
                View Examples →
              </button>
            </div>
          </div>
        </div>

        {/* Embedded ReDoc - Full Width */}
        <div className="flex-1">
          <div className="card">
            <iframe
              src="https://api.cognitude.com/redoc"
              className="w-full"
              title="Cognitude API Documentation"
              style={{ height: "800px" }}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}
