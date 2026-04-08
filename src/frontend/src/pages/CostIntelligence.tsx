import { useState } from 'react';
import { motion } from 'framer-motion';
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
import { TrendingDown, Zap, Download } from 'lucide-react';
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

  const totalCost = mockDashboardSummary.metrics.totalCost;

  const costByDeptData = mockCostByDepartment.map((dept) => ({
    name: dept.key,
    cost: Math.round(dept.cost),
  })).sort((a, b) => b.cost - a.cost);

  const costByModelData = mockCostByModel.map((model) => ({
    name: model.key,
    cost: Math.round(model.cost),
  }));

  const costTrendData = mockCostTimeSeries.data.slice(-30).map((point) => ({
    date: new Date(point.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    cost: Math.round(point.value),
    timestamp: point.timestamp,
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

  const recommendations = mockRecommendations
    .filter((rec) => rec.category === 'cost_optimization')
    .slice(0, 4);

  const handleExport = () => {
    setShowExport(true);
    setTimeout(() => setShowExport(false), 3000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-8"
    >
      {/* Header Row */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-baseline gap-2">
            <h1 className="text-4xl font-bold text-[var(--text-primary)]">Cost Intelligence</h1>
            <span className="text-3xl font-bold text-[var(--accent)]">
              <CountUp end={totalCost} prefix="€" decimals={0} />
            </span>
          </div>
          <p className="text-[var(--text-tertiary)] mt-2">Optimize AI spending across departments and models</p>
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
      </div>

      {/* Time Range Pills */}
      <div className="flex gap-2 flex-wrap">
        {(['week', 'month', 'quarter', 'ytd'] as const).map((range) => (
          <motion.button
            key={range}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setTimeRange(range)}
            className={`px-4 py-2 rounded-full font-medium transition-all backdrop-blur-sm border ${
              timeRange === range
                ? 'bg-[var(--accent)] text-white border-[var(--accent-glow)]'
                : 'bg-[var(--bg-surface)] text-[var(--text-secondary)] border-[var(--border-subtle)] hover:border-[var(--border-default)]'
            }`}
          >
            {range === 'week' ? 'Week' : range === 'month' ? 'Month' : range === 'quarter' ? 'Quarter' : 'YTD'}
          </motion.button>
        ))}
      </div>

      {/* Row 1: Three Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cost by Department */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Card header={<h3 className="font-semibold text-[var(--text-primary)]">Cost by Department</h3>}>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={costByDeptData} layout="vertical" margin={{ top: 5, right: 30, bottom: 5, left: 100 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                <XAxis type="number" stroke="var(--text-tertiary)" style={{ fontSize: '12px' }} />
                <YAxis dataKey="name" type="category" stroke="var(--text-tertiary)" width={100} style={{ fontSize: '12px' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--bg-elevated)',
                    border: '1px solid var(--border-default)',
                    borderRadius: 'var(--radius-lg)',
                    boxShadow: '0 20px 25px -5px rgba(0,0,0,0.3)',
                  }}
                  formatter={(value: any) => `€${value.toLocaleString('en-EU')}`}
                  cursor={{ fill: 'var(--accent-muted)' }}
                />
                <Bar dataKey="cost" fill="var(--accent)" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </motion.div>

        {/* Cost by Model - Donut */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.05 }}
        >
          <Card header={<h3 className="font-semibold text-[var(--text-primary)]">Cost by Model</h3>}>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={costByModelData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={85}
                  paddingAngle={2}
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
                    borderRadius: 'var(--radius-lg)',
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
                      className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ backgroundColor: MODEL_COLORS[item.name] || '#666' }}
                    />
                    <span className="text-[var(--text-tertiary)] truncate">{percentage}%</span>
                  </div>
                );
              })}
            </div>
          </Card>
        </motion.div>

        {/* Cost Trend */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <Card header={<h3 className="font-semibold text-[var(--text-primary)]">Cost Trend</h3>}>
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
                    borderRadius: 'var(--radius-lg)',
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

      {/* Row 2: Budget Alerts */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.15 }}
      >
        <div>
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Budget Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {departmentBudgets.map((dept, idx) => (
              <motion.div
                key={dept.name}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.08, duration: 0.3 }}
              >
                <Card>
                  <div className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-semibold text-[var(--text-primary)]">{dept.name}</h4>
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
                      <div className="flex justify-between text-sm font-semibold text-[var(--text-primary)]">
                        <span>€{(dept.current / 1000).toFixed(1)}k</span>
                        <span>€{(dept.budget / 1000).toFixed(1)}k</span>
                      </div>
                    </div>

                    <div className="h-2 bg-[var(--bg-surface-hover)] rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(dept.percentage, 100)}%` }}
                        transition={{ duration: 0.8, ease: 'easeOut' }}
                        className={`h-full ${
                          dept.percentage > 90
                            ? 'bg-[var(--critical)]'
                            : dept.percentage > 70
                              ? 'bg-[var(--high)]'
                              : 'bg-[var(--success)]'
                        } rounded-full`}
                      />
                    </div>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Row 3: Cost Optimization Recommendations */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.2 }}
      >
        <div>
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">Cost Optimization Opportunities</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendations.map((rec, idx) => (
              <motion.div
                key={rec.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.08, duration: 0.3 }}
                whileHover={{ y: -4 }}
              >
                <Card className="h-full hover:border-[var(--accent)] transition-colors group">
                  <div className="space-y-4">
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-lg bg-[var(--accent-muted)] group-hover:bg-[var(--accent)] transition-colors">
                        {rec.impact.effortToImplement === 'easy' || rec.impact.effortToImplement === 'trivial' ? (
                          <Zap size={18} className="text-[var(--accent)]" />
                        ) : (
                          <TrendingDown size={18} className="text-[var(--accent)]" />
                        )}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-[var(--text-primary)]">{rec.title}</h4>
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
      </motion.div>

      {/* Export Toast */}
      {showExport && (
        <motion.div
          initial={{ opacity: 0, y: 10, x: 20 }}
          animate={{ opacity: 1, y: 0, x: 0 }}
          exit={{ opacity: 0, y: 10, x: 20 }}
          className="fixed bottom-6 right-6 px-4 py-3 rounded-lg bg-[var(--success)] text-white text-sm font-medium shadow-lg flex items-center gap-2"
        >
          <span>Cost report exported as CSV</span>
        </motion.div>
      )}
    </motion.div>
  );
}
