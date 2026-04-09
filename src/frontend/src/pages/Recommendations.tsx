import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Lightbulb,
  DollarSign,
  ShieldAlert,
  Scale,
  Zap,
  ArrowLeft,
  TrendingDown,
  CheckCircle2,
} from 'lucide-react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import CountUp from '@/components/ui/CountUp';

import { mockRecommendations } from '@/lib/mock-data';
import { apiClient } from '@/lib/api';
import { useApiCall } from '@/hooks/useApiCall';
import type { Recommendation } from '@/lib/types';

const categoryConfig: Record<
  string,
  { icon: React.ComponentType<{ className?: string; size?: number }>; color: string; label: string }
> = {
  cost_optimization: { icon: DollarSign, color: '#22c55e', label: 'Cost Optimization' },
  risk_reduction: { icon: ShieldAlert, color: '#ef4444', label: 'Risk Reduction' },
  compliance_improvement: { icon: Scale, color: '#3b82f6', label: 'Compliance' },
  performance: { icon: Zap, color: '#f59e0b', label: 'Performance' },
};

const effortBadge: Record<string, { variant: 'success' | 'info' | 'medium' | 'critical'; label: string }> = {
  trivial: { variant: 'success', label: 'Trivial' },
  easy: { variant: 'success', label: 'Easy' },
  medium: { variant: 'medium', label: 'Medium' },
  hard: { variant: 'critical', label: 'Hard' },
};

const riskBadge: Record<string, { variant: 'success' | 'medium' | 'critical'; label: string }> = {
  low: { variant: 'success', label: 'Low Impact' },
  medium: { variant: 'medium', label: 'Medium Impact' },
  high: { variant: 'critical', label: 'High Impact' },
};

function RecommendationCard({ rec, index }: { rec: Recommendation; index: number }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });
  const config = categoryConfig[rec.category] || categoryConfig.performance;
  const Icon = config.icon;
  const effort = effortBadge[rec.impact.effortToImplement] || effortBadge.medium;
  const risk = riskBadge[rec.impact.riskReduction] || riskBadge.low;

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30, scale: 0.97 }}
      animate={isInView ? { opacity: 1, y: 0, scale: 1 } : undefined}
      transition={{ delay: index * 0.08, duration: 0.5, ease: 'easeOut' }}
    >
      <Card className="h-full" style={{ borderTop: `3px solid ${config.color}` }}>
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-start gap-3">
            <div
              className="p-2.5 rounded-lg flex-shrink-0"
              style={{ background: `${config.color}12` }}
            >
              <span style={{ color: config.color }}><Icon size={20} /></span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <span
                  className="text-[10px] font-semibold uppercase tracking-wider"
                  style={{ color: config.color }}
                >
                  {config.label}
                </span>
                <Badge variant={risk.variant} size="sm">
                  {risk.label}
                </Badge>
              </div>
              <h3 className="font-bold text-[var(--text-primary)] text-sm leading-snug">
                {rec.title}
              </h3>
            </div>
          </div>

          {/* Description */}
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
            {rec.description}
          </p>

          {/* Impact metrics */}
          <div className="grid grid-cols-2 gap-3 p-3 bg-[var(--bg-surface)] rounded-lg border border-[var(--border-subtle)]">
            <div>
              <p className="text-[10px] font-semibold text-[var(--text-tertiary)] uppercase mb-1">
                Est. Savings
              </p>
              <p className="text-lg font-extrabold text-[var(--success)]">
                {rec.impact.estimatedSavings > 0 ? (
                  <CountUp target={rec.impact.estimatedSavings} format="currency" />
                ) : (
                  <span className="text-[var(--text-tertiary)]">—</span>
                )}
              </p>
              <p className="text-[10px] text-[var(--text-tertiary)]">per month</p>
            </div>
            <div>
              <p className="text-[10px] font-semibold text-[var(--text-tertiary)] uppercase mb-1">
                Effort
              </p>
              <div className="mt-1">
                <Badge variant={effort.variant} size="md">
                  {effort.label}
                </Badge>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="space-y-2">
            <p className="text-[10px] font-semibold text-[var(--text-tertiary)] uppercase tracking-wide">
              Action Steps
            </p>
            {rec.actions.map((action, i) => (
              <motion.div
                key={i}
                className="flex items-start gap-2.5"
                initial={{ opacity: 0, x: -8 }}
                animate={isInView ? { opacity: 1, x: 0 } : undefined}
                transition={{ delay: index * 0.08 + 0.3 + i * 0.06 }}
              >
                <span style={{ color: config.color }}><CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" /></span>
                <span className="text-xs text-[var(--text-secondary)] leading-relaxed">{action}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

export default function Recommendations() {
  const headerRef = useRef(null);
  const headerInView = useInView(headerRef, { once: true });

  const { data: recommendations, loading } = useApiCall(
    () => apiClient.getRecommendations(),
    mockRecommendations
  );

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <div className="w-8 h-8 border-4 border-[#1e3a8a] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const totalSavings = recommendations.reduce((sum, r) => sum + r.impact.estimatedSavings, 0);
  const costRecs = recommendations.filter((r) => r.category === 'cost_optimization');
  const riskRecs = recommendations.filter((r) => r.category === 'risk_reduction');
  const complianceRecs = recommendations.filter((r) => r.category === 'compliance_improvement');
  const perfRecs = recommendations.filter((r) => r.category === 'performance');

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
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <Link
                  to="/models"
                  className="p-1.5 rounded-lg hover:bg-[var(--bg-2)] transition-colors text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
                >
                  <ArrowLeft size={18} />
                </Link>
                <h1 className="text-3xl lg:text-4xl font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-3">
                  <Lightbulb size={28} className="text-[var(--accent)]" />
                  Recommendations
                </h1>
              </div>
              <p className="text-sm text-[var(--text-tertiary)] mt-1 ml-10">
                AI-generated insights to optimize cost, reduce risk, and improve compliance
              </p>
            </div>
            <Badge variant="info" size="md">
              <CountUp target={recommendations.length} format="plain" /> active
            </Badge>
          </div>
        </motion.div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            {
              label: 'Total Potential Savings',
              value: totalSavings,
              format: 'currency' as const,
              color: '#22c55e',
              icon: TrendingDown,
              sub: 'per month',
            },
            {
              label: 'Cost Optimizations',
              value: costRecs.length,
              format: 'plain' as const,
              color: '#22c55e',
              icon: DollarSign,
              sub: 'recommendations',
            },
            {
              label: 'Risk Reductions',
              value: riskRecs.length,
              format: 'plain' as const,
              color: '#ef4444',
              icon: ShieldAlert,
              sub: 'recommendations',
            },
            {
              label: 'Compliance',
              value: complianceRecs.length + perfRecs.length,
              format: 'plain' as const,
              color: '#3b82f6',
              icon: Scale,
              sub: 'recommendations',
            },
          ].map((stat, idx) => {
            const StatIcon = stat.icon;
            return (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.06, duration: 0.4 }}
              >
                <Card className="h-full">
                  <div className="flex items-center gap-3">
                    <div
                      className="p-2.5 rounded-lg flex-shrink-0"
                      style={{ background: `${stat.color}12` }}
                    >
                      <span style={{ color: stat.color }}><StatIcon size={18} /></span>
                    </div>
                    <div>
                      <p className="text-[10px] font-semibold text-[var(--text-tertiary)] uppercase tracking-wide">
                        {stat.label}
                      </p>
                      <p className="text-xl font-extrabold text-[var(--text-primary)]">
                        <CountUp target={stat.value} format={stat.format} />
                      </p>
                      <p className="text-[10px] text-[var(--text-tertiary)]">{stat.sub}</p>
                    </div>
                  </div>
                </Card>
              </motion.div>
            );
          })}
        </div>

        {/* Recommendation Cards Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-5">
          {recommendations.map((rec, idx) => (
            <RecommendationCard key={rec.id} rec={rec} index={idx} />
          ))}
        </div>
      </div>
    </motion.div>
  );
}
