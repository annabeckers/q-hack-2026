import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence, useInView } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
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
  Radar,
  ArrowUpRight,
  ArrowDownRight,
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

// ───
// Utility
// ───
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

// ───
// Sparkline
// ───
function Sparkline({ values, color = 'var(--accent)' }: { values: number[]; color?: string }) {
  if (values.length < 2) return null;
  const w = 80, h = 24, pad = 2;
  const min = Math.min(...values), max = Math.max(...values);
  const range = max - min || 1;
  const pts = values.map((v, i) => ({
    x: pad + (i / (values.length - 1)) * (w - 2 * pad),
    y: h - pad - ((v - min) / range) * (h - 2 * pad),
  }));
  const pathD = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const areaD = `${pathD} L ${pts[pts.length - 1].x} ${h} L ${pts[0].x} ${h} Z`;

  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="w-full">
      <defs>
        <linearGradient id={`sg-${color.replace(/[^a-z0-9]/g, '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.25" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <motion.path d={areaD} fill={`url(#sg-${color.replace(/[^a-z0-9]/g, '')})`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.8, delay: 0.3 }} />
      <motion.path d={pathD} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.2, ease: 'easeOut' }} />
    </svg>
  );
}

// ───
// Compliance Ring
// ───
function ComplianceRing({ score, idx }: { score: number; idx: number }) {
  const r = 40, circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });
  const color = score >= 80 ? 'var(--success)' : score >= 60 ? 'var(--medium)' : 'var(--critical)';

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 20 }} animate={inView ? { opacity: 1, y: 0 } : undefined} transition={{ delay: idx * 0.08, duration: 0.5 }}>
      <Card className="h-full flex flex-col items-center justify-center py-6">
        <div className="relative w-24 h-24 flex items-center justify-center mb-3">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r={r} fill="none" stroke="var(--border-subtle)" strokeWidth="5" />
            <motion.circle cx="60" cy="60" r={r} fill="none" stroke={color} strokeWidth="5" strokeDasharray={circ} strokeLinecap="round" initial={{ strokeDashoffset: circ }} animate={inView ? { strokeDashoffset: offset } : undefined} transition={{ delay: 0.3, duration: 1.8, ease: 'easeOut' }} style={{ filter: `drop-shadow(0 0 6px ${color})` }} />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-2xl font-bold text-[var(--text-primary)] tabular-nums"><CountUp target={score} /></span>
          </div>
        </div>
        <p className="text-[11px] font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">EU AI Act</p>
      </Card>
    </motion.div>
  );
}

// ───
// KPI Card
// ───
function KPICard({ title, value, format = 'plain', trend, icon: Icon, sparkline, index, badge, children }: {
  title: string; value?: number; format?: 'currency' | 'percentage' | 'plain';
  trend?: { direction: 'up' | 'down'; percent: number; good?: boolean };
  icon?: React.ComponentType<{ size: number; className?: string }>; sparkline?: number[];
  index: number; badge?: string; children?: React.ReactNode;
}) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });
  const TrendIcon = trend?.direction === 'up' ? ArrowUpRight : ArrowDownRight;

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 20 }} animate={inView ? { opacity: 1, y: 0 } : undefined} transition={{ delay: index * 0.08, duration: 0.5 }}>
      <Card className="h-full">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">{title}</span>
            {Icon && (
              <div className="p-1.5 rounded-md bg-[var(--accent-muted)]">
                <Icon size={14} className="text-[var(--accent)]" />
              </div>
            )}
          </div>
          {value !== undefined && (
            <div className="space-y-2">
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-[var(--text-primary)] tabular-nums tracking-tight">
                  <CountUp target={value} format={format} />
                </span>
                {trend && (
                  <motion.span initial={{ opacity: 0 }} animate={inView ? { opacity: 1 } : undefined} transition={{ delay: 0.4 }}
                    className={`inline-flex items-center gap-0.5 text-xs font-semibold px-1.5 py-0.5 rounded ${
                      trend.good ? 'bg-[var(--success-muted)] text-[var(--success)]' : 'bg-[var(--critical-muted)] text-[var(--critical)]'
                    }`}
                  >
                    <TrendIcon size={12} />{trend.percent}%
                  </motion.span>
                )}
              </div>
              {sparkline && sparkline.length > 1 && <div className="h-6"><Sparkline values={sparkline} /></div>}
            </div>
          )}
          {badge && <Badge variant="critical" size="sm" dot>{badge}</Badge>}
          {children}
        </div>
      </Card>
    </motion.div>
  );
}

// ───
// Threat Distribution
// ───
function ThreatDistribution({ distribution }: { distribution: types.SeverityDistribution }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });
  const data = [
    { category: 'Secrets', critical: distribution.secrets.critical, high: distribution.secrets.high, medium: distribution.secrets.medium },
    { category: 'PII', critical: distribution.pii.critical, high: distribution.pii.high, medium: distribution.pii.medium },
    { category: 'Slopsquatting', critical: distribution.slopsquat.critical, high: distribution.slopsquat.high, medium: distribution.slopsquat.medium },
  ];
  const total = data.reduce((s, d) => s + d.critical + d.high + d.medium, 0);

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 20 }} animate={inView ? { opacity: 1, y: 0 } : undefined} transition={{ duration: 0.5 }}>
      <Card header={<div className="flex items-center justify-between"><div className="flex items-center gap-2"><Radar size={16} className="text-[var(--accent)]" /><span className="font-semibold text-[var(--text-primary)] text-sm">Threat Distribution</span></div><span className="text-xs text-[var(--text-tertiary)] tabular-nums">{total} total</span></div>}>
        <div className="space-y-4">
          <div className="flex gap-4 text-[11px]">
            {[{ l: 'Critical', c: 'var(--critical)' }, { l: 'High', c: 'var(--high)' }, { l: 'Medium', c: 'var(--medium)' }].map(i =>
              <div key={i.l} className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-sm" style={{ background: i.c }} /><span className="text-[var(--text-secondary)]">{i.l}</span></div>
            )}
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
              <XAxis dataKey="category" stroke="var(--border-subtle)" tick={{ fill: 'var(--text-tertiary)', fontSize: 11 }} axisLine={{ stroke: 'var(--border-subtle)' }} />
              <YAxis stroke="var(--border-subtle)" tick={{ fill: 'var(--text-tertiary)', fontSize: 11 }} axisLine={{ stroke: 'var(--border-subtle)' }} />
              <Tooltip contentStyle={{ backgroundColor: '#ffffff', border: '1px solid var(--border-default)', borderRadius: '8px', boxShadow: '0 8px 24px rgba(20,27,65,0.1)' }} cursor={{ fill: 'rgba(20,27,65,0.02)' }} />
              <Bar dataKey="critical" fill="var(--critical)" stackId="s" radius={[3, 3, 0, 0]} />
              <Bar dataKey="high" fill="var(--high)" stackId="s" />
              <Bar dataKey="medium" fill="var(--medium)" stackId="s" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </motion.div>
  );
}

// ───
// Recent Detections
// ───
function RecentDetections({ findings }: { findings: types.Finding[] }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });
  const sorted = findings.sort((a, b) => new Date(b.detectedAt).getTime() - new Date(a.detectedAt).getTime()).slice(0, 6);

  const icon = (type: types.FindingType) => {
    switch (type) {
      case 'secret': return <KeyRound size={13} className="text-[var(--critical)]" />;
      case 'pii': return <UserX size={13} className="text-[var(--critical)]" />;
      case 'slopsquat': return <Package size={13} className="text-[var(--high)]" />;
      default: return <Zap size={13} className="text-[var(--medium)]" />;
    }
  };

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 20 }} animate={inView ? { opacity: 1, y: 0 } : undefined} transition={{ duration: 0.5 }}>
      <Card header={<div className="flex items-center justify-between"><span className="font-semibold text-[var(--text-primary)] text-sm">Recent Detections</span><motion.a href="/leaks" whileHover={{ x: 3 }} className="text-[11px] text-[var(--accent)] font-semibold">View All →</motion.a></div>}>
        <div className="space-y-1">
          {sorted.map((item, idx) => (
            <motion.div key={item.id} initial={{ opacity: 0, x: -10 }} animate={inView ? { opacity: 1, x: 0 } : undefined} transition={{ delay: idx * 0.05 }}
              className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-[var(--bg-2)] transition-colors cursor-pointer group"
            >
              <div className="flex-shrink-0">{icon(item.type)}</div>
              <div className="flex-1 min-w-0">
                <p className="text-[13px] font-medium text-[var(--text-primary)] truncate group-hover:text-[var(--accent)] transition-colors">{item.category}</p>
                <p className="text-[11px] text-[var(--text-tertiary)]">{item.department} · {item.provider} · {formatRelativeTime(item.detectedAt)}</p>
              </div>
              <Badge variant={item.severity} size="sm">{item.severity.toUpperCase()}</Badge>
            </motion.div>
          ))}
        </div>
      </Card>
    </motion.div>
  );
}

// ───
// Live Threat Feed
// ───
interface StreamAlert extends types.Alert { displayTime: string; glowing: boolean; }

function LiveThreatFeed() {
  const [alerts, setAlerts] = useState<StreamAlert[]>([]);
  const [queue, setQueue] = useState<types.Alert[]>(mockAlerts.slice().reverse());

  useEffect(() => {
    const iv = setInterval(() => {
      setQueue(q => {
        if (q.length === 0) return mockAlerts.slice().reverse();
        const next = q[0];
        setAlerts(curr => [
          { ...next, displayTime: formatRelativeTime(next.timestamp), glowing: true },
          ...curr.map(a => ({ ...a, glowing: false })),
        ].slice(0, 20));
        return q.slice(1);
      });
    }, 2500);
    return () => clearInterval(iv);
  }, []);

  const getIcon = (t: types.AlertType) => {
    switch (t) { case 'secret': return <KeyRound size={13} />; case 'pii': return <UserX size={13} />; case 'slopsquat': return <Package size={13} />; case 'anomaly': return <Zap size={13} />; }
  };
  const getColor = (s: string) => s === 'critical' ? 'var(--critical)' : s === 'high' ? 'var(--high)' : 'var(--medium)';

  return (
    <Card header={
      <div className="flex items-center justify-between">
        <span className="font-semibold text-[var(--text-primary)] text-sm">Live Threat Feed</span>
        <div className="flex items-center gap-1.5">
          <div className="relative"><motion.div className="w-2 h-2 bg-[var(--critical)] rounded-full" animate={{ scale: [1, 1.3, 1] }} transition={{ repeat: Infinity, duration: 1.5 }} /><motion.div className="absolute inset-0 w-2 h-2 bg-[var(--critical)] rounded-full" animate={{ scale: [1, 2.5], opacity: [0.5, 0] }} transition={{ repeat: Infinity, duration: 1.5 }} /></div>
          <span className="text-[10px] font-bold text-[var(--critical)] uppercase tracking-wide">Live</span>
        </div>
      </div>
    } className="relative flex flex-col overflow-hidden" style={{ height: 'calc(100%)' }}>
      {/* Scan line */}
      <motion.div className="absolute left-0 right-0 h-[1px] z-10 pointer-events-none" style={{ background: 'linear-gradient(90deg, transparent, rgba(30,58,138,0.2), transparent)' }} animate={{ top: ['0%', '100%'] }} transition={{ duration: 5, repeat: Infinity, ease: 'linear' }} />

      <div className="flex-1 overflow-y-auto space-y-1 relative">
        <AnimatePresence mode="popLayout">
          {alerts.map(a => (
            <motion.div key={a.id} layout initial={{ opacity: 0, y: -20, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, x: 30, scale: 0.95 }} transition={{ type: 'spring', stiffness: 400, damping: 25 }}
              className="flex gap-2.5 p-2.5 rounded-lg border-l-2 transition-all"
              style={{ borderLeftColor: getColor(a.severity), background: a.glowing ? 'rgba(30,58,138,0.03)' : 'transparent', boxShadow: a.glowing ? `0 0 12px ${getColor(a.severity)}15` : 'none' }}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 mb-0.5 flex-wrap">
                  <span style={{ color: getColor(a.severity) }}>{getIcon(a.type)}</span>
                  <Badge variant={a.severity as 'critical' | 'high' | 'medium'} size="sm">{a.severity.toUpperCase()}</Badge>
                  <span className="text-[10px] text-[var(--text-tertiary)]">{a.displayTime}</span>
                  {a.glowing && <motion.span initial={{ opacity: 0, scale: 0 }} animate={{ opacity: 1, scale: 1 }} className="text-[9px] font-bold text-[var(--critical)] bg-[var(--critical-muted)] px-1 py-0.5 rounded">NEW</motion.span>}
                </div>
                <p className="text-[13px] font-medium text-[var(--text-primary)] truncate">{a.title}</p>
                <p className="text-[11px] text-[var(--text-tertiary)] truncate">{a.department} · {a.provider}</p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        {alerts.length === 0 && (
          <div className="flex flex-col items-center justify-center h-24 text-[var(--text-tertiary)] gap-2">
            <motion.div animate={{ rotate: 360 }} transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}><Radar size={20} className="text-[var(--accent)]" /></motion.div>
            <p className="text-xs">Scanning...</p>
          </div>
        )}
      </div>
    </Card>
  );
}

// ───
// Models Indicator
// ───
function ModelsActive() {
  const p = [{ n: 'GPT-4o', c: 'var(--openai)' }, { n: 'Claude', c: 'var(--anthropic)' }, { n: 'Gemini', c: 'var(--google)' }, { n: 'Mistral', c: 'var(--mistral)' }, { n: 'Local', c: 'var(--local)' }];
  return (
    <div className="space-y-2 mt-1">
      <div className="flex gap-1.5">
        {p.map((m, i) => (
          <motion.div key={m.n} initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: 0.5 + i * 0.06, type: 'spring', stiffness: 400 }} whileHover={{ scale: 1.4 }}
            className="w-2.5 h-2.5 rounded-full cursor-pointer" style={{ background: m.c }} title={m.n}
          />
        ))}
      </div>
      <p className="text-[11px] text-[var(--text-tertiary)]">5 providers · 7 departments</p>
    </div>
  );
}

// ───
// Insight Bar
// ───
function InsightBar() {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });
  const items = [
    { icon: TrendingUp, label: 'Top cost driver', value: 'Engineering', detail: '€18.2K/month', color: 'var(--accent)' },
    { icon: AlertTriangle, label: 'Riskiest model', value: 'GPT-4o', detail: '4.2 hallucinations/1K', color: 'var(--high)' },
    { icon: EyeOff, label: 'Shadow AI', value: '3 unapproved', detail: 'providers detected', color: 'var(--critical)' },
  ];

  return (
    <motion.div ref={ref} className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {items.map((s, i) => (
        <motion.div key={s.label} initial={{ opacity: 0, y: 15 }} animate={inView ? { opacity: 1, y: 0 } : undefined} transition={{ delay: i * 0.08 }}>
          <Card>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg" style={{ background: `color-mix(in srgb, ${s.color} 12%, transparent)` }}>
                <s.icon size={15} style={{ color: s.color }} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[11px] font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">{s.label}</p>
                <p className="text-sm font-bold text-[var(--text-primary)] mt-0.5">{s.value}</p>
                <p className="text-[11px] text-[var(--text-tertiary)]">{s.detail}</p>
              </div>
            </div>
          </Card>
        </motion.div>
      ))}
    </motion.div>
  );
}

// ═══════════════════════════════════════════
// MAIN DASHBOARD
// ═══════════════════════════════════════════
export default function Dashboard() {
  const { metrics, findings, compliance } = mockDashboardSummary;
  const costTrend = [1.2, 1.5, 1.8, 2.1, 2.4, 2.8, 3.1, 2.9];
  const [activeRange, setActiveRange] = useState(0);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }} className="p-6 lg:p-8 relative min-h-full">
      <div className="space-y-6 relative z-10">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -15 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <div className="flex items-end justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-3xl lg:text-4xl font-bold text-[var(--text-primary)] tracking-tight">
                Command Center
              </h1>
              <p className="text-sm text-[var(--text-tertiary)] mt-1 flex items-center gap-2">
                Real-time AI usage monitoring
                <span className="inline-flex items-center gap-1">
                  <motion.span className="w-1.5 h-1.5 bg-[var(--success)] rounded-full" animate={{ opacity: [0.5, 1, 0.5] }} transition={{ repeat: Infinity, duration: 1.5 }} />
                  <span className="text-[var(--success)] text-xs font-medium">Live</span>
                </span>
              </p>
            </div>
            <div className="flex gap-1.5">
              {['24h', '7d', '30d', '90d'].map((r, i) => (
                <motion.button key={r} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 + i * 0.04 }}
                  onClick={() => setActiveRange(i)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
                    i === activeRange
                      ? 'text-white border-transparent'
                      : 'bg-transparent text-[var(--text-secondary)] border-[var(--border-subtle)] hover:border-[var(--border-default)]'
                  }`}
                  style={i === activeRange ? { backgroundColor: '#1e3a8a' } : undefined}
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                >
                  {r}
                </motion.button>
              ))}
            </div>
          </div>
        </motion.div>

        {/* KPI Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KPICard title="Total AI Cost" value={metrics.totalCost} format="currency" trend={{ direction: 'up', percent: 12.3, good: false }} icon={DollarSign} sparkline={costTrend} index={0} />
          <KPICard title="Critical Findings" value={findings.criticalCount} icon={ShieldAlert} badge="8 unresolved" index={1} />
          <ComplianceRing score={compliance.complianceScore} idx={2} />
          <KPICard title="Active Models" value={5} icon={Brain} index={3}><ModelsActive /></KPICard>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-4">
            <ThreatDistribution distribution={mockSeverityDistribution} />
            <RecentDetections findings={mockFindings} />
          </div>
          <div className="min-h-[500px]">
            <LiveThreatFeed />
          </div>
        </div>

        {/* Insight Bar */}
        <InsightBar />
      </div>
    </motion.div>
  );
}
