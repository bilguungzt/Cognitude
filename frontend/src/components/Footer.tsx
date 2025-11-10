import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300 border-t border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand Section */}
          <div className="col-span-1 md:col-span-1">
            <h3 className="text-white font-bold text-xl mb-4">Cognitude</h3>
            <p className="text-sm text-gray-400 mb-4">
              ML Model Monitoring & Drift Detection Platform
            </p>
            <p className="text-xs text-gray-500">
              by <span className="text-blue-400 font-semibold">Cognitude</span>
            </p>
          </div>

          {/* Product Links */}
          <div>
            <h4 className="text-white font-semibold mb-4">Product</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link
                  to="/dashboard"
                  className="hover:text-white transition-colors"
                >
                  Dashboard
                </Link>
              </li>
              <li>
                <Link
                  to="/setup"
                  className="hover:text-white transition-colors"
                >
                  Getting Started
                </Link>
              </li>
              <li>
                <Link to="/docs" className="hover:text-white transition-colors">
                  API Documentation
                </Link>
              </li>
              <li>
                <Link
                  to="/alerts"
                  className="hover:text-white transition-colors"
                >
                  Alert Settings
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="text-white font-semibold mb-4">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="https://api.cognitude.com/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white transition-colors"
                >
                  Swagger UI
                </a>
              </li>
              <li>
                <a
                  href="https://api.cognitude.com/redoc"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white transition-colors"
                >
                  ReDoc
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/bilguungzt/Drift_Guard"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white transition-colors"
                >
                  GitHub
                </a>
              </li>
              <li>
                <a
                  href="https://api.cognitude.com/health"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white transition-colors"
                >
                  API Status
                </a>
              </li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <h4 className="text-white font-semibold mb-4">Support</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="mailto:support@cognitude.io"
                  className="hover:text-white transition-colors"
                >
                  support@cognitude.io
                </a>
              </li>
              <li>
                <a
                  href="https://cognitude.com/support"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white transition-colors"
                >
                  Help Center
                </a>
              </li>
              <li>
                <a
                  href="https://cognitude.com/privacy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white transition-colors"
                >
                  Privacy Policy
                </a>
              </li>
              <li>
                <a
                  href="https://cognitude.com/terms"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white transition-colors"
                >
                  Terms of Service
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-8 border-t border-gray-800">
          <div className="text-center">
            <p className="text-sm text-gray-500">
              © {new Date().getFullYear()} Cognitude by Cognitude. All rights
              reserved.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
