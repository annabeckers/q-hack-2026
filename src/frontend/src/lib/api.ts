import * as types from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const DASHBOARD_BASE = `${API_BASE_URL}/api/v1/dashboard`;

interface ApiError {
  status: number;
  message: string;
  data?: unknown;
}

class ApiClient {
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${DASHBOARD_BASE}${endpoint}`;

    try {
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
          // Response body not JSON, keep error as is
        }

        throw error;
      }

      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw {
        status: 0,
        message: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  private buildQueryString(params?: Record<string, string | number | boolean>): string {
    if (!params) return '';
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      query.append(key, String(value));
    });
    const str = query.toString();
    return str ? `?${str}` : '';
  }

  // Dashboard
  async getDashboardSummary(
    timeRange?: types.TimeRange,
    department?: string
  ): Promise<types.DashboardSummary> {
    const params: Record<string, string | number | boolean> = {};
    if (timeRange) params.timeRange = timeRange;
    if (department) params.department = department;
    return this.request(`/dashboard${this.buildQueryString(params)}`);
  }

  // Compliance
  async getComplianceGauge(department?: string): Promise<types.ComplianceScore> {
    const params: Record<string, string | number | boolean> = {};
    if (department) params.department = department;
    return this.request(`/compliance/gauge${this.buildQueryString(params)}`);
  }

  // Cost Analytics
  async getCostAnalytics(
    dimension: string,
    options?: {
      timeRange?: types.TimeRange;
      department?: string;
      model?: string;
      limit?: number;
    }
  ): Promise<types.CostAnalyticsResponse> {
    const params: Record<string, string | number | boolean> = { dimension };
    if (options?.timeRange) params.timeRange = options.timeRange;
    if (options?.department) params.department = options.department;
    if (options?.model) params.model = options.model;
    if (options?.limit) params.limit = options.limit;
    return this.request(`/analytics/cost${this.buildQueryString(params)}`);
  }

  // Usage Analytics
  async getUsageAnalytics(
    dimension: string,
    options?: {
      timeRange?: types.TimeRange;
      department?: string;
      model?: string;
      limit?: number;
    }
  ): Promise<{ items: types.UsageBucket[]; total: number }> {
    const params: Record<string, string | number | boolean> = { dimension };
    if (options?.timeRange) params.timeRange = options.timeRange;
    if (options?.department) params.department = options.department;
    if (options?.model) params.model = options.model;
    if (options?.limit) params.limit = options.limit;
    return this.request(`/analytics/usage${this.buildQueryString(params)}`);
  }

  // Department Analytics
  async getDepartmentAnalytics(sortBy?: string): Promise<types.DepartmentStats[]> {
    const params: Record<string, string | number | boolean> = {};
    if (sortBy) params.sortBy = sortBy;
    return this.request(`/analytics/department${this.buildQueryString(params)}`);
  }

  // Model Comparison
  async getModelComparison(department?: string): Promise<types.ModelMetrics[]> {
    const params: Record<string, string | number | boolean> = {};
    if (department) params.department = department;
    return this.request(`/analytics/models${this.buildQueryString(params)}`);
  }

  // Findings
  async getFindings(options?: {
    department?: string;
    provider?: string;
    severity?: types.Severity;
    type?: types.FindingType;
    status?: types.FindingStatus;
    offset?: number;
    limit?: number;
  }): Promise<types.FindingsResponse> {
    const params: Record<string, string | number | boolean> = {};
    if (options?.department) params.department = options.department;
    if (options?.provider) params.provider = options.provider;
    if (options?.severity) params.severity = options.severity;
    if (options?.type) params.type = options.type;
    if (options?.status) params.status = options.status;
    if (options?.offset) params.offset = options.offset;
    if (options?.limit) params.limit = options.limit;
    return this.request(`/findings${this.buildQueryString(params)}`);
  }

  // Finding Detail
  async getFindingDetail(id: string): Promise<types.FindingDetail> {
    return this.request(`/findings/${id}`);
  }

  // Update Finding Status
  async updateFindingStatus(
    id: string,
    status: types.FindingStatus,
    notes?: string
  ): Promise<{ success: boolean; finding: types.Finding }> {
    return this.request(`/findings/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, notes }),
    });
  }

  // Severity Distribution
  async getSeverityDistribution(
    department?: string,
    provider?: string
  ): Promise<types.SeverityDistribution> {
    const params: Record<string, string | number | boolean> = {};
    if (department) params.department = department;
    if (provider) params.provider = provider;
    return this.request(`/analytics/severity${this.buildQueryString(params)}`);
  }

  // Leak Counts
  async getLeakCounts(
    model?: string,
    category?: types.FindingType
  ): Promise<types.LeakCountSummary[]> {
    const params: Record<string, string | number | boolean> = {};
    if (model) params.model = model;
    if (category) params.category = category;
    return this.request(`/analytics/leaks${this.buildQueryString(params)}`);
  }

  // Slopsquatting by Model
  async getSlopsquattingByModel(
    dimension?: string,
    sortBy?: string
  ): Promise<types.SlopsquattingStats[]> {
    const params: Record<string, string | number | boolean> = {};
    if (dimension) params.dimension = dimension;
    if (sortBy) params.sortBy = sortBy;
    return this.request(`/analytics/slopsquat${this.buildQueryString(params)}`);
  }

  // Context Risk
  async getContextRisk(limit?: number): Promise<types.ContextExposureSession[]> {
    const params: Record<string, string | number | boolean> = {};
    if (limit) params.limit = limit;
    return this.request(`/risk/context${this.buildQueryString(params)}`);
  }

  // File Exposure
  async getFileExposure(): Promise<{
    filesAtRisk: number;
    sensitiveTypes: string[];
    exposureByDepartment: Record<string, number>;
  }> {
    return this.request('/risk/file-exposure');
  }

  // Duplicate Secrets
  async getDuplicateSecrets(minUsers?: number): Promise<{
    duplicateCount: number;
    secrets: Array<{ value: string; userCount: number; departments: string[] }>;
  }> {
    const params: Record<string, string | number | boolean> = {};
    if (minUsers) params.minUsers = minUsers;
    return this.request(`/findings/duplicates${this.buildQueryString(params)}`);
  }

  // Audit Trail
  async getAuditTrail(options?: {
    action?: string;
    actor?: string;
    findingId?: string;
    limit?: number;
    offset?: number;
  }): Promise<{ entries: types.AuditLogEntry[]; total: number }> {
    const params: Record<string, string | number | boolean> = {};
    if (options?.action) params.action = options.action;
    if (options?.actor) params.actor = options.actor;
    if (options?.findingId) params.findingId = options.findingId;
    if (options?.limit) params.limit = options.limit;
    if (options?.offset) params.offset = options.offset;
    return this.request(`/audit/trail${this.buildQueryString(params)}`);
  }

  // Data Flow
  async getDataFlow(department?: string): Promise<types.DataFlowResponse> {
    const params: Record<string, string | number | boolean> = {};
    if (department) params.department = department;
    return this.request(`/analytics/dataflow${this.buildQueryString(params)}`);
  }

  // Provider DPA
  async getProviderDPA(): Promise<types.ProviderComplianceMetadata[]> {
    return this.request('/compliance/providers');
  }

  // Time Series
  async getTimeSeries(
    metric: string,
    granularity?: types.Granularity,
    options?: {
      timeRange?: types.TimeRange;
      department?: string;
      provider?: string;
    }
  ): Promise<types.TimeSeriesResponse> {
    const params: Record<string, string | number | boolean> = { metric };
    if (granularity) params.granularity = granularity;
    if (options?.timeRange) params.timeRange = options.timeRange;
    if (options?.department) params.department = options.department;
    if (options?.provider) params.provider = options.provider;
    return this.request(`/analytics/timeseries${this.buildQueryString(params)}`);
  }

  // Anomalies
  async getAnomalies(department?: string, zscore?: number): Promise<types.AnomalyAlert[]> {
    const params: Record<string, string | number | boolean> = {};
    if (department) params.department = department;
    if (zscore) params.zscore = zscore;
    return this.request(`/analytics/anomalies${this.buildQueryString(params)}`);
  }

  // Time Patterns
  async getTimePatterns(): Promise<{
    hourOfDay: Record<string, number>;
    dayOfWeek: Record<string, number>;
    peakHours: string[];
  }> {
    return this.request('/analytics/patterns');
  }

  // Complexity Scatter
  async getComplexityScatter(
    department?: string,
    provider?: string
  ): Promise<types.ScatterPoint[]> {
    const params: Record<string, string | number | boolean> = {};
    if (department) params.department = department;
    if (provider) params.provider = provider;
    return this.request(`/analytics/scatter${this.buildQueryString(params)}`);
  }

  // Alerts
  async getAlerts(options?: {
    department?: string;
    provider?: string;
    severity?: types.Severity;
    status?: types.AlertStatus;
    type?: types.AlertType;
    limit?: number;
    offset?: number;
  }): Promise<{ alerts: types.Alert[]; total: number }> {
    const params: Record<string, string | number | boolean> = {};
    if (options?.department) params.department = options.department;
    if (options?.provider) params.provider = options.provider;
    if (options?.severity) params.severity = options.severity;
    if (options?.status) params.status = options.status;
    if (options?.type) params.type = options.type;
    if (options?.limit) params.limit = options.limit;
    if (options?.offset) params.offset = options.offset;
    return this.request(`/alerts${this.buildQueryString(params)}`);
  }

  // Stream Alerts
  streamAlerts(severity?: types.Severity): EventSource {
    const params = severity ? `?severity=${severity}` : '';
    return new EventSource(`${DASHBOARD_BASE}/alerts/stream${params}`);
  }

  // Acknowledge Alert
  async acknowledgeAlert(id: string, notes?: string): Promise<{ success: boolean }> {
    return this.request(`/alerts/${id}/acknowledge`, {
      method: 'PATCH',
      body: JSON.stringify({ notes }),
    });
  }

  // Conversations
  async getConversations(options?: {
    department?: string;
    provider?: string;
    limit?: number;
    offset?: number;
  }): Promise<{
    conversations: Array<{
      id: string;
      department: string;
      provider: string;
      startTime: string;
      endTime: string;
      tokenCount: number;
      cost: number;
      findingCount: number;
    }>;
    total: number;
  }> {
    const params: Record<string, string | number | boolean> = {};
    if (options?.department) params.department = options.department;
    if (options?.provider) params.provider = options.provider;
    if (options?.limit) params.limit = options.limit;
    if (options?.offset) params.offset = options.offset;
    return this.request(`/conversations${this.buildQueryString(params)}`);
  }

  // Conversation Detail
  async getConversationDetail(id: string): Promise<{
    id: string;
    department: string;
    provider: string;
    startTime: string;
    endTime: string;
    tokenCount: number;
    cost: number;
    messages: Array<{ role: string; content: string }>;
    findings: types.Finding[];
  }> {
    return this.request(`/conversations/${id}`);
  }

  // Top Entities
  async getTopEntities(options?: {
    entityType?: string;
    timeRange?: types.TimeRange;
    limit?: number;
  }): Promise<{
    entities: Array<{ name: string; count: number; risk: number }>;
  }> {
    const params: Record<string, string | number | boolean> = {};
    if (options?.entityType) params.entityType = options.entityType;
    if (options?.timeRange) params.timeRange = options.timeRange;
    if (options?.limit) params.limit = options.limit;
    return this.request(`/analytics/entities${this.buildQueryString(params)}`);
  }

  // Shadow AI
  async getShadowAI(): Promise<types.ShadowAIResponse> {
    return this.request('/compliance/shadow-ai');
  }

  // Recommendations
  async getRecommendations(
    department?: string
  ): Promise<types.Recommendation[]> {
    const params: Record<string, string | number | boolean> = {};
    if (department) params.department = department;
    return this.request(`/recommendations${this.buildQueryString(params)}`);
  }
}

export const apiClient = new ApiClient();
