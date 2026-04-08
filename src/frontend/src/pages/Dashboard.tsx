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

// Premium KPI Card
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
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { delay: index * 0.08, duration: 0.5, ease: 'easeOut' },
    },
  };

  return (
    <motion.div variants={containerVariants}>
      <Card className="h-full relative overflow-hidden group hover:shadow-lg hover:shadow-[var(--accent-glow)] transition-all duration-300">
        {/* Icon background circle */}
        {Icon && (
          <div className="absolute -right-8 -top-8 w-24 h-24 bg-[var(--accent)] opacity-5 rounded-full group-hover:opacity-10 transition-opacity" />
        )}

        <div className="relative space-y-4">
          <div className="flex items-start justify-between">
            <h3 className="text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">
              {title}
            </h3>
            {Icon && (
              <div className="p-2 bg-[var(--bg-surface)] rounded-md">
                <Icon size={16} className="text-[var(--accent)]" />
              </div>
            )}
          </div>

          {value !== undefined ? (
            <div className="space-y-3">
              <div className="flex items-baseline gap-2">
                <div className="text-5xl font-bold text-[var(--text-primary)] leading-none">
                  <CountUp target={value} format={format} />
                </div>
                {trend && (
                  <div
                    className={`text-sm font-semibold flex items-center gap-1 px-2 py-1 rounded ${
                      trend.direction === 'up'
                        ? 'bg-[var(--critical-muted)] text-[var(--critical)]'
                        : 'bg-[var(--success-muted)] text-[var(--success)]'
                    }`}
                  >
                    <span>{trend.direction === 'up' ? '↑' : '↓'}</span>
                    {trend.percent}%
                  </div>
                )}
              </div>

              {sparkline && sparkline.length > 1 && (
                <div className="h-6 -mx-2">
                  <Sparkline values={sparkline} />
                </div>
              )}
            </div>
          ) : null}

          {badge && (
            <div className="flex gap-2 pt-2">
              <Badge variant="critical" className="text-xs animate-pulse">
                {badge}
              </Badge>
            </div>
          )}
        </div>
      </Card>
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

// Recent Detections Timeline
function RecentDetections({ findings }: { findings: types.Finding[] }) {
  const sorted = findings
    .sort((a, b) => new Date(b.detectedAt).getTime() - new Date(a.detectedAt).getTime())
    .slice(0, 8);

  const getTypeIcon = (type: types.FindingType) => {
    switch (type) {
      case 'secret':
        return <KeyRound size={14} className="text-[var(--critical)]" />;
      case 'pii':
        return <UserX size={14} className="text-[var(--critical)]" />;
      case 'slopsquat':
        return <Package size={14} className="text-[var(--high)]" />;
      default:
        return <Zap size={14} className="text-[var(--medium)]" />;
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
        delayChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -10 },
    visible: { opacity: 1, x: 0, transition: { duration: 0.3 } },
  };

  return (
    <motion.div variants={containerVariants} initial="hidden" whileInView="visible">
      <Card header={
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-[var(--text-primary)]">
            Recent Detections
          </h3>
          <a href="/leaks" className="text-xs text-[var(--accent)] hover:text-[var(--accent-hover)] font-semibold">
            View All →
          </a>
        </div>
      } className="relative overflow-hidden">
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {sorted.map((item, idx) => (
            <motion.div
              key={item.id}
              variants={itemVariants}
              className={`flex items-start gap-3 p-3 rounded-md transition-colors ${
                idx % 2 === 0 ? 'bg-[var(--bg-2)]' : ''
              } hover:bg-[var(--bg-surface-hover)]`}
            >
              <div className="pt-0.5 flex-shrink-0">
                {getTypeIcon(item.type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge
                    variant={item.severity}
                    className="text-xs"
                  >
                    {item.severity.toUpperCase()}
                  </Badge>
                  <span className="text-xs text-[var(--text-secondary)]">
                    {item.type.toUpperCase()}
                  </span>
                </div>
                <p className="text-sm font-medium text-[var(--text-primary)] mt-1 truncate">
                  {item.category}
                </p>
                <div className="flex gap-3 mt-1 text-xs text-[var(--text-tertiary)]">
                  <span>{item.department}</span>
                  <span>•</span>
                  <span>{item.provider}</span>
                  <span>•</span>
                  <span>{formatRelativeTime(item.detectedAt)}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </Card>
    </motion.div>
  );
}

// Real-Time Alert Feed - THE WOW FEATURE
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
        if (queue.length === 0) {
          // Cycle back
          return mockAlerts.slice().reverse();
        }

        const newAlert = queue[0];
        const updatedQueue = queue.slice(1);

        setAlerts((current) => {
          const updated = [
            {
              ...newAlert,
              displayTime: formatRelativeTime(newAlert.timestamp),
              glowing: true,
            },
            ...current.map(a => ({ ...a, glowing: false })),
          ];
          return updated.slice(0, 20);
        });

        return updatedQueue;
      });
    }, 2500);

    return () => clearInterval(interval);
  }, []);

  const getAlertIcon = (type: types.AlertType) => {
    switch (type) {
      case 'secret':
        return <KeyRound size={14} />;
      case 'pii':
        return <UserX size={14} />;
      case 'slopsquat':
        return <Package size={14} />;
      case 'anomaly':
        return <Zap size={14} />;
    }
  };

  return (
    <Card header={
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-[var(--text-primary)]">
          Live Threat Feed
        </h3>
        <div className="flex items-center gap-2">
          <motion.div
            className="w-2 h-2 bg-[var(--critical)] rounded-full"
            animate={{ scale: [1, 1.3, 1] }}
            transition={{ repeat: Infinity, duration: 1.5 }}
          />
          <span className="text-xs font-bold text-[var(--critical)] uppercase tracking-wider">
            Live
          </span>
        </div>
      </div>
    } className="relative h-[600px] flex flex-col overflow-hidden">
      <div ref={containerRef} className="flex-1 overflow-y-auto space-y-1.5">
        <AnimatePresence mode="popLayout">
          {alerts.map((alert, idx) => (
            <motion.div
              key={alert.id}
              layout
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              transition={{ duration: 0.25 }}
              className={`flex gap-3 p-3 rounded-md border-l-4 ${
                alert.glowing
                  ? `bg-[var(--${alert.severity}-muted)] border-l-[var(--${alert.severity})] shadow-${alert.severity}-glow`
                  : `bg-[var(--bg-surface)] border-l-[var(--${alert.severity})]`
              } transition-all duration-300`}
              style={{
                boxShadow: alert.glowing ? `0 0 12px var(--${alert.severity}-glow)` : 'none',
              }}
            >
              {/* Severity bar indicator */}
              <div className={`w-1 rounded-full flex-shrink-0 bg-[var(--${alert.severity})]`} />

              <div className="flex-1 min-w-0 py-0.5">
                <div className="flex items-center gap-2 mb-1">
                  <div className={`text-[var(--${alert.severity})]`}>
                    {getAlertIcon(alert.type)}
                  </div>
                  <Badge variant={alert.severity} className="text-xs">
                    {alert.severity.toUpperCase()}
                  </Badge>
                  <span className="text-xs text-[var(--text-tertiary)]">
                    {alert.displayTime}
                  </span>
                </div>
                <p className="text-sm font-semibold text-[var(--text-primary)] truncate">
                  {alert.title}
                </p>
                <p className="text-xs text-[var(--text-tertiary)] mt-0.5 truncate">
                  {alert.department} • {alert.provider}
                </p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {alerts.length === 0 && (
          <div className="flex items-center justify-center h-32 text-[var(--text-tertiary)]">
            <p className="text-sm">Listening for live alerts...</p>
          </div>
        )}
      </div>
    </Card>
  );
}

// Models Indicator
function ModelsActive() {
  const providers = [
    { name: 'GPT-4o', color: 'var(--openai)' },
    { name: 'Claude', color: 'var(--anthropic)' },
    { name: 'Gemini', color: 'var(--google)' },
    { name: 'Mistral', color: 'var(--mistral)' },
    { name: 'Local', color: 'var(--local)' },
  ];

  return (
    <div className="space-y-4">
      <div className="flex gap-2 items-center">
        {providers.map((p, i) => (
          <motion.div
            key={p.name}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: i * 0.06, duration: 0.3 }}
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: p.color }}
            title={p.name}
          />
        ))}
      </div>
      <p className="text-xs text-[var(--text-secondary)]">
        5 providers across 7 departments
      </p>
    </div>
  );
}

// Bottom Stats Bar
function InsightBar() {
  const stats = [
    {
      icon: TrendingUp,
      label: 'Top Cost',
      value: 'Engineering',
      detail: '€18.2K',
    },
    {
      icon: AlertTriangle,
      label: 'Riskiest Model',
      value: 'GPT-4o',
      detail: '4.2 halluc/1K',
    },
    {
      icon: EyeOff,
      label: 'Shadow AI',
      value: '3 providers',
      detail: 'unapproved',
    },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.4,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      whileInView="visible"
      className="grid grid-cols-3 gap-4"
    >
      {stats.map((stat) => (
        <motion.div key={stat.label} variants={itemVariants}>
          <Card className="group hover:shadow-lg transition-all hover:shadow-[var(--accent-glow)]">
            <div className="flex items-start gap-3">
              <div className="p-2.5 bg-[var(--bg-surface)] rounded-lg group-hover:bg-[var(--bg-surface-hover)] transition-colors">
                <stat.icon size={16} className="text-[var(--accent)]" />
              </div>
              <div className="flex-1">
                <p className="text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">
                  {stat.label}
                </p>
                <p className="text-sm font-bold text-[var(--text-primary)] mt-1">
                  {stat.value}
                </p>
                <p className="text-xs text-[var(--text-tertiary)] mt-0.5">
                  {stat.detail}
                </p>
              </div>
            </div>
          </Card>
        </motion.div>
      ))}
    </motion.div>
  );
}

// Main Dashboard Component
export default function Dashboard() {
  const { metrics, findings, compliance } = mockDashboardSummary;
  const mockCostTrend = [1.2, 1.5, 1.8, 2.1, 2.4, 2.8];

  const pageVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        duration: 0.6,
        ease: 'easeOut',
      },
    },
  };

  const headerVariants = {
    hidden: { opacity: 0, y: -20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.6, ease: 'easeOut' },
    },
  };

  return (
    <motion.div
      variants={pageVariants}
      initial="hidden"
      animate="visible"
      className="min-h-screen bg-[var(--bg-0)] p-6 md:p-8"
    >
      <div className="max-w-[1600px] mx-auto space-y-8">
        {/* Page Header with Scan-line Effect */}
        <motion.div variants={headerVariants} className="relative">
          <div className="space-y-2">
            <div className="flex items-baseline gap-4">
              <h1 className="text-5xl md:text-6xl font-black text-[var(--text-primary)]">
                Command Center
              </h1>
              <div className="h-1 flex-1 bg-gradient-to-r from-[var(--accent)] to-transparent rounded-full" />
            </div>
            <div className="flex items-center gap-3 text-sm text-[var(--text-secondary)]">
              <span>Real-time AI usage monitoring</span>
              <span>•</span>
              <span className="flex items-center gap-1.5">
                <motion.span
                  className="w-1.5 h-1.5 bg-[var(--success)] rounded-full"
                  animate={{ scale: [1, 1.5, 1] }}
                  transition={{ repeat: Infinity, duration: 1.2 }}
                />
                Last updated: 2 min ago
              </span>
            </div>
          </div>

          {/* Time Range Selector */}
          <div className="mt-4 flex gap-2">
            {['24h', '7d', '30d', '90d'].map((range, idx) => (
              <motion.button
                key={range}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.05 }}
                className={`px-4 py-2 rounded-md text-xs font-semibold transition-all ${
                  idx === 0
                    ? 'bg-[var(--accent)] text-white'
                    : 'bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:bg-[var(--bg-surface-hover)]'
                }`}
              >
                {range}
              </motion.button>
            ))}
          </div>
        </motion.div>

        {/* KPI Strip - 4 Premium Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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
          >
            <ModelsActive />
          </KPICard>
        </div>

        {/* Main Grid: 2-column (7fr 5fr) + Live Feed on right */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 auto-rows-max">
          {/* Left Column (wider) */}
          <div className="lg:col-span-2 space-y-6">
            {/* Threat Distribution Chart */}
            <ThreatDistribution distribution={mockSeverityDistribution} />

            {/* Recent Detections Timeline */}
            <RecentDetections findings={mockFindings} />
          </div>

          {/* Right Column: Live Threat Feed (full height) */}
          <div className="lg:row-span-2">
            <LiveThreatFeed />
          </div>
        </div>

        {/* Bottom Insight Bar */}
        <InsightBar />
      </div>
    </motion.div>
  );
}
