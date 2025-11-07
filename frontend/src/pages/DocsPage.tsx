import { useNavigate } from "react-router-dom";
import { BookOpen, ArrowLeft, ExternalLink } from "lucide-react";
import Footer from "../components/Footer";

export default function DocsPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate(-1)}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Back</span>
            </button>
            <div className="flex items-center gap-2">
              <BookOpen className="w-6 h-6 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">
                API Documentation
              </h1>
            </div>
            <div className="w-20"></div> {/* Spacer for centering */}
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="flex-1 flex flex-col">
        {/* Quick Links Section */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Getting Started */}
              <div className="border border-gray-200 rounded-lg p-4 hover:border-blue-500 transition-colors">
                <h3 className="font-semibold text-gray-900 mb-2">
                  🚀 Getting Started
                </h3>
                <p className="text-sm text-gray-600 mb-3">
                  Learn how to authenticate and make your first API call in minutes.
                </p>
                <button
                  onClick={() => navigate("/setup")}
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  View Setup Guide →
                </button>
              </div>

              {/* Interactive Docs */}
              <div className="border border-gray-200 rounded-lg p-4 hover:border-blue-500 transition-colors">
                <h3 className="font-semibold text-gray-900 mb-2">
                  🧪 Try API (Swagger)
                </h3>
                <p className="text-sm text-gray-600 mb-3">
                  Test endpoints interactively with the Swagger UI interface.
                </p>
                <a
                  href="https://api.driftassure.com/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium inline-flex items-center gap-1"
                >
                  Open Swagger UI <ExternalLink className="w-3 h-3" />
                </a>
              </div>

              {/* Code Examples */}
              <div className="border border-gray-200 rounded-lg p-4 hover:border-blue-500 transition-colors">
                <h3 className="font-semibold text-gray-900 mb-2">
                  📚 Code Examples
                </h3>
                <p className="text-sm text-gray-600 mb-3">
                  Copy-paste code snippets in Python, Node.js, cURL, and more.
                </p>
                <button
                  onClick={() => navigate("/setup")}
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                >
                  View Examples →
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Embedded ReDoc - Full Width */}
        <div className="flex-1 bg-gray-50 py-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden" style={{ height: '800px' }}>
              <iframe
                src="https://api.driftassure.com/redoc"
                className="w-full h-full border-0"
                title="DriftAssure API Documentation"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <Footer />
    </div>
  );
}
