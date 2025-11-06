import axios from "axios";
import type { AxiosInstance, AxiosError } from "axios";
import type {
  Organization,
  MLModel,
  CreateModelRequest,
  ModelFeature,
  Prediction,
  CreatePredictionRequest,
  DriftStatus,
  DriftHistoryPoint,
  AlertChannel,
  CreateAlertChannelRequest,
  ApiError,
} from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class DriftGuardAPI {
  private client: AxiosInstance;
  private apiKey: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Load API key from localStorage
    this.apiKey = localStorage.getItem("driftguard_api_key");
    if (this.apiKey) {
      this.setApiKey(this.apiKey);
    }

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          // Unauthorized - clear API key and redirect to login
          this.clearApiKey();
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth methods
  setApiKey(apiKey: string) {
    this.apiKey = apiKey;
    localStorage.setItem("driftguard_api_key", apiKey);
    this.client.defaults.headers.common["X-API-Key"] = apiKey;
  }

  clearApiKey() {
    this.apiKey = null;
    localStorage.removeItem("driftguard_api_key");
    delete this.client.defaults.headers.common["X-API-Key"];
  }

  getApiKey(): string | null {
    return this.apiKey;
  }

  isAuthenticated(): boolean {
    return !!this.apiKey;
  }

  // Organization / Auth
  async register(name: string): Promise<Organization> {
    const response = await this.client.post<Organization>("/auth/register", {
      name,
    });
    return response.data;
  }

  // Models
  async getModels(): Promise<MLModel[]> {
    const response = await this.client.get<MLModel[]>("/models");
    return response.data;
  }

  async getModel(modelId: number): Promise<MLModel> {
    const response = await this.client.get<MLModel>(`/models/${modelId}`);
    return response.data;
  }

  async createModel(model: CreateModelRequest): Promise<MLModel> {
    const response = await this.client.post<MLModel>("/models/", model);
    return response.data;
  }

  async deleteModel(modelId: number): Promise<void> {
    await this.client.delete(`/models/${modelId}`);
  }

  async updateFeatureBaseline(
    modelId: number,
    featureId: number,
    baselineStats: { samples: number[] }
  ): Promise<ModelFeature> {
    const response = await this.client.put<ModelFeature>(
      `/models/${modelId}/features/${featureId}`,
      { baseline_stats: baselineStats }
    );
    return response.data;
  }

  // Predictions
  async logPredictions(
    modelId: number,
    predictions: CreatePredictionRequest[]
  ): Promise<Prediction[]> {
    const response = await this.client.post<Prediction[]>(
      `/predictions/models/${modelId}/predictions`,
      predictions
    );
    return response.data;
  }

  async getPredictions(
    modelId: number,
    skip = 0,
    limit = 100
  ): Promise<Prediction[]> {
    const response = await this.client.get<Prediction[]>(
      `/predictions/models/${modelId}/predictions`,
      { params: { skip, limit } }
    );
    return response.data;
  }

  // Drift Detection
  async getCurrentDrift(modelId: number): Promise<DriftStatus> {
    const response = await this.client.get<DriftStatus>(
      `/drift/models/${modelId}/drift/current`
    );
    return response.data;
  }

  async getDriftHistory(
    modelId: number,
    days = 7
  ): Promise<DriftHistoryPoint[]> {
    const response = await this.client.get<DriftHistoryPoint[]>(
      `/drift/models/${modelId}/drift/history`,
      { params: { days } }
    );
    return response.data;
  }

  // Alert Channels
  async getAlertChannels(): Promise<AlertChannel[]> {
    const response = await this.client.get<AlertChannel[]>("/alert-channels/");
    return response.data;
  }

  async createAlertChannel(
    channel: CreateAlertChannelRequest
  ): Promise<AlertChannel> {
    const response = await this.client.post<AlertChannel>(
      "/alert-channels/",
      channel
    );
    return response.data;
  }

  async deleteAlertChannel(channelId: number): Promise<void> {
    await this.client.delete(`/alert-channels/${channelId}`);
  }

  // Health check
  async healthCheck(): Promise<{ message: string }> {
    const response = await this.client.get<{ message: string }>("/");
    return response.data;
  }
}

// Export singleton instance
export const api = new DriftGuardAPI();
export default api;
