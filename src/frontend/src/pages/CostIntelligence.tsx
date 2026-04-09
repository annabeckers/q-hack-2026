import { useState, useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { TrendingDown, Zap, Download, DollarSign } from 'lucide-react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import CountUp from '@/components/ui/CountUp';

import {
  mockCostByDepartment,
  mockCostByModel,
  mockCostTimeSeries,
  mockDashboardSummary,
  mockRecommendations,
} from '@/lib/mock-data';
import { apiClient } from '@/lib/api';
import { useApiCall } from '@/hooks/useApiCall';
import type * as types from '@/lib/types';

const MODEL_COLORS: Record<string, string> = {
  'GPT-4o': '#10b981',
  'Claude 3.5 Sonnet': '#f59e0b',
  'Gemini Pro': '#3b82f6',
  'Mistral': '#8b5cf6',
  'Local Ollama': '#ef5350',
};

export default function CostIntelligence() {
  const [timeRange, setTimeRange] = useState<types.TimeRange>('month');
  const [showExport, setShowExport] = useState(false);
  const headerRef = useRef(null);
  const headerInView = useInView(headerRef, { once: true });

  // ── API calls with mock fallback ──
  const { data: summaryData } = useApiCall(
    () => apiClient.getDashboardSummary(timeRange),
    mockDashboardSummary,
    [timeRange]
  );

  const { data: costByDeptRaw } = useApiCall(
    () => apiClient.getCostAnalytics('department').then(r => {
      if (Array.isArray(r)) return r as types.CostBucket[];
      if (r && 'items' in r) return (r as any).items as types.CostBucket[];
      return mockCostByDepartment;
    }),
    mockCostByDepartment
  );

  const { data: costByModelRaw } = useApiCall(
    () => apiClient.getCostAnalytics('model').then(r => {
      if (Array.isArray(r)) return r as types.CostBucket[];
      if (r && 'items' in r) return (r as any).items as types.CostBucket[];
      return mockCostByModel;
    }),
    mockCostByModel
  );

  const { data: costTimeSeriesRaw } = useApiCall(
    () => apiClient.getTimeSeries('cost', 'day'),
    mockCostTimeSeries
  );

  const { data: recommendations } = useApiCall(
    () => apiClient.getRecommendations(),
    mockRecommendations
  );

  const totalCost = summaryData?.metrics?.totalCost ?? mockDashboardSummary.metrics.totalCost;

  const costByDeptData = costByDeptRaw.map((dept) => ({
    name: dept.key,
    cost: Math.round(dept.cost),
  })).sort((a, b) => b.cost - a.cost);

  const costByModelData = costByModelRaw.map((model) => ({
    name: model.key,
    cost: Math.round(model.cost),
  }));

  // Normalize time series — backend may return { data: [...] } or { metric, data }
  const timeSeriesData = (costTimeSeriesRaw as any)?.data ?? costTimeSeriesRaw;
  const costTrendData = (Array.isArray(timeSeriesData) ? timeSeriesData : []).slice(-30).map((point: any) => ({
    date: new Date(point.timestamp ?? point.date ?? '').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    cost: Math.round(point.value ?? point.cost ?? 0),
    timestamp: point.timestamp ?? point.date,
  }));

  const departmentBudgets = [
    { name: 'Engineering', current: 18200, budget: 20000, percentage: 91 },
    { name: 'Product', current: 8400, budget: 10000, percentage: 84 },
    { name: 'Marketing', current: 5320, budget: 5500, percentage: 97 },
  ];

  const getBudgetVariant = (percentage: number): 'critical' | 'high' | 'success' => {
    if (percentage > 90) return 'critical';
    if (percentage > 70) return 'high';
    return 'success';
  };

  const costRecs = recommendations
    .filter((rec) => rec.category === 'cost_optimization')
    .slice(0, 4);

  const handleExport = () => {
    setShowExport(true);
    setTimeout(() => setShowExport(false), 3000);
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="p-6 lg:p-8 relative min-h-full"
    >

      <div className="space-y-6 relative z-10">
        {/* Header */}
        <motion.div
          ref={headerRef}
          initial={{ opacity: 0, y: -20 }}
          animate={headerInView ? { opacity: 1, y: 0 } : undefined}
          transition={{ duration: 0.6 }}
          className="flex items-center justify-between"
        >
          <div>
            <h1 className="text-3xl lg:text-4xl font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-3">
              <DollarSign size={28} className="text-[var(--accent)]" />
              Cost Intelligence
              <span className="text-xl font-bold text-[var(--accent)] ml-1">
                <CountUp target={totalCost} format="currency" />
              </span>
            </h1>
            <p className="text-sm text-[var(--text-tertiary)] mt-1">Optimize AI spending across departments and models</p>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)] text-[var(--text-primary)] hover:bg-[var(--bg-surface-hover)] transition-colors"
          >
            <Download size={16} />
            <span className="text-sm font-medium">Export</span>
          </motion.button>
        </motion.div>

        {/* Time Range */}
        <div className="flex gap-2 flex-wrap">
          {(['week', 'month', 'quarter', 'ytd'] as const).map((range, idx) => (
            <motion.button
              key={range}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 rounded-full font-medium transition-all border text-sm ${
                timeRange === range
                  ? 'border-transparent'
                  : 'bg-transparent text-[var(--text-secondary)] border-[var(--border-subtle)] hover:border-[var(--border-default)]'
              }`}
              style={timeRange === range ? { backgroundColor: '#1e3a8a', color: '#ffffff' } : undefined}
            >
              {range === 'week' ? 'Week' : range === 'month' ? 'Month' : range === 'quarter' ? 'Quarter' : 'YTD'}
            </motion.button>
          ))}
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <Card header={<h3 className="font-bold text-[var(--text-primary)]">Cost by Department</h3>}>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={costByDeptData} layout="vertical" margin={{ top: 5, right: 30, bottom: 5, left: 100 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                  <XAxis type="number" stroke="var(--text-tertiary)" style={{ fontSize: '12px' }} />
                  <YAxis dataKey="name" type="category" stroke="var(--text-tertiary)" width={100} style={{ fontSize: '12px' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'var(--bg-elevated)',
                      border: '1px solid var(--border-default)',
                      borderRadius: '10px',
                      boxShadow: '0 20px 40px rgba(20,27,65,0.1)',
                    }}
                    formatter={(value: any) => `€${value.toLocaleString('en-EU')}`}
                    cursor={{ fill: 'var(--accent-muted)' }}
                  />
                  <Bar dataKey="cost" fill="var(--accent)" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}>
            <Card header={<h3 className="font-bold text-[var(--text-primary)]">Cost by Model</h3>}>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={costByModelData}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={85}
                    paddingAngle={3}
                    dataKey="cost"
                  >
                    {costByModelData.map((entry) => (
                      <Cell key={entry.name} fill={MODEL_COLORS[entry.name] || '#666'} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'var(--bg-elevated)',
                      border: '1px solid var(--border-default)',
                      borderRadius: '10px',
                    }}
                    formatter={(value: any) => `€${value.toLocaleString('en-EU')}`}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                {costByModelData.map((item) => {
                  const percentage = ((item.cost / costByModelData.reduce((a, b) => a + b.cost, 0)) * 100).toFixed(0);
                  return (
                    <div key={item.name} className="flex items-center gap-2">
                      <div
                        className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: MODEL_COLORS[item.name] || '#666' }}
                      />
                      <span className="text-[var(--text-secondary)] truncate">{item.name}</span>
                      <span className="text-[var(--text-tertiary)] ml-auto">{percentage}%</span>
                    </div>
                  );
                })}
              </div>
            </Card>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }}>
            <Card header={<h3 className="font-bold text-[var(--text-primary)]">Cost Trend</h3>}>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={costTrendData}>
                  <defs>
                    <linearGradient id="colorAccent" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--accent)" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="var(--accent)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                  <XAxis
                    dataKey="date"
                    stroke="var(--text-tertiary)"
                    style={{ fontSize: '12px' }}
                    interval={Math.floor(costTrendData.length / 5)}
                  />
                  <YAxis stroke="var(--text-tertiary)" style={{ fontSize: '12px' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'var(--bg-elevated)',
                      border: '1px solid var(--border-default)',
                      borderRadius: '10px',
                    }}
                    formatter={(value: any) => `€${value.toLocaleString('en-EU')}`}
                  />
                  <ReferenceLine y={10000} stroke="var(--border-default)" strokeDasharray="5 5" />
                  <Area
                    type="monotone"
                    dataKey="cost"
                    stroke="var(--accent)"
                    strokeWidth={2}
                    fill="url(#colorAccent)"
                    dot={false}
                    isAnimationActive
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Card>
          </motion.div>
        </div>

        {/* Budget Status */}
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)] mb-4">Budget Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {departmentBudgets.map((dept, idx) => (
              <motion.div
                key={dept.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1, duration: 0.4 }}
              >
                <Card>
                  <div className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-bold text-[var(--text-primary)]">{dept.name}</h4>
                        <p className="text-xs text-[var(--text-tertiary)] mt-1">{dept.percentage}% of budget used</p>
                      </div>
                      <Badge variant={getBudgetVariant(dept.percentage)}>
                        {dept.percentage > 90 ? 'Alert' : dept.percentage > 70 ? 'Caution' : 'OK'}
                      </Badge>
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between text-xs text-[var(--text-tertiary)]">
                        <span>Spent</span>
                        <span>Budget</span>
                      </div>
                      <div className="flex justify-between text-sm font-bold text-[var(--text-primary)]">
                        <span>€{(dept.current / 1000).toFixed(1)}k</span>
                        <span>€{(dept.budget / 1000).toFixed(1)}k</span>
                      </div>
                    </div>

                    <div className="h-2 bg-[var(--bg-surface-hover)] rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(dept.percentage, 100)}%` }}
                        transition={{ duration: 1, delay: 0.3, ease: 'easeOut' }}
                        className={`h-full ${
                          dept.percentage > 90
                            ? 'bg-[var(--critical)]'
                            : dept.percentage > 70
                              ? 'bg-[var(--high)]'
                              : 'bg-[var(--success)]'
                        } rounded-full`}
                        style={{
                          boxShadow: dept.percentage > 90 ? '0 0 8px var(--critical-glow)' : 'none',
                        }}
                      />
                    </div>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)] mb-4">Cost Optimization Opportunities</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {costRecs.map((rec, idx) => (
              <motion.div
                key={rec.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.08, duration: 0.4 }}
              >
                <Card className="h-full hover:border-[var(--accent)] transition-all group">
                  <div className="space-y-4">
                    <div className="flex items-start gap-3">
                      <motion.div
                        className="p-2 rounded-lg bg-[var(--accent-muted)] group-hover:bg-[#1e3a8a] transition-colors"
                        whileHover={{ rotate: 15 }}
                      >
                        {rec.impact.effortToImplement === 'easy' || rec.impact.effortToImplement === 'trivial' ? (
                          <Zap size={18} className="text-[var(--accent)] group-hover:text-white transition-colors" />
                        ) : (
                          <TrendingDown size={18} className="text-[var(--accent)] group-hover:text-white transition-colors" />
                        )}
                      </motion.div>
                      <div className="flex-1">
                        <h4 className="font-bold text-[var(--text-primary)]">{rec.title}</h4>
                        <p className="text-xs text-[var(--text-tertiary)] mt-1">{rec.description}</p>
                      </div>
                    </div>

                    <div className="border-t border-[var(--border-subtle)] pt-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-xs text-[var(--text-tertiary)]">Monthly Savings</p>
                          <p className="text-sm font-bold text-[var(--success)] mt-1">
                            €{rec.impact.estimatedSavings.toLocaleString('en-EU', { maximumFractionDigits: 0 })}
                          </p>
                        </div>
                        <Badge
                          variant={
                            rec.impact.effortToImplement === 'trivial' || rec.impact.effortToImplement === 'easy'
                              ? 'success'
                              : rec.impact.effortToImplement === 'medium'
                                ? 'info'
                                : 'high'
                          }
                        >
                          {rec.impact.effortToImplement}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Export Toast */}
        {showExport && (
          <motion.div
            initial={{ opacity: 0, y: 10, x: 20 }}
            animate={{ opacity: 1, y: 0, x: 0 }}
            exit={{ opacity: 0, y: 10, x: 20 }}
            className="fixed bottom-6 right-6 px-4 py-3 rounded-lg bg-[var(--success)] text-white text-sm font-medium shadow-lg flex items-center gap-2 z-50"
          >
            <span>Cost report exported as CSV</span>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
