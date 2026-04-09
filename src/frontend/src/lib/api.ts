import type * as types from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const DASHBOARD_BASE = `${API_BASE_URL}/api/v1/dashboard`;

interface ApiError {
  status: number;
  message: string;
  data?: unknown;
}

class ApiClient {
  private async request<T>(
    endpoint: string,
    options?: RequestInit,
    base?: string
  ): Promise<T> {
    const url = `${base ?? DASHBOARD_BASE}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error: ApiError = {
        status: response.status,
        message: `API error: ${response.statusText}`,
      };
      try {
        error.data = await response.json();
      } catch {
        // Response body not JSON
      }
      throw error;
    }

    return await response.json();
  }

  private qs(params?: Record<string, string | number | boolean | undefined>): string {
    if (!params) return '';
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) query.append(key, String(value));
    });
    const str = query.toString();
    return str ? `?${str}` : '';
  }

  // ── Dashboard Summary ──────────────────────────────────────────────
  async getDashboardSummary(
    timeRange?: string,
    department?: string
  ): Promise<types.DashboardSummary> {
    return this.request(`/summary${this.qs({ time_range: timeRange, department })}`);
  }

  // ── Compliance ─────────────────────────────────────────────────────
  async getComplianceGauge(department?: string): Promise<types.ComplianceScore> {
    return this.request(`/summary/compliance-gauge${this.qs({ department })}`);
  }

  // ── Cost Analytics ─────────────────────────────────────────────────
  async getCostAnalytics(
    dimension: string,
    options?: {
      costBasis?: string;
      department?: string;
      limit?: number;
      startDate?: string;
      endDate?: string;
    }
  ): Promise<types.CostAnalyticsResponse> {
    return this.request(
      `/analytics/cost${this.qs({
        dimension,
        cost_basis: options?.costBasis ?? 'per_session',
        department: options?.department,
        limit: options?.limit,
        startDate: options?.startDate,
        endDate: options?.endDate,
      })}`
    );
  }

  // ── Usage Analytics ────────────────────────────────────────────────
  async getUsageAnalytics(
    dimension: string,
    options?: {
      metric?: string;
      department?: string;
      startDate?: string;
      endDate?: string;
    }
  ): Promise<{ items: types.UsageBucket[]; total: number }> {
    return this.request(
      `/analytics/usage${this.qs({
        dimension,
        metric: options?.metric ?? 'avgWordCountPerSession',
        department: options?.department,
        startDate: options?.startDate,
        endDate: options?.endDate,
      })}`
    );
  }

  // ── Model Comparison ───────────────────────────────────────────────
  async getModelComparison(department?: string): Promise<types.ModelMetrics[]> {
    return this.request(`/analytics/model-comparison${this.qs({ department })}`);
  }

  // ── Findings ───────────────────────────────────────────────────────
  async getFindings(options?: {
    type?: string;
    severity?: string;
    status?: string;
    department?: string;
    provider?: string;
    limit?: number;
    offset?: number;
  }): Promise<types.FindingsResponse> {
    return this.request(
      `/security/findings${this.qs({
        type: options?.type ?? 'all',
        severity: options?.severity ?? 'all',
        status: options?.status ?? 'open',
        department: options?.department,
        provider: options?.provider,
        limit: options?.limit,
        offset: options?.offset,
      })}`
    );
  }

  // ── Finding Detail ─────────────────────────────────────────────────
  async getFindingDetail(id: string): Promise<types.FindingDetail> {
    return this.request(`/security/findings/${id}`);
  }

  // ── Update Finding Status ──────────────────────────────────────────
  async updateFindingStatus(
    id: string,
    status: string,
    notes?: string
  ): Promise<unknown> {
    return this.request(`/security/findings/${id}/remediation`, {
      method: 'PATCH',
      body: JSON.stringify({ status, notes }),
    });
  }

  // ── Severity Distribution ──────────────────────────────────────────
  async getSeverityDistribution(
    department?: string,
    provider?: string
  ): Promise<types.SeverityDistribution> {
    return this.request(`/security/severity-distribution${this.qs({ department, provider })}`);
  }

  // ── Leak Counts ────────────────────────────────────────────────────
  async getLeakCounts(
    model?: string,
    category?: string,
    department?: string
  ): Promise<types.LeakCountSummary[]> {
    return this.request(`/security/leak-counts${this.qs({ model, category, department })}`);
  }

  // ── Slopsquatting ──────────────────────────────────────────────────
  async getSlopsquattingByModel(
    dimension?: string,
    sortBy?: string,
    department?: string
  ): Promise<types.SlopsquattingStats[]> {
    return this.request(
      `/security/slopsquatting${this.qs({ dimension: dimension ?? 'model', sortBy: sortBy ?? 'count', department })}`
    );
  }

  // ── Duplicate Secrets ──────────────────────────────────────────────
  async getDuplicateSecrets(minUsers?: number, department?: string): Promise<unknown> {
    return this.request(`/security/duplicate-secrets${this.qs({ minUsers, department })}`);
  }

  // ── Time Series ────────────────────────────────────────────────────
  async getTimeSeries(
    metric: string,
    granularity?: string,
    options?: { department?: string; startDate?: string; endDate?: string }
  ): Promise<types.TimeSeriesResponse> {
    return this.request(
      `/trends/timeseries${this.qs({
        metric,
        granularity: granularity ?? 'day',
        department: options?.department,
        startDate: options?.startDate,
        endDate: options?.endDate,
      })}`
    );
  }

  // ── Anomalies ──────────────────────────────────────────────────────
  async getAnomalies(department?: string, zscore?: number): Promise<types.AnomalyAlert[]> {
    return this.request(`/trends/anomalies${this.qs({ department, zscore })}`);
  }

  // ── Time Patterns ──────────────────────────────────────────────────
  async getTimePatterns(department?: string): Promise<unknown> {
    return this.request(`/trends/patterns-by-time${this.qs({ department })}`);
  }

  // ── Complexity Scatter ─────────────────────────────────────────────
  async getComplexityScatter(
    department?: string,
    provider?: string
  ): Promise<types.ScatterPoint[]> {
    return this.request(`/trends/complexity-scatter${this.qs({ department, provider })}`);
  }

  // ── Alerts ─────────────────────────────────────────────────────────
  async getAlerts(options?: {
    severity?: string;
    type?: string;
    department?: string;
    limit?: number;
  }): Promise<types.Alert[]> {
    return this.request(
      `/alerts${this.qs({
        severity: options?.severity,
        type: options?.type,
        department: options?.department,
        limit: options?.limit ?? 50,
      })}`
    );
  }

  // ── Stream Alerts (SSE) ────────────────────────────────────────────
  streamAlerts(severity?: string): EventSource {
    const params = severity ? `?severity=${severity}` : '';
    return new EventSource(`${DASHBOARD_BASE}/alerts/stream${params}`);
  }

  // ── Acknowledge Alert ──────────────────────────────────────────────
  async acknowledgeAlert(id: string, notes?: string): Promise<unknown> {
    return this.request(`/alerts/${id}/acknowledge`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    });
  }

  // ── Recommendations (separate router prefix) ──────────────────────
  async getRecommendations(department?: string): Promise<types.Recommendation[]> {
    return this.request(
      `${this.qs({ department })}`,
      undefined,
      `${API_BASE_URL}/api/v1/recommendations`
    );
  }

  // ── Data Flow (compliance) ─────────────────────────────────────────
  async getDataFlow(department?: string): Promise<types.DataFlowResponse> {
    return this.request(`/compliance/data-flow${this.qs({ department })}`);
  }

  // ── Provider DPA ───────────────────────────────────────────────────
  async getProviderDPA(): Promise<types.ProviderComplianceMetadata[]> {
    return this.request('/compliance/provider-dpa');
  }

  // ── Shadow AI ──────────────────────────────────────────────────────
  async getShadowAI(): Promise<types.ShadowAIResponse> {
    return this.request('/explorer/shadow-ai');
  }

  // ── Context Risk ───────────────────────────────────────────────────
  async getContextRisk(limit?: number): Promise<types.ContextExposureSession[]> {
    return this.request(`/security/context-risk${this.qs({ limit })}`);
  }
}

export const apiClient = new ApiClient();
