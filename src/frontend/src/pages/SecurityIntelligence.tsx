import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Modal from '@/components/ui/Modal';
import { mockFindings, mockSeverityDistribution, mockSlopsquattingStats, mockContextRisk } from '@/lib/mock-data';
import type * as types from '@/lib/types';

const PROVIDER_COLORS: Record<string, string> = {
  OpenAI: '#10b981',
  Anthropic: '#f59e0b',
  Google: '#3b82f6',
  Mistral: '#8b5cf6',
  Local: '#ef5350',
};

const SEVERITY_COLORS: Record<types.Severity, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
};

export default function SecurityIntelligence() {
  const [filterType, setFilterType] = useState<types.FindingType>('all');
  const [selectedFinding, setSelectedFinding] = useState<types.FindingDetail | null>(null);
  const [sortBy, setSortBy] = useState<keyof types.Finding>('detectedAt');
  const [sortDesc, setSortDesc] = useState(true);

  const filteredFindings = useMemo(() => {
    let filtered = mockFindings;
    if (filterType !== 'all') {
      filtered = filtered.filter((f) => f.type === filterType);
    }
    return filtered.sort((a, b) => {
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
  }, [filterType, sortBy, sortDesc]);

  const totalFindings = filteredFindings.length;

  const slopsquattingData = mockSlopsquattingStats.map((stat) => ({
    name: stat.provider,
    count: stat.hallucCount,
  }));

  const handleFindingClick = (finding: types.Finding) => {
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
  ) => (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="overflow-hidden border-l-4" style={{ borderLeftColor: accentColor }}>
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">{title}</h3>

          <div className="space-y-2">
            {[
              { label: 'Critical', value: severity.critical, color: '#ef4444', dot: '•' },
              { label: 'High', value: severity.high, color: '#f97316', dot: '•' },
              { label: 'Medium', value: severity.medium, color: '#eab308', dot: '•' },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span style={{ color: item.color, fontSize: '20px', lineHeight: '1' }}>{item.dot}</span>
                  <span className="text-[var(--text-secondary)]">{item.label}</span>
                </div>
                <span className="font-medium text-[var(--text-primary)]">{item.value}</span>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-[var(--border-subtle)]">
            <ResponsiveContainer width="100%" height={30}>
              <BarChart
                data={[severity]}
                layout="vertical"
                margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
              >
                <Bar dataKey="critical" stackId="a" fill="#ef4444" radius={2} />
                <Bar dataKey="high" stackId="a" fill="#f97316" radius={2} />
                <Bar dataKey="medium" stackId="a" fill="#eab308" radius={2} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="pt-2 border-t border-[var(--border-subtle)]">
            <p className="text-xs text-[var(--text-tertiary)]">
              Total: <span className="text-[var(--text-primary)] font-semibold">{severity.critical + severity.high + severity.medium}</span>
            </p>
          </div>
        </div>
      </Card>
    </motion.div>
  );

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
          <h1 className="text-4xl font-bold text-[var(--text-primary)]">Security Intelligence</h1>
          <p className="text-[var(--text-tertiary)] mt-2">Detect and track data exposure risks across AI usage</p>
        </div>
        <Badge variant="critical" className="px-4 py-2">
          {totalFindings} findings
        </Badge>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 flex-wrap">
        {(['all', 'secret', 'pii', 'slopsquat'] as const).map((tab) => (
          <motion.button
            key={tab}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setFilterType(tab)}
            className={`px-4 py-2 rounded-full font-medium transition-all backdrop-blur-sm border ${
              filterType === tab
                ? 'bg-[var(--accent)] text-white border-[var(--accent-glow)]'
                : 'bg-[var(--bg-surface)] text-[var(--text-secondary)] border-[var(--border-subtle)] hover:border-[var(--border-default)]'
            }`}
          >
            {tab === 'all' ? 'All' : tab === 'slopsquat' ? 'Slopsquatting' : tab.toUpperCase()}
          </motion.button>
        ))}
      </div>

      {/* Row 1: Severity Panels */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {severityPanel('Secrets', mockSeverityDistribution.secrets, '#ef4444')}
        {severityPanel('PII', mockSeverityDistribution.pii, '#f59e0b')}
        {severityPanel('Slopsquatting', mockSeverityDistribution.slopsquat, '#8b5cf6')}
      </div>

      {/* Row 2: Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Slopsquatting by Model */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="lg:col-span-2"
        >
          <Card header={<h3 className="font-semibold text-[var(--text-primary)]">Slopsquatting by Model</h3>}>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={slopsquattingData} layout="vertical" margin={{ top: 5, right: 30, bottom: 5, left: 100 }}>
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
                  cursor={{ fill: 'var(--accent-muted)' }}
                />
                <Bar dataKey="count" fill="var(--accent)" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </motion.div>

        {/* Context Exposure Risk Top 10 */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.15 }}
        >
          <Card header={<h3 className="font-semibold text-[var(--text-primary)]">Context Exposure Risk</h3>}>
            <div className="space-y-2 max-h-[350px] overflow-y-auto">
              {mockContextRisk.slice(0, 10).map((session, idx) => (
                <motion.div
                  key={session.sessionId}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.04 }}
                  className="p-3 bg-[var(--bg-surface)] rounded-lg border border-[var(--border-subtle)] hover:border-[var(--border-default)] transition-colors group"
                >
                  <div className="flex items-start gap-3">
                    <span className="text-xs font-bold text-[var(--text-tertiary)] bg-[var(--bg-0)] px-2 py-1 rounded">
                      #{idx + 1}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="h-1.5 bg-[var(--bg-surface-hover)] rounded-full overflow-hidden mb-2">
                        <div
                          className={`h-full ${
                            session.riskScore > 75
                              ? 'bg-[var(--critical)]'
                              : session.riskScore > 50
                                ? 'bg-[var(--high)]'
                                : 'bg-[var(--medium)]'
                          } transition-all`}
                          style={{ width: `${session.riskScore}%` }}
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
                    <span className="text-sm font-semibold text-[var(--text-primary)] whitespace-nowrap">
                      {Math.round(session.riskScore)}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          </Card>
        </motion.div>
      </div>

      {/* Row 3: Findings Table */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.2 }}
      >
        <Card header={<h3 className="font-semibold text-[var(--text-primary)]">Security Findings</h3>}>
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
                    transition={{ delay: idx * 0.03, duration: 0.2 }}
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
    </motion.div>
  );
}
