import { motion } from 'framer-motion';
import { Check, AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import { mockComplianceScore, mockDataFlow, mockProviderDPA, mockShadowAI } from '@/lib/mock-data';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: 'easeOut' },
  },
};

const checkmarkVariants = {
  hidden: { pathLength: 0, opacity: 0 },
  visible: {
    pathLength: 1,
    opacity: 1,
    transition: { duration: 0.6, delay: 0.2 },
  },
};

function ComplianceGauge() {
  const score = mockComplianceScore.overallScore;
  const radius = 55;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  const getGaugeColor = (s: number) => {
    if (s >= 80) return '#22c55e';
    if (s >= 60) return '#eab308';
    return '#ef4444';
  };

  const getStatusLabel = (s: number) => {
    if (s >= 80) return 'COMPLIANT';
    if (s >= 60) return 'PARTIAL COMPLIANCE';
    return 'NON-COMPLIANT';
  };

  const gaugeColor = getGaugeColor(score);

  return (
    <motion.div variants={itemVariants}>
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Gauge */}
        <div className="lg:col-span-2 flex flex-col items-center justify-center">
          <Card className="w-full flex flex-col items-center justify-center py-12">
            <div className="relative w-48 h-48 mb-8">
              <svg viewBox="0 0 160 160" className="w-full h-full transform -rotate-90">
                {/* Background circle */}
                <circle cx="80" cy="80" r={radius} fill="none" stroke="var(--border-default)" strokeWidth="8" />

                {/* Progress circle with glow */}
                <defs>
                  <filter id="gaugeGlow">
                    <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                    <feMerge>
                      <feMergeNode in="coloredBlur" />
                      <feMergeNode in="SourceGraphic" />
                    </feMerge>
                  </filter>
                </defs>

                <motion.circle
                  cx="80"
                  cy="80"
                  r={radius}
                  fill="none"
                  stroke={gaugeColor}
                  strokeWidth="8"
                  strokeDasharray={circumference}
                  initial={{ strokeDashoffset: circumference }}
                  animate={{ strokeDashoffset }}
                  transition={{ duration: 1.8, ease: 'easeOut' }}
                  strokeLinecap="round"
                  filter="url(#gaugeGlow)"
                />
              </svg>

              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <motion.div
                  initial={{ opacity: 0, scale: 0.5 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.6, delay: 0.3 }}
                  className="text-center"
                >
                  <p className="text-5xl font-bold text-[var(--text-primary)]">{score}</p>
                  <p className="text-xs text-[var(--text-secondary)] mt-1">/100</p>
                </motion.div>
              </div>
            </div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="text-center"
            >
              <div className="inline-block px-3 py-1 bg-[var(--accent-muted)] rounded-full mb-2">
                <p className="text-sm font-semibold text-[var(--accent)]">{getStatusLabel(score)}</p>
              </div>
              <p className="text-xs text-[var(--text-secondary)]">EU AI Act Compliance</p>
            </motion.div>
          </Card>
        </div>

        {/* Audit Pillars */}
        <div className="lg:col-span-3">
          <Card header={<h2 className="font-semibold text-[var(--text-primary)]">Compliance Pillars</h2>}>
            <div className="space-y-4">
              {mockComplianceScore.auditPillars.map((pillar, idx) => {
                const percentage = pillar.compliancePercentage;
                let barColor = 'bg-[var(--success)]';
                if (percentage < 70) barColor = 'bg-[var(--critical)]';
                else if (percentage < 85) barColor = 'bg-[var(--medium)]';

                return (
                  <motion.div
                    key={pillar.check}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.08 }}
                    className="space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-[var(--text-primary)]">{pillar.check}</p>
                      <p className="text-sm font-bold text-[var(--text-primary)]">{percentage}%</p>
                    </div>
                    <div className="h-2 bg-[var(--bg-surface)] rounded-full overflow-hidden">
                      <motion.div
                        className={`h-full ${barColor} rounded-full`}
                        initial={{ width: '0%' }}
                        animate={{ width: `${percentage}%` }}
                        transition={{ duration: 1, delay: 0.3 + idx * 0.08 }}
                      />
                    </div>
                    <p className="text-xs text-[var(--text-tertiary)]">
                      {pillar.recordsCovering.toLocaleString()} / {pillar.totalRecords.toLocaleString()} records
                    </p>
                  </motion.div>
                );
              })}
            </div>
          </Card>
        </div>
      </div>
    </motion.div>
  );
}

function DataFlowVisualization() {
  const nodesByType = {
    department: mockDataFlow.nodes.filter((n) => n.type === 'department'),
    tool: mockDataFlow.nodes.filter((n) => n.type === 'tool'),
    model: mockDataFlow.nodes.filter((n) => n.type === 'model'),
    region: mockDataFlow.nodes.filter((n) => n.type === 'region'),
  };

  const typeColors: Record<string, string> = {
    department: '#6366f1',
    tool: '#06b6d4',
    model: '#10a37f',
    region: '#22c55e',
  };

  const typeLabels: Record<string, string> = {
    department: 'Departments',
    tool: 'Tools',
    model: 'Models',
    region: 'Regions',
  };

  return (
    <motion.div variants={itemVariants}>
      <Card
        header={
          <div>
            <h2 className="font-semibold text-[var(--text-primary)]">Data Flow Architecture</h2>
            <p className="text-xs text-[var(--text-secondary)] mt-1">Department → Tool → Model → Region</p>
          </div>
        }
      >
        <div className="space-y-8">
          {/* Flow columns */}
          <div className="flex justify-between items-start gap-6 overflow-x-auto pb-4">
            {(Object.entries(nodesByType) as Array<[keyof typeof nodesByType, typeof nodesByType.department]>).map(
              ([type, nodes]) => (
                <div key={type} className="flex flex-col items-center gap-4 flex-shrink-0 min-w-max">
                  <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">{typeLabels[type]}</p>
                  <div className="space-y-3 flex flex-col">
                    {nodes.map((node, idx) => (
                      <motion.div
                        key={node.id}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: idx * 0.05 }}
                        className="px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap text-center border"
                        style={{
                          backgroundColor: `${typeColors[type]}15`,
                          color: typeColors[type],
                          borderColor: `${typeColors[type]}40`,
                        }}
                      >
                        {node.label}
                      </motion.div>
                    ))}
                  </div>
                </div>
              )
            )}
          </div>

          {/* Legend */}
          <div className="flex flex-wrap justify-center gap-6 pt-4 border-t border-[var(--border-subtle)]">
            {Object.entries(typeColors).map(([type, color]) => (
              <div key={type} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                <span className="text-xs text-[var(--text-secondary)]">{typeLabels[type as keyof typeof typeLabels]}</span>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

function ProviderComplianceTable() {
  const providers = mockProviderDPA.slice(0, 5);

  const riskBadgeVariant = (risk: string): 'critical' | 'medium' | 'success' => {
    if (risk === 'high') return 'critical';
    if (risk === 'medium') return 'medium';
    return 'success';
  };

  return (
    <motion.div variants={itemVariants}>
      <Card header={<h2 className="font-semibold text-[var(--text-primary)]">Provider Compliance & Data Retention</h2>}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border-subtle)]">
                <th className="text-left py-3 px-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase">Provider</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase">Regions</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase">Retention</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase">GDPR DPA</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-[var(--text-tertiary)] uppercase">Risk</th>
              </tr>
            </thead>
            <tbody>
              {providers.map((provider, idx) => (
                <motion.tr
                  key={provider.provider}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="border-b border-[var(--border-subtle)] hover:bg-[var(--bg-surface-hover)] transition-colors"
                >
                  <td className="py-3 px-4 font-medium text-[var(--text-primary)]">{provider.provider}</td>
                  <td className="py-3 px-4 text-[var(--text-secondary)] text-sm">{provider.regions.join(', ')}</td>
                  <td className="py-3 px-4 text-[var(--text-primary)] text-sm">
                    {provider.dataRetention.days === 0 ? 'Instant' : `${provider.dataRetention.days}d`}
                  </td>
                  <td className="py-3 px-4">
                    {provider.hasGDPRDPA ? (
                      <div className="flex items-center gap-1">
                        <Check className="w-4 h-4 text-[var(--success)]" />
                        <span className="text-xs text-[var(--success)]">Yes</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1">
                        <AlertCircle className="w-4 h-4 text-[var(--critical)]" />
                        <span className="text-xs text-[var(--critical)]">No</span>
                      </div>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <Badge variant={riskBadgeVariant(provider.riskLevel)} size="sm">
                      {provider.riskLevel.charAt(0).toUpperCase() + provider.riskLevel.slice(1)}
                    </Badge>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </motion.div>
  );
}

function ShadowAIDetection() {
  const { approvedProviders, violations } = mockShadowAI;

  return (
    <motion.div variants={itemVariants}>
      <Card header={<h2 className="font-semibold text-[var(--text-primary)]">Shadow AI Detection</h2>}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Approved Providers */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle className="w-5 h-5 text-[var(--success)]" />
              <h3 className="font-semibold text-[var(--text-primary)]">Approved Providers</h3>
            </div>
            <div className="space-y-2">
              {approvedProviders.map((provider) => (
                <motion.div
                  key={provider}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center gap-3 p-3 bg-[var(--success-muted)] rounded-lg border border-[var(--success)]/30"
                >
                  <Check className="w-4 h-4 text-[var(--success)] flex-shrink-0" />
                  <span className="text-sm text-[var(--text-primary)]">{provider}</span>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Violations */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="w-5 h-5 text-[var(--critical)]" />
              <h3 className="font-semibold text-[var(--text-primary)]">Unapproved Detected</h3>
            </div>
            <div className="space-y-2">
              {violations.map((violation) => (
                <motion.div
                  key={violation.provider}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="p-3 bg-[var(--critical-muted)] rounded-lg border border-[var(--critical)]/30"
                >
                  <p className="text-sm font-semibold text-[var(--critical)]">{violation.provider}</p>
                  <p className="text-xs text-[var(--text-secondary)] mt-1">
                    {violation.eventCount} events • {violation.departments.join(', ')}
                  </p>
                  <p className="text-xs font-medium text-[var(--critical)] mt-1">€{violation.totalCost.toFixed(2)}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

function ComplianceChecklist() {
  const checks = [
    { status: 'pass', label: 'All prompts logged with purpose', coverage: '92%' },
    { status: 'pass', label: 'Model names tracked in all sessions', coverage: '98%' },
    { status: 'warning', label: '24% of sessions missing region data', coverage: '76%' },
    { status: 'pass', label: 'User IDs properly pseudonymized', coverage: '88%' },
    { status: 'warning', label: 'Vendor compliance verification needed for 2 providers', coverage: '60%' },
    { status: 'pass', label: 'Audit trail maintained for all findings', coverage: '100%' },
  ];

  return (
    <motion.div variants={itemVariants}>
      <Card header={<h2 className="font-semibold text-[var(--text-primary)]">Compliance Checklist</h2>}>
        <div className="space-y-3">
          {checks.map((check, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.08 }}
              className={`flex items-center gap-4 p-4 rounded-lg border ${
                check.status === 'pass'
                  ? 'bg-[var(--success-muted)] border-[var(--success)]/30'
                  : 'bg-[var(--medium-muted)] border-[var(--medium)]/30'
              }`}
            >
              {check.status === 'pass' ? (
                <motion.svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  variants={checkmarkVariants}
                  initial="hidden"
                  animate="visible"
                  className="text-[var(--success)] flex-shrink-0"
                >
                  <polyline points="20 6 9 17 4 12" />
                </motion.svg>
              ) : (
                <AlertTriangle className="w-6 h-6 text-[var(--medium)] flex-shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium ${check.status === 'pass' ? 'text-[var(--text-primary)]' : 'text-[var(--medium)]'}`}>
                  {check.label}
                </p>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-xs font-semibold text-[var(--text-secondary)]">{check.coverage}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </Card>
    </motion.div>
  );
}

export default function Compliance() {
  return (
    <motion.div
      className="space-y-8 pb-12"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-[var(--text-primary)] mb-2">EU AI Act Compliance</h1>
          <p className="text-sm text-[var(--text-secondary)]">Monitor regulatory requirements and audit readiness</p>
        </div>
        <Badge variant="info" size="md">
          {mockComplianceScore.overallScore}/100
        </Badge>
      </div>

      {/* Gauge + Pillars */}
      <ComplianceGauge />

      {/* Data Flow */}
      <DataFlowVisualization />

      {/* Provider Table */}
      <ProviderComplianceTable />

      {/* Shadow AI */}
      <ShadowAIDetection />

      {/* Checklist */}
      <ComplianceChecklist />
    </motion.div>
  );
}
