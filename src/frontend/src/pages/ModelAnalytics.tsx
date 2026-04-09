import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
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
import { Link } from 'react-router-dom';
import { Lightbulb, TrendingDown, Brain } from 'lucide-react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import CountUp from '@/components/ui/CountUp';

import { mockModelMetrics, mockScatterPoints } from '@/lib/mock-data';
import { apiClient } from '@/lib/api';
import { useApiCall } from '@/hooks/useApiCall';
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

interface ModelCardProps {
  metric: ModelMetrics;
  index: number;
}

function ModelUsageCard({ metric, index }: ModelCardProps) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });
  const leakColor = metric.risk.leakRate > 0.3 ? '#ef4444' : metric.risk.leakRate > 0.15 ? '#f97316' : '#22c55e';

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30, scale: 0.95 }}
      animate={isInView ? { opacity: 1, y: 0, scale: 1 } : undefined}
      transition={{ delay: index * 0.08, duration: 0.5, ease: 'easeOut' }}
    >
      <Card
        className="h-full group"
        style={{
          borderTop: `3px solid ${providerColors[metric.model]}`,
          boxShadow: `0 -4px 15px ${providerColors[metric.model]}10`,
        }}
      >
        <div className="space-y-4">
          <div>
            <h3 className="font-bold text-[var(--text-primary)] text-sm mb-1">{metric.model}</h3>
            <p className="text-xs text-[var(--text-secondary)]">{metric.provider}</p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <p className="text-xs text-[var(--text-tertiary)]">Sessions</p>
              <p className="text-lg font-extrabold text-[var(--text-primary)]">
                <CountUp target={metric.usage.sessions} format="plain" />
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-[var(--text-tertiary)]">Total Cost</p>
              <p className="text-lg font-extrabold text-[var(--text-primary)]">
                <CountUp target={metric.costs.total} format="currency" />
              </p>
            </div>
          </div>

          <div className="h-px bg-[var(--border-subtle)]" />

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <p className="text-xs text-[var(--text-tertiary)]">Leak Rate /1K</p>
              <p className="text-lg font-extrabold" style={{ color: leakColor }}>
                {(metric.risk.leakRate * 1000).toFixed(0)}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-[var(--text-tertiary)]">Halluc Rate /1K</p>
              <p className="text-lg font-extrabold text-[var(--text-secondary)]">
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
  const headerRef = useRef(null);
  const headerInView = useInView(headerRef, { once: true });

  // ── API calls with mock fallback ──
  const { data: modelMetrics, loading: l1 } = useApiCall(
    () => apiClient.getModelComparison(),
    mockModelMetrics
  );

  const { data: scatterPoints, loading: l2 } = useApiCall(
    () => apiClient.getComplexityScatter(),
    mockScatterPoints
  );

  const models = modelMetrics.slice(0, 5);

  if (l1 || l2) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="w-8 h-8 border-4 border-[#1e3a8a] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // Ensure robust provider list for Risk Map
  const colorPalette = ['#10b981', '#f59e0b', '#3b82f6', '#8b5cf6', '#ef5350', '#06b6d4', '#ec4899'];
  const riskMapProviders = Array.from(new Set(scatterPoints.map((p) => p.provider)));

  return (
    <motion.div
      className="p-6 lg:p-8 pb-12 relative min-h-full"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <div className="space-y-6 relative z-10">
        {/* Header */}
        <motion.div
          ref={headerRef}
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="flex items-center justify-between"
        >
          <div>
            <h1 className="text-3xl lg:text-4xl font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-3">
              <Brain size={28} className="text-[var(--accent)]" />
              Model Intelligence
            </h1>
            <p className="text-sm text-[var(--text-tertiary)] mt-1">Usage patterns and risk analysis across AI providers</p>
          </div>
          <Badge variant="info" size="md">
            <CountUp target={models.length} format="plain" /> models tracked
          </Badge>
        </motion.div>

        {/* Model Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {models.map((metric, idx) => (
            <ModelUsageCard key={metric.model} metric={metric} index={idx} />
          ))}
        </div>

        {/* Scatter Chart */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
        >
          <Card
            header={
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-bold text-[var(--text-primary)]">Usage Risk Map</h2>
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
                      borderRadius: '10px',
                      boxShadow: '0 20px 40px rgba(20,27,65,0.1)',
                    }}
                    cursor={{ strokeDasharray: '3 3' }}
                    formatter={(value) => {
                      if (typeof value === 'number') return value.toLocaleString();
                      return value;
                    }}
                  />
                  <Legend wrapperStyle={{ color: 'var(--text-secondary)' }} />
                  {riskMapProviders.map((provider, i) => (
                    <Scatter
                      key={provider}
                      name={provider}
                      data={scatterPoints.filter((p) => p.provider === provider)}
                      fill={colorPalette[i % colorPalette.length]}
                      fillOpacity={0.7}
                    />
                  ))}
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </motion.div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="lg:col-span-1"
          >
            <Card header={<h2 className="font-bold text-[var(--text-primary)] text-sm">Hallucination Rate</h2>}>
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
                        borderRadius: '10px',
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

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="lg:col-span-2"
          >
            <Card variant="premium" glow={true}>
              <div className="space-y-6">
                <div className="flex items-start gap-4">
                  <motion.div
                    className="p-3 rounded-lg bg-[var(--accent-muted)]"
                    animate={{ scale: [1, 1.05, 1] }}
                    transition={{ duration: 3, repeat: Infinity }}
                  >
                    <Lightbulb className="w-6 h-6 text-[var(--accent)]" />
                  </motion.div>
                  <div className="flex-1">
                    <h2 className="font-bold text-[var(--text-primary)] text-base mb-1">Cost Optimization Opportunity</h2>
                    <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                      40% of GPT-4o usage is trivial Q&A. Routing to Mistral or local Ollama saves{' '}
                      <span className="font-bold text-[var(--success)]">€8,900/month</span> with zero quality impact.
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 p-4 bg-[var(--bg-surface)] rounded-lg border border-[var(--border-subtle)]">
                  <div>
                    <p className="text-xs font-semibold text-[var(--text-tertiary)] uppercase mb-2">Current Spend</p>
                    <div className="text-2xl font-extrabold text-[var(--text-primary)]">
                      <CountUp target={22100} format="currency" />
                    </div>
                    <p className="text-xs text-[var(--text-tertiary)] mt-1">on GPT-4o</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-[var(--text-tertiary)] uppercase mb-2">Optimized Spend</p>
                    <div className="text-2xl font-extrabold text-[var(--success)]">
                      <CountUp target={13200} format="currency" />
                    </div>
                    <p className="text-xs text-[var(--text-tertiary)] mt-1">after routing</p>
                  </div>
                </div>

                <div className="space-y-3 p-4 bg-[var(--bg-surface)] rounded-lg border border-[var(--border-subtle)]">
                  <p className="text-xs font-semibold text-[var(--text-tertiary)] uppercase">Recommended Actions</p>
                  <div className="space-y-2">
                    {[
                      'Route Q&A queries to Mistral Large (50% cost reduction)',
                      'Deploy Ollama for internal code documentation',
                      'Keep GPT-4o for complex reasoning tasks',
                    ].map((action, i) => (
                      <motion.div
                        key={i}
                        className="flex items-start gap-3"
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.8 + i * 0.1 }}
                      >
                        <TrendingDown className="w-4 h-4 text-[var(--success)] flex-shrink-0 mt-0.5" />
                        <span className="text-sm text-[var(--text-secondary)]">{action}</span>
                      </motion.div>
                    ))}
                  </div>
                </div>

                <Link
                  to="/recommendations"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors border border-transparent hover:opacity-90"
                  style={{ backgroundColor: '#1e3a8a', color: '#ffffff' }}
                >
                  View Recommendations
                  <span>→</span>
                </Link>
              </div>
            </Card>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}
