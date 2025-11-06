// Organization & Auth
export interface Organization {
  id: number;
  name: string;
  api_key?: string;
  created_at?: string;
  updated_at?: string;
}

// Model Feature
export interface ModelFeature {
  id?: number;
  feature_name: string;
  feature_type: "numeric" | "categorical";
  order: number;
  baseline_stats?: {
    samples?: number[];
    mean?: number;
    std?: number;
    categories?: string[];
  };
}

// ML Model
export interface MLModel {
  id: number;
  name: string;
  version: string;
  description?: string;
  organization_id: number;
  created_at: string;
  updated_at: string;
  features: ModelFeature[];
}

export interface CreateModelRequest {
  name: string;
  version: string;
  description?: string;
  features: Omit<ModelFeature, "id">[];
}

// Predictions
export interface Prediction {
  id?: number;
  model_id: number;
  features: Record<string, any>;
  prediction_value: number;
  actual_value?: number;
  timestamp?: string;
  time?: string;
}

export interface CreatePredictionRequest {
  features: Record<string, any>;
  prediction_value: number;
  actual_value?: number;
  timestamp?: string;
}

// Drift Detection
export interface DriftStatus {
  drift_detected: boolean;
  drift_score?: number;
  p_value?: number;
  samples?: number;
  message?: string;
}

export interface DriftHistoryPoint {
  timestamp: string;
  drift_score: number;
  drift_detected: boolean;
  p_value: number;
  samples: number;
}

export interface DriftHistoryPoint {
  timestamp: string;
  drift_score: number;
  drift_detected: boolean;
  p_value: number;
  samples: number;
}

// Alert Channels
export interface AlertChannel {
  id: number;
  channel_type: "email" | "slack";
  configuration: EmailConfig | SlackConfig;
  is_active: boolean;
  created_at: string;
  configured?: boolean;
}

export interface EmailConfig {
  email: string;
}

export interface SlackConfig {
  webhook_url: string;
}

export interface CreateAlertChannelRequest {
  channel_type: "email" | "slack";
  configuration: EmailConfig | SlackConfig;
}

// API Response types
export interface ApiError {
  detail: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}
