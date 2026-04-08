# Dashboard API Integration Guide

**For Frontend Developers** | Generated 2026-04-08

This guide maps the OpenAPI specification (`openapi.yaml`/`openapi.json`) to the frontend features described in `evaluation.md`.

---

## Quick Start

### 1. Base Configuration

```typescript
// config/api.ts
export const API_CONFIG = {
  baseURL: process.env.VITE_API_URL || 'http://localhost:8000/api/v1/dashboard',
  timeout: 10000,
  headers: {
    'Authorization': `Bearer ${getToken()}`, // JWT from auth service
    'Accept': 'application/json',
  }
};
```

### 2. API Client Setup (Recommended: TanStack Query)

```typescript
// hooks/useApi.ts
import { useQuery, useMutation } from '@tanstack/react-query';
import axios from 'axios';

const apiClient = axios.create({
  baseURL: API_CONFIG.baseURL,
  headers: API_CONFIG.headers,
});

// Example: Fetch summary
export const useDashboardSummary = (timeRange: string) => {
  return useQuery({
    queryKey: ['dashboard', 'summary', timeRange],
    queryFn: () => apiClient.get('/summary', { params: { time_range: timeRange } }),
    refetchInterval: 30000, // Auto-refresh every 30s
  });
};
```

---

## Feature → Endpoint Mapping

### 📊 Main Dashboard View

| Feature | Endpoint | Priority |
|---------|----------|----------|
| **Costs** (card) | `GET /analytics/cost` | 🔴 P0 |
| **Model usage (message counts)** | `GET /analytics/usage` | 🔴 P0 |
| **Leaks by severity** | `GET /security/severity-distribution` | 🔴 P0 |
| **Compliance gauge** | `GET /summary/compliance-gauge` | 🔴 P0 |
| **Libraries (slopsquatting table)** | `GET /security/slopsquatting` | 🟡 P1 |
| **Scatter plot (Complexity vs Leak)** | `GET /explorer/complexity-scatter` | 🟡 P1 |

### 🔒 Security Findings Panel

| Feature | Endpoint | Implementation |
|---------|----------|-----------------|
| All findings list | `GET /security/findings` | Paginated table with filters |
| Find by ID | `GET /security/findings/{id}` | Modal/detail view on row click |
| Update status | `PATCH /security/findings/{id}/remediation` | Bulk action or per-finding |
| Drill-down context | Embedded in `FindingDetail.fullContext` | ±1000 char context window |

**Example Query:**
```typescript
const { data: findings } = useQuery({
  queryKey: ['findings', { type: 'all', severity, status, limit: 100 }],
  queryFn: () => apiClient.get('/security/findings', {
    params: {
      type: 'all',
      severity: severity, // 'critical' | 'high' | 'medium' | 'all'
      status: 'open',
      limit: 100,
    }
  }),
});
```

### 📈 Cost & Usagereakdowns

| Feature | Endpoint |
|---------|----------|
| By department | `GET /analytics/department` |
| By model | `GET /analytics/model-comparison` |
| By tool | `GET /analytics/cost?dimension=tool` |
| By region | `GET /analytics/cost?dimension=region` |

Each supports time-range filtering and sparkline trend data for the last 90 days.

### 🔴 Critical Additions (per evaluation.md)

#### 1. Severity Distribution (P0)
```typescript
const { data } = useQuery({
  queryKey: ['findings', 'severity'],
  queryFn: () => apiClient.get('/security/severity-distribution'),
});
// Returns: { secrets: { critical: 3, high: 8, medium: 12 }, pii: {...}, slopsquat: {...} }
```

**Display as:**
- Vertical bar chart per category
- Color-coded (red=critical, orange=high, yellow=medium)

#### 2. Slopsquatting Rate by Model (P0)
```typescript
const { data: slopsquatting } = useQuery({
  queryKey: ['findings', 'slopsquatting'],
  queryFn: () => apiClient.get('/security/slopsquatting'),
});
// Returns: [{provider: "chatgpt-4o", hallucCount: 34, hallucRate: 12.5, fabricationTypes: {...}}]
```

**Display as:**
- Bar chart: models ranked by hallucination rate
- Show fabrication breakdown (packages vs endpoints vs tools)

#### 3. Compliance Gauge (P0)
```typescript
const { data: compliance } = useQuery({
  queryKey: ['compliance', 'gauge'],
  queryFn: () => apiClient.get('/summary/compliance-gauge'),
});
// Returns: { overallScore: 76, status: 'yellow', auditPillars: [{check: 'purpose_logged', compliancePercentage: 80}] }
```

**Display as:**
- Large radial gauge (0-100), color-coded
- Breakdown cards below: purpose logged (80%), region logged (75%), etc.

#### 4. Department Attribution (P1)
```typescript
const { data: deptStats } = useQuery({
  queryKey: ['analytics', 'department'],
  queryFn: () => apiClient.get('/analytics/department', { params: { sortBy: 'cost' } }),
});
// Returns: [{department: 'Eng', cost: 5000, leakCount: 42, complianceScore: 65}]
```

**Display as:**
- Sortable table or carousel
- Key insight: "Engineering: 80% of costs, 90% of leaks"

#### 5. Context Risk (P1)
```typescript
const { data: contextRisk } = useQuery({
  queryKey: ['security', 'context-risk'],
  queryFn: () => apiClient.get('/security/context-risk', { params: { limit: 10 } }),
});
// Returns: [{sessionId, riskScore: 87, filesAccessedCount: 23, sensitiveFileTypes: ['.env', '.pem']}]
```

**Display as:**
- List of top-10 riskiest sessions
- Color-coded risk score badge
- Show file types as tags

#### 6. Real-Time Alert Stream (P1 — "WOW" moment)
```typescript
// Use Server-Sent Events for live updates
const setupAlertStream = () => {
  const eventSource = new EventSource(`${API_URL}/alerts/stream?severity=critical`);
  eventSource.onmessage = (event) => {
    const alert = JSON.parse(event.data);
    // Show toast notification, update findings list live
    addAlertToast(alert);
  };
};
```

---

## Component Architecture

### Suggested Component Structure

```
src/
├── pages/
│   ├── Dashboard.tsx          # Main view (summary + panels)
│   ├── SecurityFindings.tsx    # Full findings explorer
│   ├── Compliance.tsx          # Compliance & audit trail
│   ├── Trends.tsx              # Time-series, anomalies
│   └── ConversationDetail.tsx  # Drill-down view
│
├── components/
│   ├── cards/
│   │   ├── CostCard.tsx        # .../analytics/cost
│   │   ├── UsageCard.tsx       # .../analytics/usage
│   │   ├── ComplianceGauge.tsx # .../summary/compliance-gauge
│   │   └── SeverityCard.tsx    # .../security/severity-distribution
│   │
│   ├── charts/
│   │   ├── CostTrendChart.tsx  # Line chart + sparkline
│   │   ├── ScatterPlot.tsx     # Complexity vs Risk
│   │   ├── HeatmapChart.tsx    # Time-of-day patterns
│   │   └── SankeyFlow.tsx      # Data flow visualization
│   │
│   ├── tables/
│   │   ├── FindingsTable.tsx   # /security/findings (paginated)
│   │   ├── DeptTable.tsx       # /analytics/department
│   │   └── ModelComparison.tsx # /analytics/model-comparison
│   │
│   ├── alerts/
│   │   ├── AlertFeed.tsx       # GET /alerts + SSE stream
│   │   └── AlertToast.tsx      # Inline notifications
│   │
│   └── modals/
│       ├── FindingDetail.tsx   # /security/findings/{id}
│       └── ConversationExplorer.tsx # /explorer/conversations/{id}
│
├── hooks/
│   ├── useApi.ts              # TanStack Query wrappers
│   ├── useAlertStream.ts      # SSE subscription
│   └── useFilters.ts          # Persistent filter state
│
└── services/
    ├── apiClient.ts           # Axios instance
    └── queryClient.ts         # TanStack Query config
```

---

## Implementation Phases

### 🔴 Phase 1 — Core Foundation (Hackathon MVP)

**Required for demo day:**

1. **Dashboard Summary**
   - Endpoint: `GET /summary`
   - Shows: cost, usage, top depts, compliance score, critical finding count
   - UI: 4-5 key metrics + sparklines

2. **Findings Table**
   - Endpoint: `GET /security/findings`
   - Shows: paginated list, severity color-coded, status badge
   - Actions: filter, sort, click for detail

3. **Severity Breakdown**
   - Endpoint: `GET /security/severity-distribution`
   - Shows: 3 stacked bar charts (secrets/pii/slopsquat)

4. **Model Comparison**
   - Endpoint: `GET /analytics/model-comparison`
   - Shows: table ranked by leak rate or cost-per-token

5. **Compliance Gauge**
   - Endpoint: `GET /summary/compliance-gauge`
   - Shows: large radial gauge + 5 audit pillar cards

### 🟡 Phase 2 — Intelligence Layer (Post-MVP)

1. **Real-Time Alert Stream**
   - Endpoint: `GET /alerts/stream` (SSE)
   - Shows: live feed of detected findings

2. **Scatter Plot**
   - Endpoint: `GET /explorer/complexity-scatter`
   - Shows: token count vs findings, colored by provider

3. **Time-Series Trends**
   - Endpoint: `GET /trends/timeseries`
   - Shows: 90-day cost/findings charts

4. **Anomaly Detection**
   - Endpoint: `GET /trends/anomalies`
   - Shows: week-over-week spikes flagged

5. **Department Drill-Down**
   - Endpoint: `GET /analytics/department`
   - Shows: per-dept metrics, sortable table

### 🟢 Phase 3 — Advanced Features (Post-launch)

1. **Conversation Explorer**
   - Endpoint: `GET /explorer/conversations` + `/explorer/conversations/{id}`
   - Shows: conversation list with findings, drill-down view

2. **Audit Trail**
   - Endpoint: `GET /compliance/audit-trail`
   - Shows: timeline of finding actions for compliance

3. **Data Flow Sankey**
   - Endpoint: `GET /compliance/data-flow`
   - Shows: dept → tool → model → region flow

4. **Shadow AI Detection**
   - Endpoint: `GET /explorer/shadow-ai`
   - Shows: unapproved provider usage

---

## Common Query Patterns

### A. Time-Range Filtering

Most endpoints support `startDate` and `endDate` (ISO 8601):

```typescript
const last30Days = () => {
  const now = new Date();
  const start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
  return { startDate: start.toISOString(), endDate: now.toISOString() };
};

const { data } = useQuery({
  queryKey: ['analytics', 'cost', 'month'],
  queryFn: () => apiClient.get('/analytics/cost', {
    params: { dimension: 'department', ...last30Days() }
  }),
});
```

### B. Pagination

```typescript
const [page, setPage] = useState(0);
const itemsPerPage = 50;

const { data: findings } = useQuery({
  queryKey: ['findings', page],
  queryFn: () => apiClient.get('/security/findings', {
    params: { limit: itemsPerPage, offset: page * itemsPerPage }
  }),
});
```

### C. Multi-Filter

```typescript
interface FindingsFilter {
  type?: 'secret' | 'pii' | 'slopsquat';
  severity?: 'critical' | 'high' | 'medium';
  status?: 'open' | 'acknowledged' | 'resolved';
  department?: string;
  provider?: string;
}

const getFindings = (filter: FindingsFilter) => {
  return apiClient.get('/security/findings', {
    params: filter,
  });
};
```

### D. Real-Time Updates

```typescript
// Polling approach (simpler for MVP)
const { data: alerts } = useQuery({
  queryKey: ['alerts', 'recent'],
  queryFn: () => apiClient.get('/alerts', { params: { limit: 50 } }),
  refetchInterval: 5000, // Refresh every 5 seconds
});

// SSE approach (production-ready)
useEffect(() => {
  const sse = new EventSource(`${API_URL}/alerts/stream?severity=critical`);
  sse.onmessage = (e) => handleNewAlert(JSON.parse(e.data));
  return () => sse.close();
}, []);
```

---

## Error Handling

All endpoints return standard error responses:

```typescript
interface ApiError {
  detail: string;
  code?: string;
  fields?: Record<string, string[]>;
}

// Usage in React Query
const { data, error, isLoading } = useQuery({
  queryKey: ['findings'],
  queryFn: async () => {
    try {
      const res = await apiClient.get('/security/findings');
      return res.data;
    } catch (err: any) {
      if (err.response?.status === 400) {
        // Bad request — show validation errors
        const apiErr: ApiError = err.response.data;
        throwError(`Invalid params: ${apiErr.detail}`);
      } else if (err.response?.status === 401) {
        // Re-auth required
        redirectToLogin();
      }
      throw err;
    }
  },
});
```

---

## Authentication

All endpoints require either:

1. **JWT Bearer Token** (user-facing frontend)
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

2. **Static API Key** (service-to-service, dashboards)
   ```
   X-API-Key: dashboard_key_abc123xyz
   ```

Set up in your API client:

```typescript
const apiClient = axios.create({
  baseURL: API_CONFIG.baseURL,
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`,
    'Accept': 'application/json',
  },
});

// Auto-refresh token before expiry
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const newToken = await refreshAuthToken();
      localStorage.setItem('token', newToken);
      error.config.headers.Authorization = `Bearer ${newToken}`;
      return apiClient(error.config);
    }
    return Promise.reject(error);
  }
);
```

---

## Testing the API

### Recommended Tools

1. **Swagger UI** (built-in with FastAPI)
   ```
   http://localhost:8000/docs
   ```

2. **ReDoc** (alternative docs)
   ```
   http://localhost:8000/redoc
   ```

3. **Postman** (import openapi.yaml/json)
   - File → Import → Upload `openapi.yaml`
   - Auto-generates collection with mock requests

4. **cURL Examples**

```bash
# Get dashboard summary
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/dashboard/summary?time_range=month

# Get findings
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/dashboard/security/findings?severity=critical&limit=20"

# Get alerts (SSE stream)
curl -N -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/dashboard/alerts/stream?severity=critical
```

---

## Frontend State Management Tips

### Recommended: TanStack Query + Zustand

```typescript
// hooks/useDashboardState.ts
import { create } from 'zustand';
import { useQuery, useMutation } from '@tanstack/react-query';

interface DashboardState {
  filters: {
    timeRange: 'week' | 'month' | 'quarter' | 'ytd';
    department?: string;
    provider?: string;
  };
  setTimeRange: (range: string) => void;
  setDepartment: (dept: string) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  filters: { timeRange: 'month' },
  setTimeRange: (tr) => set((s) => ({ filters: { ...s.filters, timeRange: tr as any } })),
  setDepartment: (d) => set((s) => ({ filters: { ...s.filters, department: d } })),
}));

// Usage in components
const { filters, setTimeRange } = useDashboardStore();
const { data: summary } = useDashboardSummary(filters.timeRange);
```

---

## Performance Optimization

### 1. Request Deduplication
```typescript
// TanStack Query automatically deduplicates identical requests
// within `staleTime` window (default 0)
queryClient.setDefaultOptions({
  queries: {
    staleTime: 1000 * 60 * 5, // 5 min cache
    gcTime: 1000 * 60 * 10,   // Keep in memory 10 min
  },
});
```

### 2. Pagination / Infinite Scroll
```typescript
const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
  queryKey: ['findings'],
  queryFn: ({ pageParam = 0 }) => apiClient.get('/security/findings', {
    params: { offset: pageParam, limit: 50 }
  }),
  getNextPageParam: (lastPage) => lastPage.data.offset + 50,
});
```

### 3. Lazy Loading
```typescript
// Load expensive data (scatter plot, Sankey) on-demand
const [showAdvanced, setShowAdvanced] = useState(false);
const { data: scatter } = useQuery({
  queryKey: ['scatter'],
  queryFn: () => apiClient.get('/explorer/complexity-scatter'),
  enabled: showAdvanced, // Only fetch when needed
});
```

---

## Deployment Checklist

- [ ] Update `API_CONFIG.baseURL` for production environment
- [ ] Enable CORS in backend for frontend domain
- [ ] Set up JWT token refresh strategy
- [ ] Configure API rate limiting / throttling
- [ ] Add error tracking (Sentry/LogRocket)
- [ ] Test SSE stream under load
- [ ] Verify pagination performance with large datasets
- [ ] Document any custom authentication requirements

---

## Support & Troubleshooting

**Q: Getting 401 Unauthorized?**
- Check JWT expiry: `jwtdecode.decode(token)`
- Ensure `Authorization` header is set
- Test with API key if JWT fails

**Q: SSE stream not connecting?**
- Check CORS headers on backend
- Verify browser supports EventSource
- Test with `curl -N` for comparison

**Q: Empty response for /analytics/cost?**
- Ensure `dimension` parameter is provided
- Check date range (may have no data outside window)
- Verify department exists in database

**Q: Pagination showing duplicates?**
- Confirm `offset` and `limit` are incremented correctly
- Check if data is being inserted between page fetches
- Use cursor-based pagination if data is highly volatile

---

**Generated 2026-04-08 | Last Updated: OpenAPI 1.0.0**
