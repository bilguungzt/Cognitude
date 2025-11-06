import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import type { MLModel, DriftStatus } from '../types/api';
import { useNavigate } from 'react-router-dom';

export default function DashboardPage() {
  const [models, setModels] = useState<MLModel[]>([]);
  const [driftStatuses, setDriftStatuses] = useState<Record<number, DriftStatus>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    loadModels();
    // Poll for updates every 30 seconds
    const interval = setInterval(loadModels, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadModels = async () => {
    try {
      const data = await api.getModels();
      setModels(data);
      
      // Load drift status for each model
      const statuses: Record<number, DriftStatus> = {};
      await Promise.all(
        data.map(async (model) => {
          try {
            const drift = await api.getCurrentDrift(model.id);
            statuses[model.id] = drift;
          } catch (err) {
            // Model may not have baseline set yet
            statuses[model.id] = {
              drift_detected: false,
              message: 'Baseline not configured',
            };
          }
        })
      );
      setDriftStatuses(statuses);
      setError('');
    } catch (err) {
      setError('Failed to load models');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getDriftBadge = (status: DriftStatus | undefined) => {
    if (!status) {
      return <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">Loading...</span>;
    }

    if (status.message) {
      return <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">{status.message}</span>;
    }

    if (status.drift_detected) {
      return (
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">
            ⚠️ Drift Detected
          </span>
          <span className="text-sm text-gray-600">
            Score: {status.drift_score?.toFixed(3)} | p-value: {status.p_value?.toFixed(4)}
          </span>
        </div>
      );
    }

    return (
      <div className="flex items-center gap-2">
        <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
          ✓ No Drift
        </span>
        <span className="text-sm text-gray-600">
          Score: {status.drift_score?.toFixed(3)}
        </span>
      </div>
    );
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
          <p className="text-gray-600">Loading models...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gray-900">DriftGuard AI</h1>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/alerts')}
                className="px-4 py-2 text-gray-700 hover:text-gray-900 font-medium"
              >
                Alert Settings
              </button>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Action Bar */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Your ML Models</h2>
            <p className="text-gray-600 mt-1">Monitor drift and performance across all registered models</p>
          </div>
          <button
            onClick={() => navigate('/models/new')}
            className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Register New Model
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Models Grid */}
        {models.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No models yet</h3>
            <p className="text-gray-600 mb-6">Get started by registering your first ML model</p>
            <button
              onClick={() => navigate('/models/new')}
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium inline-flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Register Your First Model
            </button>
          </div>
        ) : (
          <div className="grid gap-6">
            {models.map((model) => (
              <div
                key={model.id}
                className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900">{model.name}</h3>
                      <p className="text-gray-600 mt-1">
                        Version {model.version}
                        {model.description && ` • ${model.description}`}
                      </p>
                    </div>
                    {getDriftBadge(driftStatuses[model.id])}
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-500">Model ID</p>
                      <p className="font-medium text-gray-900">#{model.id}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Features</p>
                      <p className="font-medium text-gray-900">{model.features.length}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Created</p>
                      <p className="font-medium text-gray-900">
                        {new Date(model.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Last Checked</p>
                      <p className="font-medium text-gray-900">
                        {driftStatuses[model.id]?.timestamp
                          ? new Date(driftStatuses[model.id].timestamp!).toLocaleTimeString()
                          : 'N/A'}
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={() => navigate(`/models/${model.id}`)}
                      className="px-4 py-2 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 font-medium"
                    >
                      View Details
                    </button>
                    <button
                      onClick={() => navigate(`/models/${model.id}/drift`)}
                      className="px-4 py-2 bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 font-medium"
                    >
                      Drift History
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
