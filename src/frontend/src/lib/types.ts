// Theme
export type Theme = 'dark' | 'light';

// Time ranges
export type TimeRange = 'week' | 'month' | 'quarter' | 'ytd';
export type Granularity = 'hour' | 'day' | 'week';
export type FindingType = 'secret' | 'pii' | 'slopsquat' | 'all';
export type Severity = 'critical' | 'high' | 'medium';
export type FindingStatus = 'open' | 'acknowledged' | 'resolved';
export type AlertStatus = 'new' | 'acknowledged' | 'resolved';
export type AlertType = 'secret' | 'pii' | 'slopsquat' | 'anomaly';
export type ComplianceStatus = 'compliant' | 'partial' | 'non_compliant';
export type RiskLevel = 'low' | 'medium' | 'high';

// DashboardSummary
export interface DashboardSummary {
  period: string;
  generatedAt: string;
  metrics: {
    totalCost: number;
    totalEvents: number;
    totalTokens: number;
    totalDepartments: number;
    totalModels: number;
  };
  findings: {
    totalFindings: number;
    criticalCount: number;
    highCount: number;
    mediumCount: number;
    categoryCounts: {
      secrets: number;
      pii: number;
      slopsquat: number;
    };
  };
  compliance: {
    complianceScore: number;
    status: 'green' | 'yellow' | 'red';
  };
  anomalies: number;
  topDepartments: Array<{ department: string; cost: number; events: number }>;
}

// ComplianceScore
export interface ComplianceScore {
  overallScore: number;
  status: ComplianceStatus;
  auditPillars: Array<{
    check: string;
    description: string;
    compliancePercentage: number;
    recordsCovering: number;
    totalRecords: number;
  }>;
  lastAudited: string;
}

// CostBucket
export interface CostBucket {
  key: string;
  cost: number;
  sessions: number;
  avgCostPerSession: number;
  events: number;
  tokens: number;
  costPerToken: number;
  trivialPercentage: number;
  privatePercentage: number;
}

// UsageBucket
export interface UsageBucket {
  key: string;
  events: number;
  tokens: number;
  sessions: number;
  averageTokensPerSession: number;
  averageWordCountPerSession: number;
}

// LeakCountSummary
export interface LeakCountSummary {
  model: string;
  category: 'secret' | 'pii' | 'slopsquat';
  leakCount: number;
}

// DepartmentStats
export interface DepartmentStats {
  department: string;
  cost: number;
  events: number;
  tokens: number;
  leakCount: number;
  criticalLeaks: number;
  trivialPercentage: number;
  privatePercentage: number;
  complianceScore: number;
  topModels: string[];
  riskScore: number;
}

// ModelMetrics
export interface ModelMetrics {
  model: string;
  provider: string;
  usage: { events: number; tokens: number; sessions: number };
  costs: { total: number; perToken: number; perSession: number };
  risk: { leakCount: number; leakRate: number; hallucRate: number };
  costPerQualityRatio: number;
}

// Finding
export interface Finding {
  id: string;
  type: FindingType;
  severity: Severity;
  category: string;
  detectedAt: string;
  department: string;
  user: string;
  provider: string;
  conversationId: string;
  status: FindingStatus;
  matchValue: string;
  contextPreview: string;
  confidence: number;
}

// FindingDetail extends Finding
export interface FindingDetail extends Finding {
  fullContext: string;
  remediationHistory: Array<{
    timestamp: string;
    oldStatus: string;
    newStatus: string;
    notes: string;
    actor: string;
  }>;
  relatedFindings: string[];
  duplicateCount: number;
}

// SeverityBucket
export interface SeverityBucket {
  critical: number;
  high: number;
  medium: number;
}

// SeverityDistribution
export interface SeverityDistribution {
  secrets: SeverityBucket;
  pii: SeverityBucket;
  slopsquat: SeverityBucket;
}

// SlopsquattingStats
export interface SlopsquattingStats {
  provider: string;
  hallucCount: number;
  hallucRate: number;
  fabricationTypes: {
    packages: number;
    endpoints: number;
    cliTools: number;
    rbacRoles: number;
  };
  topHallucinations: Array<{ name: string; type: string; count: number }>;
}

// ContextExposureSession
export interface ContextExposureSession {
  sessionId: string;
  riskScore: number;
  department: string;
  provider: string;
  filesAccessedCount: number;
  sensitiveFileTypes: string[];
  duration: string;
  tokenCount: number;
  foundFindings: number;
  exposureBreakdown: Record<string, number>;
}

// ProviderComplianceMetadata
export interface ProviderComplianceMetadata {
  provider: string;
  regions: string[];
  dataRetention: { days: number; policy: string };
  hasGDPRDPA: boolean;
  hasBizAssociate: boolean;
  jurisdictions: string[];
  riskLevel: RiskLevel;
  recommendations: string[];
}

// DataFlow (Sankey)
export interface DataFlowResponse {
  nodes: Array<{ id: string; label: string; type: 'department' | 'tool' | 'model' | 'region' }>;
  links: Array<{ source: string; target: string; value: number }>;
}

// TimeSeries
export interface TimeSeriesResponse {
  metric: string;
  granularity: string;
  data: Array<{ timestamp: string; value: number }>;
}

// Alert
export interface Alert {
  id: string;
  type: AlertType;
  severity: Severity;
  title: string;
  message: string;
  timestamp: string;
  department: string;
  provider: string;
  conversationId: string;
  status: AlertStatus;
  actionUrl: string;
}

// ScatterPoint
export interface ScatterPoint {
  conversationId: string;
  tokenCount: number;
  findingCount: number;
  provider: string;
  cost: number;
  department: string;
  severity: Severity;
}

// Recommendation
export interface Recommendation {
  id: string;
  category: 'cost_optimization' | 'risk_reduction' | 'compliance_improvement' | 'performance';
  title: string;
  description: string;
  impact: {
    estimatedSavings: number;
    riskReduction: RiskLevel;
    effortToImplement: 'trivial' | 'easy' | 'medium' | 'hard';
  };
  actions: string[];
}

// ShadowAI
export interface ShadowAIResponse {
  approvedProviders: string[];
  violations: Array<{
    provider: string;
    eventCount: number;
    departments: string[];
    totalCost: number;
  }>;
}

// AnomalyAlert
export interface AnomalyAlert {
  department: string;
  period: string;
  metric: string;
  baselineValue: number;
  observedValue: number;
  zScore: number;
  severity: string;
  explanation: string;
}

// AuditLogEntry
export interface AuditLogEntry {
  id: string;
  timestamp: string;
  action: string;
  findingId: string;
  actor: string;
  details: Record<string, unknown>;
  complianceRelevant: boolean;
}

// CostAnalyticsResponse
export interface CostAnalyticsResponse {
  costBasis: string;
  dimension: string;
  items: CostBucket[];
  total: number;
  totalRecords: number;
  trendSparklines: Record<string, number[]>;
}

// FindingsResponse
export interface FindingsResponse {
  items: Finding[];
  total: number;
  offset: number;
  limit: number;
}
