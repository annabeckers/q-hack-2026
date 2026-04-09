import { useState, useEffect, useMemo, useRef } from 'react';
import { motion, AnimatePresence, useInView } from 'framer-motion';
import { KeyRound, UserX, Package, Zap, CheckCircle2, Clock, Bell, Radar } from 'lucide-react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';

import { mockAlerts } from '@/lib/mock-data';
import { Alert, AlertStatus } from '@/lib/types';

const severityColors: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
};

const alertTypeIcons: Record<string, React.FC<{ size: number; className?: string; style?: React.CSSProperties }>> = {
  secret: KeyRound,
  pii: UserX,
  slopsquat: Package,
  anomaly: Zap,
};

const typeLabels: Record<string, string> = {
  secret: 'Secret',
  pii: 'PII',
  slopsquat: 'Slopsquat',
  anomaly: 'Anomaly',
};

function getRelativeTime(timestamp: string): string {
  const now = new Date();
  const alertTime = new Date(timestamp);
  const diffMs = now.getTime() - alertTime.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

interface AlertItemProps {
  alert: Alert;
  onStatusChange: (id: string, status: AlertStatus) => void;
  isNew: boolean;
  index: number;
}

function AlertItem({ alert, onStatusChange, isNew, index }: AlertItemProps) {
  const IconComponent = alertTypeIcons[alert.type];

  const severityBadgeVariant = (sev: string) => {
    if (sev === 'critical') return 'critical' as const;
    if (sev === 'high') return 'high' as const;
    return 'medium' as const;
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -30, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, x: 100, scale: 0.9 }}
      transition={{
        type: 'spring',
        stiffness: 400,
        damping: 25,
        delay: index * 0.02,
      }}
      className="relative"
    >
      <Card
        className={`border-l-4 transition-all duration-500 overflow-hidden ${
          alert.status === 'new'
            ? 'shadow-[0_0_20px_rgba(239,68,68,0.1)]'
            : alert.status === 'acknowledged'
              ? 'opacity-80'
              : 'opacity-50'
        }`}
        style={{
          borderLeftColor: severityColors[alert.severity],
          boxShadow: isNew ? `0 0 25px ${severityColors[alert.severity]}30` : undefined,
        }}
      >
        <div className="flex gap-4">
          {/* Icon */}
          <motion.div
            className="flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: `${severityColors[alert.severity]}20` }}
            whileHover={{ scale: 1.1, rotate: 5 }}
          >
            <IconComponent size={20} style={{ color: severityColors[alert.severity] }} />
          </motion.div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-4 mb-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant={severityBadgeVariant(alert.severity)} size="sm">
                    {alert.severity.toUpperCase()}
                  </Badge>
                  <p className="font-bold text-[var(--text-primary)] truncate text-sm">{alert.title}</p>
                </div>
                <p className="text-sm text-[var(--text-secondary)] line-clamp-1">{alert.message}</p>
              </div>

              {isNew && (
                <motion.div
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="flex-shrink-0"
                >
                  <Badge variant="critical" size="sm" dot>
                    NEW
                  </Badge>
                </motion.div>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-2 mb-3">
              <Badge variant="info" size="sm">{typeLabels[alert.type]}</Badge>
              <Badge variant="neutral" size="sm">{alert.department}</Badge>
              <Badge variant="neutral" size="sm">{alert.provider}</Badge>
              <div className="flex items-center gap-1 text-xs text-[var(--text-tertiary)]">
                <Clock size={12} />
                {getRelativeTime(alert.timestamp)}
              </div>
            </div>

            <div className="flex items-center gap-2">
              {alert.status === 'new' && (
                <>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => onStatusChange(alert.id, 'acknowledged')}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--medium-muted)] text-[var(--medium)] border border-[var(--medium)]/30 hover:border-[var(--medium)]/50 transition-colors"
                  >
                    Acknowledge
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => onStatusChange(alert.id, 'resolved')}
                    className="px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--success-muted)] text-[var(--success)] border border-[var(--success)]/30 hover:border-[var(--success)]/50 transition-colors"
                  >
                    Resolve
                  </motion.button>
                </>
              )}

              {alert.status === 'acknowledged' && (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => onStatusChange(alert.id, 'resolved')}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg bg-[var(--success-muted)] text-[var(--success)] border border-[var(--success)]/30 hover:border-[var(--success)]/50 transition-colors"
                >
                  Resolve
                </motion.button>
              )}

              {alert.status === 'resolved' && (
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={16} className="text-[var(--success)]" />
                  <span className="text-xs text-[var(--success)] font-medium">Resolved</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

export default function AlertsFeed() {
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts.slice(0, 8));
  const [severityFilter, setSeverityFilter] = useState<'all' | 'critical' | 'high' | 'medium'>('all');
  const [typeFilter, setTypeFilter] = useState<'all' | 'secret' | 'pii' | 'slopsquat' | 'anomaly'>('all');
  const [newAlertIds, setNewAlertIds] = useState<Set<string>>(new Set());
  const headerRef = useRef(null);
  const headerInView = useInView(headerRef, { once: true });

  const stats = useMemo(() => {
    const critical = alerts.filter((a) => a.severity === 'critical').length;
    const high = alerts.filter((a) => a.severity === 'high').length;
    const medium = alerts.filter((a) => a.severity === 'medium').length;
    const resolved = alerts.filter((a) => a.status === 'resolved').length;
    return { critical, high, medium, resolved };
  }, [alerts]);

  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      if (severityFilter !== 'all' && alert.severity !== severityFilter) return false;
      if (typeFilter !== 'all' && alert.type !== typeFilter) return false;
      return true;
    });
  }, [alerts, severityFilter, typeFilter]);

  useEffect(() => {
    const interval = setInterval(() => {
      const availableAlerts = mockAlerts.filter((a) => !alerts.some((existing) => existing.id === a.id));

      if (availableAlerts.length > 0 && alerts.length < 25) {
        const randomAlert = availableAlerts[Math.floor(Math.random() * availableAlerts.length)];
        setNewAlertIds((prev) => new Set([...prev, randomAlert.id]));
        setAlerts((prev) => [randomAlert, ...prev]);

        setTimeout(() => {
          setNewAlertIds((prev) => {
            const next = new Set(prev);
            next.delete(randomAlert.id);
            return next;
          });
        }, 3000);
      }
    }, 4000);

    return () => clearInterval(interval);
  }, [alerts]);

  const handleStatusChange = (id: string, status: AlertStatus) => {
    setAlerts((prev) =>
      prev.map((alert) => (alert.id === id ? { ...alert, status } : alert))
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="p-6 lg:p-8 pb-12 relative min-h-full"
    >

      <div className="space-y-6 relative z-10">
        {/* Header */}
        <motion.div
          ref={headerRef}
          initial={{ opacity: 0, y: -20 }}
          animate={headerInView ? { opacity: 1, y: 0 } : undefined}
          transition={{ duration: 0.6 }}
          className="flex items-center justify-between gap-4"
        >
          <div>
            <h1 className="text-3xl lg:text-4xl font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-3">
                <Bell size={24} className="text-[var(--critical)]" />
              Real-Time Alert Feed
            </h1>
            <div className="flex items-center gap-3 mt-2">
              <motion.div
                className="flex items-center gap-2 px-3 py-1 bg-[var(--critical-muted)] rounded-full border border-[var(--critical)]/30"
                animate={{ opacity: [0.6, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              >
                <div className="relative">
                  <motion.div
                    className="w-2 h-2 bg-[var(--critical)] rounded-full"
                    animate={{ scale: [1, 1.3, 1] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  />
                  <motion.div
                    className="absolute inset-0 w-2 h-2 bg-[var(--critical)] rounded-full"
                    animate={{ scale: [1, 2.5], opacity: [0.5, 0] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  />
                </div>
                <span className="text-xs font-bold text-[var(--critical)]">LIVE</span>
              </motion.div>
              <p className="text-sm text-[var(--text-secondary)]">Active monitoring across all departments</p>
            </div>

          </div>

          <div className="text-right bg-[var(--bg-surface)] rounded-lg p-4 border border-[var(--border-subtle)]">
            <p className="text-xs text-[var(--text-tertiary)] uppercase tracking-wide mb-1">Total Alerts</p>
            <p className="text-3xl font-black text-[var(--text-primary)]">{alerts.length}</p>
          </div>
        </motion.div>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Critical', count: stats.critical, color: '#ef4444' },
            { label: 'High', count: stats.high, color: '#f97316' },
            { label: 'Medium', count: stats.medium, color: '#eab308' },
            { label: 'Resolved', count: stats.resolved, color: '#22c55e' },
          ].map((stat, idx) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.08 }}
              className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-lg p-4 text-center hover:border-[var(--border-default)] transition-all"
            >
              <p className="text-xs text-[var(--text-tertiary)] uppercase mb-2 font-semibold">{stat.label}</p>
              <p className="text-2xl font-black" style={{ color: stat.color }}>
                {stat.count}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Filters */}
        <Card header={<p className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-wide">Filters</p>}>
          <div className="space-y-4">
            <div>
              <p className="text-xs font-bold text-[var(--text-tertiary)] mb-3 uppercase">Severity</p>
              <div className="flex gap-2 flex-wrap">
                {(['all', 'critical', 'high', 'medium'] as const).map((sev) => (
                  <motion.button
                    key={sev}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setSeverityFilter(sev)}
                    className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all border ${
                      severityFilter === sev
                        ? 'border-transparent'
                        : 'bg-transparent text-[var(--text-secondary)] border-[var(--border-subtle)] hover:border-[var(--border-default)]'
                    }`}
                    style={severityFilter === sev ? { backgroundColor: '#1e3a8a', color: '#ffffff' } : undefined}
                  >
                    {sev === 'all' ? 'All Severities' : sev.charAt(0).toUpperCase() + sev.slice(1)}
                  </motion.button>
                ))}
              </div>
            </div>

            <div>
              <p className="text-xs font-bold text-[var(--text-tertiary)] mb-3 uppercase">Type</p>
              <div className="flex gap-2 flex-wrap">
                {(['all', 'secret', 'pii', 'slopsquat', 'anomaly'] as const).map((type) => (
                  <motion.button
                    key={type}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setTypeFilter(type)}
                    className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all border ${
                      typeFilter === type
                        ? 'border-transparent'
                        : 'bg-transparent text-[var(--text-secondary)] border-[var(--border-subtle)] hover:border-[var(--border-default)]'
                    }`}
                    style={typeFilter === type ? { backgroundColor: '#1e3a8a', color: '#ffffff' } : undefined}
                  >
                    {type === 'all' ? 'All Types' : typeLabels[type]}
                  </motion.button>
                ))}
              </div>
            </div>
          </div>
        </Card>

        {/* Alert Feed */}
        <div className="space-y-3">
          <AnimatePresence mode="popLayout">
            {filteredAlerts.length > 0 ? (
              filteredAlerts.map((alert, index) => (
                <AlertItem
                  key={alert.id}
                  alert={alert}
                  onStatusChange={handleStatusChange}
                  isNew={newAlertIds.has(alert.id)}
                  index={index}
                />
              ))
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-center py-12"
              >
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
                  className="inline-block mb-3"
                >
                  <Radar size={32} className="text-[var(--accent)]" />
                </motion.div>
                <p className="text-[var(--text-secondary)]">No alerts match your filters</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}
