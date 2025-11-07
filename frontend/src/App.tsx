import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import AlertSettingsPage from "./pages/AlertSettingsPage";
import ModelDetailsPage from "./pages/ModelDetailsPage";
import ModelDriftPage from "./pages/ModelDriftPage";
import SetupPage from "./pages/SetupPage";
import DocsPage from "./pages/DocsPage";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/alerts"
            element={
              <ProtectedRoute>
                <AlertSettingsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/models/:modelId"
            element={
              <ProtectedRoute>
                <ModelDetailsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/models/:modelId/drift"
            element={
              <ProtectedRoute>
                <ModelDriftPage />
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
    </AuthProvider>
  );
}

export default App;
