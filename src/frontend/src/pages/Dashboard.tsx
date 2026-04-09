import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import {
  DollarSign,
  ShieldAlert,
  Brain,
  TrendingUp,
  AlertTriangle,
  EyeOff,
  KeyRound,
  UserX,
  Package,
  Zap,
} from 'lucide-react';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import CountUp from '../components/ui/CountUp';
import {
  mockDashboardSummary,
  mockSeverityDistribution,
  mockAlerts,
  mockFindings,
} from '../lib/mock-data';
import * as types from '../lib/types';

// Utility for relative time formatting
function formatRelativeTime(timestamp: string): string {
  const now = new Date();
  const date = new Date(timestamp);
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

// Sparkline SVG component
function Sparkline({ values }: { values: number[] }) {
  if (values.length < 2) return null;

  const width = 60;
  const height = 24;
  const padding = 4;

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const points = values.map((v, i) => ({
    x: padding + (i / (values.length - 1)) * (width - 2 * padding),
    y: height - padding - ((v - min) / range) * (height - 2 * padding),
  }));

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="w-full">
      <motion.path
        d={pathD}
        fill="none"
        stroke="var(--accent)"
        strokeWidth="2"
        strokeLinecap="round"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 1.2, ease: 'easeOut' }}
      />
    </svg>
  );
}

// Compliance Gauge - Animated SVG Ring
function ComplianceGauge({ score, index }: { score: number; index: number }) {
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { delay: index * 0.08, duration: 0.5, ease: 'easeOut' },
    },
  };

  const gaugeVariants = {
    hidden: { strokeDashoffset: circumference },
    visible: {
      strokeDashoffset,
      transition: { delay: 0.4, duration: 1.8, ease: 'easeOut' },
    },
  };

  const getColor = (s: number): string => {
    if (s >= 80) return 'var(--success)';
    if (s >= 60) return 'var(--medium)';
    return 'var(--critical)';
  };

  const getStatus = (s: number): string => {
    if (s >= 80) return 'Compliant';
    if (s >= 60) return 'Partial';
    return 'At Risk';
  };

  return (
    <motion.div variants={containerVariants}>
      <Card className="h-full flex flex-col items-center justify-center py-8 relative overflow-hidden group hover:shadow-lg transition-shadow">
        <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
          <span className="text-xs text-[var(--text-tertiary)]">EU AI Act</span>
        </div>

        <div className="relative w-32 h-32 flex items-center justify-center mb-4">
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 160 160">
            <circle
              cx="80"
              cy="80"
              r={radius}
              fill="none"
              stroke="var(--border-subtle)"
              strokeWidth="6"
              opacity="0.3"
            />
            <motion.circle
              cx="80"
              cy="80"
              r={radius}
              fill="none"
              stroke={getColor(score)}
              strokeWidth="6"
              strokeDasharray={circumference}
              strokeLinecap="round"
              variants={gaugeVariants}
              filter="drop-shadow(0 0 8px var(--accent-glow))"
            />
          </svg>

          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="text-3xl font-bold text-[var(--text-primary)]">
                <CountUp target={score} format="plain" />
              </div>
              <div className="text-xs text-[var(--text-tertiary)] font-medium mt-1">
                / 100
              </div>
            </div>
          </div>
        </div>

        <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">
          {getStatus(score)}
        </p>
      </Card>
    </motion.div>
  );
}

// Minimal KPI Card
function KPICard({
  title,
  value,
  format = 'plain',
  trend,
  icon: Icon,
  sparkline,
  index,
  badge,
}: {
  title: string;
  value?: number;
  format?: 'currency' | 'percentage' | 'plain';
  trend?: { direction: 'up' | 'down'; percent: number };
  icon?: React.ComponentType<{ size: number; className?: string }>;
  sparkline?: number[];
  index: number;
  badge?: string;
}) {
  const containerVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { delay: index * 0.05, duration: 0.4, ease: 'easeOut' },
    },
  };

  return (
    <motion.div variants={containerVariants} className="h-full">
      <div className="glass-card rounded-2xl p-5 h-full flex flex-col justify-between group transition-shadow hover:shadow-lg">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 text-[var(--text-secondary)]">
            {Icon && <Icon size={16} className="opacity-70" />}
            <h3 className="text-xs font-medium tracking-tight">
              {title}
            </h3>
          </div>
          {badge && (
            <Badge variant="critical" className="text-[10px] font-semibold px-1.5 py-0.5">
              {badge}
            </Badge>
          )}
        </div>

        {value !== undefined ? (
          <div className="mt-4">
            <div className="flex items-baseline gap-2">
              <div className="text-4xl font-semibold tracking-tight text-[var(--text-primary)]">
                <CountUp target={value} format={format} />
              </div>
            </div>

            {trend && (
              <div className="flex items-center gap-1.5 mt-2 text-xs font-medium">
                <span className={trend.direction === 'up' ? 'text-[var(--critical)]' : 'text-[var(--success)]'}>
                  {trend.direction === 'up' ? '↗' : '↘'} {trend.percent}%
                </span>
                <span className="text-[var(--text-tertiary)]">vs last week</span>
              </div>
            )}

            {sparkline && sparkline.length > 1 && (
              <div className="h-4 mt-3 opacity-50 group-hover:opacity-100 transition-opacity">
                <Sparkline values={sparkline} />
              </div>
            )}
          </div>
        ) : null}
      </div>
    </motion.div>
  );
}

// Severity Breakdown Chart - Premium styling
function ThreatDistribution({ distribution }: { distribution: types.SeverityDistribution }) {
  const chartData = [
    {
      category: 'Secrets',
      critical: distribution.secrets.critical,
      high: distribution.secrets.high,
      medium: distribution.secrets.medium,
      total: distribution.secrets.critical + distribution.secrets.high + distribution.secrets.medium,
    },
    {
      category: 'PII',
      critical: distribution.pii.critical,
      high: distribution.pii.high,
      medium: distribution.pii.medium,
      total: distribution.pii.critical + distribution.pii.high + distribution.pii.medium,
    },
    {
      category: 'Slopsquatting',
      critical: distribution.slopsquat.critical,
      high: distribution.slopsquat.high,
      medium: distribution.slopsquat.medium,
      total: distribution.slopsquat.critical + distribution.slopsquat.high + distribution.slopsquat.medium,
    },
  ];

  const totalFindings = chartData.reduce((sum, d) => sum + d.total, 0);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { duration: 0.6, ease: 'easeOut' },
    },
  };

  return (
    <motion.div variants={containerVariants}>
      <Card header={
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-[var(--text-primary)]">
            Threat Distribution
          </h3>
          <Badge variant="default" className="text-xs">
            {totalFindings} total
          </Badge>
        </div>
      } className="relative overflow-hidden">
        <div className="space-y-6">
          {/* Legend */}
          <div className="flex gap-6 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-sm bg-[var(--critical)]" />
              <span className="text-[var(--text-secondary)]">Critical</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-sm bg-[var(--high)]" />
              <span className="text-[var(--text-secondary)]">High</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-sm bg-[var(--medium)]" />
              <span className="text-[var(--text-secondary)]">Medium</span>
            </div>
          </div>

          {/* Chart */}
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
              <XAxis
                dataKey="category"
                stroke="var(--border-subtle)"
                tick={{ fill: 'var(--text-tertiary)', fontSize: 12 }}
                axisLine={{ stroke: 'var(--border-subtle)' }}
              />
              <YAxis
                stroke="var(--border-subtle)"
                tick={{ fill: 'var(--text-tertiary)', fontSize: 12 }}
                axisLine={{ stroke: 'var(--border-subtle)' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--bg-elevated)',
                  border: '1px solid var(--border-default)',
                  borderRadius: '6px',
                  boxShadow: 'var(--shadow-lg)',
                }}
                cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
              />
              <Bar dataKey="critical" fill="var(--critical)" stackId="severity" radius={[4, 4, 0, 0]} />
              <Bar dataKey="high" fill="var(--high)" stackId="severity" />
              <Bar dataKey="medium" fill="var(--medium)" stackId="severity" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </motion.div>
  );
}

// Removed RecentDetections and InsightBar to compress layout

// Real-Time Alert Feed
interface StreamingAlert extends types.Alert {
  displayTime: string;
  glowing: boolean;
}

function LiveThreatFeed() {
  const [alerts, setAlerts] = useState<StreamingAlert[]>([]);
  const [alertQueue, setAlertQueue] = useState<types.Alert[]>(mockAlerts.slice().reverse());
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setAlertQueue((queue) => {
        if (queue.length === 0) return mockAlerts.slice().reverse();
        const newAlert = queue[0];
        const updatedQueue = queue.slice(1);
        setAlerts((current) => {
          const updated = [
            { ...newAlert, displayTime: formatRelativeTime(newAlert.timestamp), glowing: true },
            ...current.map(a => ({ ...a, glowing: false })),
          ];
          return updated.slice(0, 15);
        });
        return updatedQueue;
      });
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  const getAlertIcon = (type: types.AlertType) => {
    switch (type) {
      case 'secret': return <KeyRound size={14} />;
      case 'pii': return <UserX size={14} />;
      case 'slopsquat': return <Package size={14} />;
      case 'anomaly': return <Zap size={14} />;
    }
  };

  return (
    <div className="glass-card rounded-2xl h-full flex flex-col overflow-hidden relative">
      <div className="p-5 border-b border-[var(--border-subtle)] flex items-center justify-between z-10 bg-[var(--bg-1)]/50">
        <h3 className="text-sm font-semibold text-[var(--text-primary)] tracking-tight">
          Live Threat Feed
        </h3>
        <div className="flex items-center gap-2">
          <motion.div
            className="w-1.5 h-1.5 bg-[var(--critical)] rounded-full"
            animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
            transition={{ repeat: Infinity, duration: 1.5 }}
          />
        </div>
      </div>
      <div ref={containerRef} className="flex-1 overflow-y-auto p-4 space-y-2 no-scrollbar">
        <AnimatePresence mode="popLayout">
          {alerts.map((alert) => (
            <motion.div
              key={alert.id}
              layout
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.25 }}
              className={`flex gap-3 p-3 rounded-xl border-l-2 transition-all duration-300 ${alert.glowing
                ? `bg-[var(--${alert.severity}-muted)] border-l-[var(--${alert.severity})] shadow-[var(--${alert.severity}-glow)]`
                : `bg-[var(--bg-surface)] border-l-[var(--${alert.severity})]`
                }`}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1.5">
                  <div className={`text-[var(--${alert.severity})]`}>
                    {getAlertIcon(alert.type)}
                  </div>
                  <Badge variant={alert.severity} className="text-[10px] uppercase font-bold px-1.5 py-0">
                    {alert.severity}
                  </Badge>
                  <span className="text-[10px] text-[var(--text-tertiary)] ml-auto">
                    {alert.displayTime}
                  </span>
                </div>
                <p className="text-sm font-medium text-[var(--text-primary)] truncate">
                  {alert.title}
                </p>
                <p className="text-xs text-[var(--text-tertiary)] mt-1 truncate">
                  {alert.department} • {alert.provider}
                </p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}

// Main Dashboard Component
export default function Dashboard() {
  const { metrics, findings, compliance } = mockDashboardSummary;
  const mockCostTrend = [1.2, 1.5, 1.8, 2.1, 2.4, 2.8];

  const pageVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { duration: 0.6, ease: 'easeOut' } },
  };

  const headerVariants = {
    hidden: { opacity: 0, y: -10 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
  };

  return (
    <motion.div
      variants={pageVariants}
      initial="hidden"
      animate="visible"
      className="h-full bg-[var(--bg-0)] p-6 md:p-8 overflow-hidden"
    >
      <div className="max-w-[1600px] h-full mx-auto flex flex-col gap-6">
        {/* Page Header */}
        <motion.div variants={headerVariants} className="flex-shrink-0">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-semibold tracking-tight text-[var(--text-primary)]">
              Command Center
            </h1>
            <div className="flex items-center gap-4 text-xs font-medium text-[var(--text-secondary)]">
              <span className="flex items-center gap-1.5 opacity-80">
                <span className="w-1.5 h-1.5 bg-[var(--success)] rounded-full animate-pulse" />
                Live update
              </span>
              <div className="flex gap-1 bg-[var(--bg-surface)] border border-[var(--border-subtle)] p-1 rounded-md">
                {['24h', '7d', '30d'].map((range, idx) => (
                  <button
                    key={range}
                    className={`px-3 py-1 rounded transition-all ${idx === 0
                      ? 'bg-[var(--bg-elevated)] text-[var(--text-primary)] shadow-sm'
                      : 'hover:text-[var(--text-primary)]'
                      }`}
                  >
                    {range}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Bento Box Grid */}
        <div className="flex-1 min-h-0 flex flex-col gap-6">
          {/* Top Row: VIP KPIs */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 flex-shrink-0 min-h-[160px]">
            <KPICard
              title="Total AI Cost"
              value={metrics.totalCost}
              format="currency"
              trend={{ direction: 'up', percent: 12.3 }}
              icon={DollarSign}
              sparkline={mockCostTrend}
              index={0}
            />
            <KPICard
              title="Critical Findings"
              value={findings.criticalCount}
              format="plain"
              icon={ShieldAlert}
              badge="8 NEW"
              index={1}
            />
            <ComplianceGauge score={compliance.complianceScore} index={2} />
            <KPICard
              title="Models Active"
              value={5}
              format="plain"
              icon={Brain}
              index={3}
            />
          </div>

          {/* Bottom Row: Charts & Feeds (Takes remaining height) */}
          <div className="flex-1 min-h-[400px] grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 h-full glass-card rounded-2xl">
              <ThreatDistribution distribution={mockSeverityDistribution} />
            </div>
            <div className="h-full">
              <LiveThreatFeed />
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
