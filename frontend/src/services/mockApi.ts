import type {
  Organization,
  Provider,
  ProviderCreate,
  ProviderUpdate,
  ChatCompletionRequest,
  ChatCompletionResponse,
  UsageStats,
  RecommendationsResponse,
  CacheStats,
  CacheClearRequest,
  CacheClearResponse,
  AlertChannel,
  AlertChannelCreate,
  AlertConfig,
  RateLimitConfig,
  RateLimitUpdate,
  APIError,
} from "../types/api";

function fetchJson<T = any>(path: string): Promise<T> {
  return fetch(`/mock/${path}.json`).then(async (r) => {
    if (!r.ok)
      throw new Error(`Mock fetch failed: ${r.status} ${r.statusText}`);
    return (await r.json()) as T;
  });
}

class MockCognitudeAPI {
  private apiKey: string | null = null;

  setApiKey(apiKey: string) {
    this.apiKey = apiKey;
    localStorage.setItem("cognitude_api_key", apiKey);
  }

  clearApiKey() {
    this.apiKey = null;
    localStorage.removeItem("cognitude_api_key");
  }

  getApiKey(): string | null {
    return this.apiKey || localStorage.getItem("cognitude_api_key");
  }

  isAuthenticated(): boolean {
    return !!this.getApiKey();
  }

  // Auth (mocked)
  async register(name: string): Promise<Organization> {
    // return a fake organization with a generated api_key
    const now = new Date().toISOString();
    return {
      id: Math.floor(Math.random() * 10000) + 100,
      name,
      api_key: `mock-${Math.random().toString(36).slice(2, 12)}`,
      created_at: now,
    };
  }

  // Providers
  async getProviders(): Promise<Provider[]> {
    const data = await fetchJson<any[]>("providers");
    // normalize to Provider shape expected by the frontend where possible
    return data.map((p) => ({
      id: p.id,
      organization_id: p.organization_id || 1,
      provider: p.provider,
      api_key: p.masked_api_key || "sk-mock",
      priority: p.priority || 0,
      enabled: !!p.enabled,
      created_at: p.created_at || new Date().toISOString(),
      updated_at: p.updated_at,
    }));
  }

  async getProvider(providerId: number): Promise<Provider> {
    const providers = await this.getProviders();
    const found = providers.find((p) => p.id === providerId);
    if (!found) throw new Error("Provider not found (mock)");
    return found;
  }

  async createProvider(provider: ProviderCreate): Promise<Provider> {
    return {
      id: Math.floor(Math.random() * 10000) + 200,
      organization_id: 1,
      provider: provider.provider,
      api_key: provider.api_key,
      priority: provider.priority || 0,
      enabled: provider.enabled ?? true,
      created_at: new Date().toISOString(),
    } as Provider;
  }

  async updateProvider(
    providerId: number,
    update: ProviderUpdate
  ): Promise<Provider> {
    const existing = await this.getProvider(providerId);
    return {
      ...existing,
      ...update,
      updated_at: new Date().toISOString(),
    } as Provider;
  }

  async deleteProvider(providerId: number): Promise<{ message: string }> {
    return { message: `Mock deleted provider ${providerId}` };
  }

  // Chat completions
  async chatCompletion(
    request: ChatCompletionRequest
  ): Promise<ChatCompletionResponse> {
    const sample = await fetchJson<any>("chat_completion_sample");
    // adapt sample to ChatCompletionResponse expected by frontend types
    const resp: ChatCompletionResponse = {
      id: sample.id,
      object: sample.object || "chat.completion",
      created: sample.created || Math.floor(Date.now() / 1000),
      model: sample.model || request.model || "gpt-3.5-turbo",
      choices: sample.choices || [
        {
          index: 0,
          message: { role: "assistant", content: "Mock response" },
          finish_reason: "stop",
        },
      ],
      usage: sample.usage || {
        prompt_tokens: 0,
        completion_tokens: 0,
        total_tokens: 0,
      },
      x_cognitude: {
        cached: sample.cached || false,
        cost: sample.cost_usd || 0,
        provider: sample.provider || "mock",
      },
    };
    return resp;
  }

  async smartCompletion(
    request: Omit<ChatCompletionRequest, "model">
  ): Promise<ChatCompletionResponse> {
    // simply reuse chatCompletion mock
    return this.chatCompletion({ ...(request as any), model: "smart-mock" });
  }

  // Analytics
  async getUsageStats(_params?: any): Promise<UsageStats> {
    const raw = await fetchJson<any>("usage_stats");
    // map raw fields into the frontend UsageStats shape
    const cache_hits = raw.usage_by_day
      ? raw.usage_by_day.reduce(
          (s: number, d: any) => s + (d.cached_requests || 0),
          0
        )
      : 0;
    const breakdown = (raw.usage_by_provider || []).map((p: any) => ({
      provider: p.provider,
      requests: p.requests,
      cost: p.cost,
      tokens: p.total_tokens || 0,
    }));
    const daily_usage = (raw.usage_by_day || []).map((d: any) => ({
      date: d.date,
      requests: d.requests,
      cost: d.cost,
    }));
    const mapped: UsageStats = {
      total_requests: raw.total_requests || 0,
      total_cost: raw.total_cost || 0,
      cache_hits,
      cache_hit_rate: raw.cache_hit_rate || 0,
      cost_savings: raw.estimated_savings_usd || 0,
      breakdown,
      daily_usage,
    };
    return mapped;
  }

  async getRecommendations(): Promise<RecommendationsResponse> {
    // return a couple of canned recommendations
    return {
      recommendations: [
        {
          type: "cache",
          title: "Cache repeated prompts",
          description: "Enable caching for duplicate prompts to save cost.",
          potential_savings: 120.5,
          priority: "high",
        },
        {
          type: "model",
          title: "Use cheaper model for simple tasks",
          description: "Route classification to gpt-3.5.",
          potential_savings: 45.0,
          priority: "medium",
        },
      ],
      total_potential_savings: 165.5,
    };
  }

  // Cache
  async getCacheStats(): Promise<CacheStats> {
    const raw = await fetchJson<any>("cache_stats");
    // construct a simple CacheStats structure expected by types (redis/postgres breakdown)
    return {
      redis: {
        hits: raw.total_hits || 0,
        misses: Math.max(0, (raw.total_entries || 0) - (raw.total_hits || 0)),
        hit_rate: raw.hit_rate || 0,
        total_keys: raw.total_entries || 0,
        memory_usage_mb: 12.3,
      },
      postgresql: {
        total_cached_responses: raw.total_entries || 0,
        cost_savings: raw.estimated_savings_usd || 0,
        oldest_cache_entry: new Date().toISOString(),
      },
      lifetime_savings: {
        total_cost_saved: raw.estimated_savings_usd || 0,
        requests_served_from_cache: Math.floor((raw.total_hits || 0) / 1) || 0,
      },
    };
  }

  async clearCache(_request?: CacheClearRequest): Promise<CacheClearResponse> {
    return {
      message: "Mock: cache cleared",
      redis_keys_deleted: 123,
      postgresql_rows_deleted: 12,
    };
  }

  // Alerts
  async getAlertChannels(): Promise<AlertChannel[]> {
    const raw = await fetchJson<any>("alerts");
    return (raw.channels || []).map((c: any, i: number) => ({
      id: c.id || i + 1,
      organization_id: 1,
      channel_type: c.channel_type,
      configuration: c.configuration,
      enabled: c.is_active ?? true,
      created_at: c.created_at || new Date().toISOString(),
    }));
  }

  async createAlertChannel(channel: AlertChannelCreate): Promise<AlertChannel> {
    return {
      id: Math.floor(Math.random() * 10000) + 500,
      organization_id: 1,
      channel_type: channel.channel_type,
      configuration: channel.configuration,
      enabled: true,
      created_at: new Date().toISOString(),
    };
  }

  async updateAlertChannel(
    channelId: number,
    update: Partial<AlertChannelCreate>
  ): Promise<AlertChannel> {
    const channels = await this.getAlertChannels();
    const found = channels[0];
    return { ...found, ...update, id: channelId, created_at: found.created_at };
  }

  async deleteAlertChannel(channelId: number): Promise<{ message: string }> {
    return { message: `Mock deleted alert channel ${channelId}` };
  }

  async getAlertConfig(): Promise<AlertConfig> {
    const raw = await fetchJson<any>("alerts");
    const cfg = (raw.configs && raw.configs[0]) || {};
    return {
      id: cfg.id || 1,
      organization_id: 1,
      cost_threshold_daily: cfg.threshold_usd || undefined,
      enabled: cfg.enabled ?? true,
      created_at: cfg.created_at,
      updated_at: cfg.updated_at,
    } as AlertConfig;
  }

  async updateAlertConfig(config: AlertConfig): Promise<AlertConfig> {
    return { ...config, updated_at: new Date().toISOString() };
  }

  // Rate limits
  async getRateLimitConfig(): Promise<RateLimitConfig> {
    const raw = await fetchJson<any>("rate_limits");
    return raw.config as RateLimitConfig;
  }

  async updateRateLimitConfig(
    config: RateLimitUpdate
  ): Promise<RateLimitConfig> {
    const current = await this.getRateLimitConfig();
    return {
      ...current,
      ...config,
      updated_at: new Date().toISOString(),
    } as RateLimitConfig;
  }

  // Error helper
  handleError(_error: unknown): string {
    return "Mock error";
  }
}

export const mockApi = new MockCognitudeAPI();
export default mockApi;
