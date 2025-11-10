// ==================== Core Types ====================

export interface Organization {
  id: number;
  name: string;
  api_key?: string;
  created_at: string;
}

// ==================== Provider Management ====================

export type ProviderType = 'openai' | 'anthropic' | 'mistral' | 'groq';

export interface Provider {
  id: number;
  organization_id: number;
  provider: ProviderType;
  api_key: string;
  priority: number;
  enabled: boolean;
  created_at: string;
  updated_at?: string;
}

export interface ProviderCreate {
  provider: ProviderType;
  api_key: string;
  priority: number;
  enabled: boolean;
}

export interface ProviderUpdate {
  priority?: number;
  enabled?: boolean;
}

// ==================== Chat Completions ====================

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface ChatCompletionRequest {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
  stream?: boolean;
}

export interface ChatCompletionChoice {
  index: number;
  message: ChatMessage;
  finish_reason: string;
}

export interface ChatCompletionUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface CognitudeMetadata {
  cached: boolean;
  cost: number;
  provider: string;
  cache_key?: string;
  selected_model?: string;
  complexity_score?: number;
  reasoning?: string;
}

export interface ChatCompletionResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: ChatCompletionChoice[];
  usage: ChatCompletionUsage;
  x_cognitude: CognitudeMetadata;
}

// ==================== Analytics ====================

export interface UsageBreakdown {
  model?: string;
  provider?: string;
  date?: string;
  requests: number;
  cost: number;
  tokens: number;
}

export interface DailyUsage {
  date: string;
  requests: number;
  cost: number;
}

export interface UsageStats {
  total_requests: number;
  total_cost: number;
  cache_hits: number;
  cache_hit_rate: number;
  cost_savings: number;
  breakdown: UsageBreakdown[];
  daily_usage: DailyUsage[];
}

export interface Recommendation {
  type: string;
  title: string;
  description: string;
  potential_savings: number;
  priority: 'high' | 'medium' | 'low';
}

export interface RecommendationsResponse {
  recommendations: Recommendation[];
  total_potential_savings: number;
}

// ==================== Cache Management ====================

export interface RedisCacheStats {
  hits: number;
  misses: number;
  hit_rate: number;
  total_keys: number;
  memory_usage_mb: number;
}

export interface PostgreSQLCacheStats {
  total_cached_responses: number;
  cost_savings: number;
  oldest_cache_entry: string;
}

export interface LifetimeSavings {
  total_cost_saved: number;
  requests_served_from_cache: number;
}

export interface CacheStats {
  redis: RedisCacheStats;
  postgresql: PostgreSQLCacheStats;
  lifetime_savings: LifetimeSavings;
}

export interface CacheClearRequest {
  cache_type?: 'redis' | 'postgresql' | 'all';
  pattern?: string;
}

export interface CacheClearResponse {
  message: string;
  redis_keys_deleted?: number;
  postgresql_rows_deleted?: number;
}

// ==================== Alerts ====================

export type AlertChannelType = 'email' | 'slack' | 'webhook';

export interface AlertChannelConfig {
  email?: string;
  webhook_url?: string;
  url?: string;
  method?: string;
  headers?: Record<string, string>;
}

export interface AlertChannel {
  id: number;
  organization_id: number;
  channel_type: AlertChannelType;
  configuration: AlertChannelConfig;
  enabled: boolean;
  created_at: string;
}

export interface AlertChannelCreate {
  channel_type: AlertChannelType;
  configuration: AlertChannelConfig;
}

export interface AlertConfig {
  id?: number;
  organization_id?: number;
  cost_threshold_daily?: number;
  cost_threshold_monthly?: number;
  rate_limit_warning?: number;
  cache_hit_rate_warning?: number;
  enabled: boolean;
  created_at?: string;
  updated_at?: string;
}

// ==================== Rate Limiting ====================

export interface RateLimitUsage {
  minute: number;
  hour: number;
  day: number;
}

export interface RateLimitConfig {
  organization_id: number;
  requests_per_minute: number;
  requests_per_hour: number;
  requests_per_day: number;
  enabled: boolean;
  current_usage?: RateLimitUsage;
  updated_at?: string;
}

export interface RateLimitUpdate {
  requests_per_minute?: number;
  requests_per_hour?: number;
  requests_per_day?: number;
  enabled?: boolean;
}

// ==================== Error Types ====================

export interface APIError {
  error: {
    message: string;
    type: string;
    code?: string;
  };
}
