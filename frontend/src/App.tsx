import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { ToastProvider } from "./components/ToastContainer";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPageEnhanced from "./pages/LoginPageEnhanced";
import DashboardPage from "./pages/DashboardPage";
import ProvidersPage from "./pages/ProvidersPage";
import CachePage from "./pages/CachePage";
import AlertsPage from "./pages/AlertsPage";
import RateLimitsPage from "./pages/RateLimitsPage";
import SetupPage from "./pages/SetupPage";
import DocsPage from "./pages/DocsPage";
import CostDashboardEnhanced from "./pages/CostDashboardEnhanced";
import { ThemeProvider } from "./contexts/ThemeProvider";

function App() {
 return (
    <AuthProvider>
      <ThemeProvider>
        <ToastProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<LoginPageEnhanced />} />
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <DashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/providers"
                element={
                  <ProtectedRoute>
                    <ProvidersPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/cache"
                element={
                  <ProtectedRoute>
                    <CachePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/alerts"
                element={
                  <ProtectedRoute>
                    <AlertsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/rate-limits"
                element={
                  <ProtectedRoute>
                    <RateLimitsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/cost"
                element={
                  <ProtectedRoute>
                    <CostDashboardEnhanced />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/setup"
                element={
                  <ProtectedRoute>
                    <SetupPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/docs"
                element={
                  <ProtectedRoute>
                    <DocsPage />
                  </ProtectedRoute>
                }
              />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </BrowserRouter>
        </ToastProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;
