import { useState, useMemo } from 'react';
import { motion, useInView } from 'framer-motion';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useRef } from 'react';
import { Shield, Radar } from 'lucide-react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Modal from '@/components/ui/Modal';

import { mockFindings, mockSeverityDistribution, mockSlopsquattingStats, mockContextRisk } from '@/lib/mock-data';
import { apiClient } from '@/lib/api';
import { useApiCall } from '@/hooks/useApiCall';
import type * as types from '@/lib/types';

const PROVIDER_COLORS: Record<string, string> = {
  OpenAI: '#10b981',
  Anthropic: '#f59e0b',
  Google: '#3b82f6',
  Mistral: '#8b5cf6',
  Local: '#ef5350',
};

export default function SecurityIntelligence() {
  const [filterType, setFilterType] = useState<types.FindingType>('all');
  const [selectedFinding, setSelectedFinding] = useState<types.FindingDetail | null>(null);
  const [sortBy, setSortBy] = useState<keyof types.Finding>('detectedAt');
  const [sortDesc, setSortDesc] = useState(true);
  const headerRef = useRef(null);
  const headerInView = useInView(headerRef, { once: true });

  // ── API calls with mock fallback ──
  const { data: findingsRaw } = useApiCall(
    () => apiClient.getFindings({ limit: 100 }).then(r => {
      if (Array.isArray(r)) return r as types.Finding[];
      if (r && 'items' in r) return (r as any).items as types.Finding[];
      return mockFindings;
    }),
    mockFindings
  );

  const { data: severityDist } = useApiCall(
    () => apiClient.getSeverityDistribution(),
    mockSeverityDistribution
  );

  const { data: slopsquattingStats } = useApiCall(
    () => apiClient.getSlopsquattingByModel(),
    mockSlopsquattingStats
  );

  const { data: contextRisk } = useApiCall(
    () => apiClient.getContextRisk(10),
    mockContextRisk
  );

  const filteredFindings = useMemo(() => {
    let filtered = findingsRaw;
    if (filterType !== 'all') {
      filtered = filtered.filter((f) => f.type === filterType);
    }
    return [...filtered].sort((a, b) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortDesc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
      }
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDesc ? bVal - aVal : aVal - bVal;
      }
      return 0;
    });
  }, [findingsRaw, filterType, sortBy, sortDesc]);

  const totalFindings = filteredFindings.length;

  const slopsquattingData = slopsquattingStats.map((stat) => ({
    name: stat.provider,
    count: stat.hallucCount,
  }));

  const handleFindingClick = (finding: types.Finding) => {
    // Try to fetch detail from API, fall back to constructing from finding
    apiClient.getFindingDetail(finding.id).then(detail => {
      setSelectedFinding(detail);
    }).catch(() => {
      const detail: types.FindingDetail = {
        ...finding,
        fullContext: finding.contextPreview + '\n\n... [Additional context with surrounding data] ...',
        remediationHistory: [
          {
            timestamp: finding.detectedAt,
            oldStatus: 'new',
            newStatus: finding.status,
            notes: 'Finding detected and logged',
            actor: 'security-scanner',
          },
        ],
        relatedFindings: [],
        duplicateCount: Math.floor(Math.random() * 5),
      };
      setSelectedFinding(detail);
    });
  };

  const handleSort = (column: keyof types.Finding) => {
    if (sortBy === column) {
      setSortDesc(!sortDesc);
    } else {
      setSortBy(column);
      setSortDesc(true);
    }
  };

  const severityPanel = (
    title: string,
    severity: types.SeverityBucket,
    accentColor: string,
    idx: number,
  ) => {
    const panelRef = useRef(null);
    const inView = useInView(panelRef, { once: true });

    return (
      <motion.div
        ref={panelRef}
        initial={{ opacity: 0, y: 20 }}
        animate={inView ? { opacity: 1, y: 0 } : undefined}
        transition={{ duration: 0.5, delay: idx * 0.1 }}
      >
        <Card className="overflow-hidden border-l-4 group" style={{ borderLeftColor: accentColor }}>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[var(--text-primary)]">{title}</h3>
              <div className="text-lg font-extrabold" style={{ color: accentColor }}>
                {severity.critical + severity.high + severity.medium}
              </div>
            </div>

            <div className="space-y-2">
              {[
                { label: 'Critical', value: severity.critical, color: '#ef4444' },
                { label: 'High', value: severity.high, color: '#f97316' },
                { label: 'Medium', value: severity.medium, color: '#eab308' },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-[var(--text-secondary)]">{item.label}</span>
                  </div>
                  <span className="font-bold text-[var(--text-primary)]">{item.value}</span>
                </div>
              ))}
            </div>

            <div className="pt-2 border-t border-[var(--border-subtle)]">
              <div className="h-2 bg-[var(--bg-surface-hover)] rounded-full overflow-hidden flex">
                {[
                  { value: severity.critical, color: '#ef4444' },
                  { value: severity.high, color: '#f97316' },
                  { value: severity.medium, color: '#eab308' },
                ].map((seg, i) => {
                  const total = severity.critical + severity.high + severity.medium;
                  const width = total > 0 ? (seg.value / total) * 100 : 0;
                  return (
                    <motion.div
                      key={i}
                      className="h-full"
                      style={{ backgroundColor: seg.color }}
                      initial={{ width: 0 }}
                      animate={inView ? { width: `${width}%` } : undefined}
                      transition={{ duration: 0.8, delay: 0.3 + i * 0.1 }}
                    />
                  );
                })}
              </div>
            </div>
          </div>
        </Card>
      </motion.div>
    );
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
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="flex items-center justify-between"
        >
          <div>
            <h1 className="text-3xl lg:text-4xl font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-3">
              <Shield size={28} className="text-[var(--accent)]" />
              Security Intelligence
            </h1>
            <p className="text-sm text-[var(--text-tertiary)] mt-1">Detect and track data exposure risks across AI usage</p>
          </div>
          <Badge variant="critical" className="px-4 py-2" dot>
            {totalFindings} findings
          </Badge>
        </motion.div>


        {/* Severity Panels */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {severityPanel('Secrets', severityDist.secrets, '#ef4444', 0)}
          {severityPanel('PII', severityDist.pii, '#f59e0b', 1)}
          {severityPanel('Slopsquatting', severityDist.slopsquat, '#8b5cf6', 2)}
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="lg:col-span-2"
          >
            <Card header={
              <div className="flex items-center gap-2">
                <Radar size={16} className="text-[var(--accent)]" />
                <h3 className="font-bold text-[var(--text-primary)]">Slopsquatting by Model</h3>
              </div>
            }>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={slopsquattingData} layout="vertical" margin={{ top: 5, right: 30, bottom: 5, left: 100 }}>
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
                    cursor={{ fill: 'var(--accent-muted)' }}
                  />
                  <Bar dataKey="count" fill="var(--accent)" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <Card header={<h3 className="font-bold text-[var(--text-primary)]">Context Exposure Risk</h3>}>
              <div className="space-y-2 max-h-[350px] overflow-y-auto">
                {contextRisk.slice(0, 10).map((session, idx) => (
                  <motion.div
                    key={session.sessionId}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 + idx * 0.04 }}
                    className="p-3 bg-[var(--bg-surface)] rounded-lg border border-[var(--border-subtle)] hover:border-[var(--border-default)] transition-all group"
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-xs font-bold text-[var(--text-tertiary)] bg-[var(--bg-0)] px-2 py-1 rounded">
                        #{idx + 1}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="h-1.5 bg-[var(--bg-surface-hover)] rounded-full overflow-hidden mb-2">
                          <motion.div
                            className={`h-full ${
                              session.riskScore > 75
                                ? 'bg-[var(--critical)]'
                                : session.riskScore > 50
                                  ? 'bg-[var(--high)]'
                                  : 'bg-[var(--medium)]'
                            }`}
                            initial={{ width: 0 }}
                            animate={{ width: `${session.riskScore}%` }}
                            transition={{ duration: 0.8, delay: 0.4 + idx * 0.05 }}
                          />
                        </div>
                        <p className="text-xs font-mono text-[var(--text-secondary)] truncate">{session.sessionId.slice(0, 24)}...</p>
                        <p className="text-xs text-[var(--text-tertiary)] mt-0.5">{session.department}</p>
                        <div className="flex gap-1 mt-2 flex-wrap">
                          {session.sensitiveFileTypes.slice(0, 2).map((type) => (
                            <span key={type} className="px-2 py-0.5 rounded text-xs bg-[var(--accent-muted)] text-[var(--accent)]">
                              {type}
                            </span>
                          ))}
                        </div>
                      </div>
                      <span className="text-sm font-bold text-[var(--text-primary)] whitespace-nowrap">
                        {Math.round(session.riskScore)}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </Card>
          </motion.div>
        </div>

        {/* Findings Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          {/* Filter Tabs — directly above the findings table */}
          <div className="flex gap-2 flex-wrap mb-4">
            {(['all', 'secret', 'pii', 'slopsquat'] as const).map((tab, idx) => (
              <motion.button
                key={tab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setFilterType(tab)}
                className={`px-4 py-2 rounded-full font-medium transition-all border text-sm ${
                  filterType === tab
                    ? 'border-transparent'
                    : 'bg-transparent text-[var(--text-secondary)] border-[var(--border-subtle)] hover:border-[var(--border-default)]'
                }`}
                style={filterType === tab ? { backgroundColor: '#1e3a8a', color: '#ffffff' } : undefined}
              >
                {tab === 'all' ? 'All' : tab === 'slopsquat' ? 'Slopsquatting' : tab.toUpperCase()}
              </motion.button>
            ))}
          </div>
          <Card header={<h3 className="font-bold text-[var(--text-primary)]">Security Findings</h3>}>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--border-default)] sticky top-0 bg-[var(--bg-surface)]">
                    {[
                      { key: 'severity' as const, label: 'Severity' },
                      { key: 'type' as const, label: 'Type' },
                      { key: 'category' as const, label: 'Category' },
                      { key: 'department' as const, label: 'Department' },
                      { key: 'provider' as const, label: 'Provider' },
                      { key: 'detectedAt' as const, label: 'Detected' },
                      { key: 'status' as const, label: 'Status' },
                    ].map(({ key, label }) => (
                      <th key={key}>
                        <button
                          onClick={() => handleSort(key)}
                          className="w-full px-4 py-3 text-left text-[var(--text-secondary)] font-semibold hover:text-[var(--text-primary)] transition-colors flex items-center gap-1 group"
                        >
                          {label}
                          <span className="text-xs opacity-50 group-hover:opacity-100 transition-opacity">
                            {sortBy === key ? (sortDesc ? '↓' : '↑') : '↕'}
                          </span>
                        </button>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredFindings.map((finding, idx) => (
                    <motion.tr
                      key={finding.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.02, duration: 0.2 }}
                      onClick={() => handleFindingClick(finding)}
                      className="border-b border-[var(--border-subtle)] hover:bg-[var(--bg-surface-hover)] cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-3">
                        <Badge variant={finding.severity}>{finding.severity}</Badge>
                      </td>
                      <td className="px-4 py-3 text-[var(--text-primary)] font-medium">{finding.type.toUpperCase()}</td>
                      <td className="px-4 py-3 text-[var(--text-secondary)]">{finding.category}</td>
                      <td className="px-4 py-3 text-[var(--text-secondary)]">{finding.department}</td>
                      <td className="px-4 py-3">
                        <span
                          className="px-2 py-1 rounded text-xs font-medium"
                          style={{ backgroundColor: `${PROVIDER_COLORS[finding.provider] || '#666'}20`, color: PROVIDER_COLORS[finding.provider] }}
                        >
                          {finding.provider}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-[var(--text-tertiary)]">
                        {new Date(finding.detectedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            finding.status === 'open'
                              ? 'bg-[var(--critical-muted)] text-[var(--critical)]'
                              : finding.status === 'acknowledged'
                                ? 'bg-[var(--high-muted)] text-[var(--high)]'
                                : 'bg-[var(--success-muted)] text-[var(--success)]'
                          }`}
                        >
                          {finding.status.charAt(0).toUpperCase() + finding.status.slice(1)}
                        </span>
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>
            </div>
            {filteredFindings.length === 0 && (
              <div className="text-center py-12">
                <p className="text-[var(--text-tertiary)]">No findings match the selected filter</p>
              </div>
            )}
          </Card>
        </motion.div>

        {/* Finding Detail Modal */}
        <Modal isOpen={!!selectedFinding} onClose={() => setSelectedFinding(null)} title="Finding Details">
          {selectedFinding && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-[var(--text-tertiary)] uppercase tracking-wider">Type</p>
                  <p className="text-sm font-semibold text-[var(--text-primary)] mt-1">{selectedFinding.type.toUpperCase()}</p>
                </div>
                <div>
                  <p className="text-xs text-[var(--text-tertiary)] uppercase tracking-wider">Severity</p>
                  <Badge variant={selectedFinding.severity} className="mt-1">
                    {selectedFinding.severity}
                  </Badge>
                </div>
                <div>
                  <p className="text-xs text-[var(--text-tertiary)] uppercase tracking-wider">Department</p>
                  <p className="text-sm font-semibold text-[var(--text-primary)] mt-1">{selectedFinding.department}</p>
                </div>
                <div>
                  <p className="text-xs text-[var(--text-tertiary)] uppercase tracking-wider">Provider</p>
                  <p className="text-sm font-semibold text-[var(--text-primary)] mt-1">{selectedFinding.provider}</p>
                </div>
                <div>
                  <p className="text-xs text-[var(--text-tertiary)] uppercase tracking-wider">Category</p>
                  <p className="text-sm font-semibold text-[var(--text-primary)] mt-1">{selectedFinding.category}</p>
                </div>
                <div>
                  <p className="text-xs text-[var(--text-tertiary)] uppercase tracking-wider">Detected</p>
                  <p className="text-sm font-semibold text-[var(--text-primary)] mt-1">
                    {new Date(selectedFinding.detectedAt).toLocaleDateString()}
                  </p>
                </div>
              </div>

              <div className="border-t border-[var(--border-default)] pt-6">
                <p className="text-xs text-[var(--text-tertiary)] uppercase tracking-wider mb-3">Context Window</p>
                <div className="bg-[var(--bg-0)] p-4 rounded-lg border border-[var(--border-subtle)] overflow-auto max-h-48">
                  <p className="text-xs font-mono text-[var(--text-secondary)] whitespace-pre-wrap break-words">
                    {selectedFinding.fullContext}
                  </p>
                </div>
              </div>

              <div className="border-t border-[var(--border-default)] pt-6">
                <p className="text-xs text-[var(--text-tertiary)] uppercase tracking-wider mb-3">Remediation History</p>
                <div className="space-y-2">
                  {selectedFinding.remediationHistory.map((history, idx) => (
                    <div key={idx} className="bg-[var(--bg-surface)] p-3 rounded-lg border border-[var(--border-subtle)]">
                      <div className="flex items-start justify-between text-xs">
                        <span className="text-[var(--text-tertiary)]">{new Date(history.timestamp).toLocaleDateString()}</span>
                        <span className="text-[var(--text-secondary)] font-semibold">
                          {history.oldStatus} → {history.newStatus}
                        </span>
                      </div>
                      <p className="text-xs text-[var(--text-secondary)] mt-2">{history.notes}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </Modal>
      </div>
    </motion.div>
  );
}
