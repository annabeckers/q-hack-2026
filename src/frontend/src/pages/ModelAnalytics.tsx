import { motion } from 'framer-motion';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from 'recharts';
import { Lightbulb, TrendingDown } from 'lucide-react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import CountUp from '@/components/ui/CountUp';
import { mockModelMetrics, mockScatterPoints } from '@/lib/mock-data';
import { ModelMetrics } from '@/lib/types';

const providerColors: Record<string, string> = {
  'GPT-4o': '#10a37f',
  'Claude 3.5 Sonnet': '#d4a574',
  'Gemini Pro': '#4285f4',
  'Mistral': '#7c3aed',
  'Local Ollama': '#64748b',
};

const hallucData = [
  { model: 'GPT-4o', rate: 4.2 },
  { model: 'Gemini Pro', rate: 2.8 },
  { model: 'Mistral', rate: 2.1 },
  { model: 'Claude 3.5 Sonnet', rate: 1.1 },
  { model: 'Local Ollama', rate: 0.3 },
];

const getHallucinationColor = (rate: number) => {
  if (rate > 3.5) return '#ef4444';
  if (rate > 2.5) return '#f97316';
  if (rate > 1.5) return '#eab308';
  return '#22c55e';
};

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: 'easeOut' },
  },
};

interface ModelCardProps {
  metric: ModelMetrics;
}

function ModelUsageCard({ metric }: ModelCardProps) {
  const leakColor = metric.risk.leakRate > 0.3 ? '#ef4444' : metric.risk.leakRate > 0.15 ? '#f97316' : '#22c55e';

  return (
    <motion.div variants={itemVariants}>
      <Card className="h-full" style={{ borderTop: `3px solid ${providerColors[metric.model]}` }}>
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold text-[var(--text-primary)] text-sm mb-1">{metric.model}</h3>
            <p className="text-xs text-[var(--text-secondary)]">{metric.provider}</p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <p className="text-xs text-[var(--text-tertiary)]">Sessions</p>
              <p className="text-lg font-bold text-[var(--text-primary)]">
                <CountUp target={metric.usage.sessions} format="plain" />
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-[var(--text-tertiary)]">Total Cost</p>
              <p className="text-lg font-bold text-[var(--text-primary)]">
                <CountUp target={metric.costs.total} format="currency" currencySymbol="€" />
              </p>
            </div>
          </div>

          <div className="h-px bg-[var(--border-subtle)]" />

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <p className="text-xs text-[var(--text-tertiary)]">Leak Rate /1K</p>
              <p className="text-lg font-bold" style={{ color: leakColor }}>
                {(metric.risk.leakRate * 1000).toFixed(0)}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-[var(--text-tertiary)]">Halluc Rate /1K</p>
              <p className="text-lg font-bold text-[var(--text-secondary)]">
                {(metric.risk.hallucRate * 1000).toFixed(0)}
              </p>
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

export default function ModelAnalytics() {
  const models = mockModelMetrics.slice(0, 5);

  return (
    <motion.div
      className="space-y-8 pb-12"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-[var(--text-primary)] mb-2">Model Intelligence</h1>
          <p className="text-sm text-[var(--text-secondary)]">Usage patterns and risk analysis across AI providers</p>
        </div>
        <Badge variant="info" size="md">
          <CountUp target={models.length} format="plain" /> models tracked
        </Badge>
      </div>

      {/* Model Cards Grid - Row 1 */}
      <motion.div
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {models.map((metric) => (
          <ModelUsageCard key={metric.model} metric={metric} />
        ))}
      </motion.div>

      {/* Bubble Chart - Row 2 */}
      <motion.div variants={itemVariants} initial="hidden" animate="visible">
        <Card
          header={
            <div className="flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-[var(--text-primary)]">Usage Risk Map</h2>
                <p className="text-xs text-[var(--text-secondary)] mt-1">Token complexity vs risk exposure</p>
              </div>
            </div>
          }
        >
          <div className="h-[420px]">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
                <XAxis
                  dataKey="tokenCount"
                  type="number"
                  name="Complexity"
                  stroke="var(--text-secondary)"
                  style={{ fontSize: '12px' }}
                />
                <YAxis
                  dataKey="findingCount"
                  name="Risk Score"
                  stroke="var(--text-secondary)"
                  style={{ fontSize: '12px' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'var(--bg-elevated)',
                    border: '1px solid var(--border-default)',
                    color: 'var(--text-primary)',
                    borderRadius: '8px',
                    boxShadow: 'var(--shadow-lg)',
                  }}
                  cursor={{ strokeDasharray: '3 3' }}
                  formatter={(value) => {
                    if (typeof value === 'number') return value.toLocaleString();
                    return value;
                  }}
                />
                <Legend wrapperStyle={{ color: 'var(--text-secondary)' }} />
                {Object.entries(providerColors).map(([provider, color]) => (
                  <Scatter
                    key={provider}
                    name={provider}
                    data={mockScatterPoints.filter((p) => p.provider === provider)}
                    fill={color}
                    fillOpacity={0.7}
                  />
                ))}
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </motion.div>

      {/* Charts Row - Row 3 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Hallucination Rate Chart */}
        <motion.div variants={itemVariants} initial="hidden" animate="visible" className="lg:col-span-1">
          <Card header={<h2 className="font-semibold text-[var(--text-primary)] text-sm">Hallucination Rate</h2>}>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={hallucData}
                  margin={{ top: 20, right: 10, bottom: 40, left: 40 }}
                  layout="vertical"
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                  <XAxis type="number" stroke="var(--text-secondary)" style={{ fontSize: '11px' }} />
                  <YAxis dataKey="model" type="category" stroke="var(--text-secondary)" style={{ fontSize: '11px' }} width={100} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'var(--bg-elevated)',
                      border: '1px solid var(--border-default)',
                      borderRadius: '6px',
                    }}
                    formatter={(value) => `${(value as number).toFixed(1)}/1K`}
                  />
                  <Bar dataKey="rate" radius={[0, 8, 8, 0]}>
                    {hallucData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={getHallucinationColor(entry.rate)} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </motion.div>

        {/* Cost Optimization Insight */}
        <motion.div variants={itemVariants} initial="hidden" animate="visible" className="lg:col-span-2">
          <Card variant="elevated" glow={true}>
            <div className="space-y-6">
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-lg bg-[var(--accent-muted)]">
                  <Lightbulb className="w-6 h-6 text-[var(--accent)]" />
                </div>
                <div className="flex-1">
                  <h2 className="font-semibold text-[var(--text-primary)] text-base mb-1">Cost Optimization Opportunity</h2>
                  <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                    40% of GPT-4o usage is trivial Q&A. Routing to Mistral or local Ollama saves{' '}
                    <span className="font-semibold text-[var(--success)]">€8,900/month</span> with zero quality impact.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 p-4 bg-[var(--bg-surface)] rounded-lg border border-[var(--border-subtle)]">
                <div>
                  <p className="text-xs font-semibold text-[var(--text-tertiary)] uppercase mb-2">Current Spend</p>
                  <div className="text-2xl font-bold text-[var(--text-primary)]">€22,100</div>
                  <p className="text-xs text-[var(--text-tertiary)] mt-1">on GPT-4o</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-[var(--text-tertiary)] uppercase mb-2">Optimized Spend</p>
                  <div className="text-2xl font-bold text-[var(--success)]">€13,200</div>
                  <p className="text-xs text-[var(--text-tertiary)] mt-1">after routing</p>
                </div>
              </div>

              <div className="space-y-3 p-4 bg-[var(--bg-surface)] rounded-lg border border-[var(--border-subtle)]">
                <p className="text-xs font-semibold text-[var(--text-tertiary)] uppercase">Recommended Actions</p>
                <div className="space-y-2">
                  <div className="flex items-start gap-3">
                    <TrendingDown className="w-4 h-4 text-[var(--success)] flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-[var(--text-secondary)]">Route Q&A queries to Mistral Large (50% cost reduction)</span>
                  </div>
                  <div className="flex items-start gap-3">
                    <TrendingDown className="w-4 h-4 text-[var(--success)] flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-[var(--text-secondary)]">Deploy Ollama for internal code documentation</span>
                  </div>
                  <div className="flex items-start gap-3">
                    <TrendingDown className="w-4 h-4 text-[var(--success)] flex-shrink-0 mt-0.5" />
                    <span className="text-sm text-[var(--text-secondary)]">Keep GPT-4o for complex reasoning tasks</span>
                  </div>
                </div>
              </div>

              <motion.a
                href="/recommendations"
                whileHover={{ x: 4 }}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white font-medium text-sm transition-colors"
              >
                View Recommendations
                <span>→</span>
              </motion.a>
            </div>
          </Card>
        </motion.div>
      </div>
    </motion.div>
  );
}
