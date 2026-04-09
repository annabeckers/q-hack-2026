import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { Check, AlertCircle, CheckCircle, AlertTriangle, Scale } from 'lucide-react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import CountUp from '@/components/ui/CountUp';
import { mockComplianceScore, mockDataFlow, mockProviderDPA, mockShadowAI } from '@/lib/mock-data';

function ComplianceGauge() {
  const score = mockComplianceScore.overallScore;
  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });
  const gaugeColor = score >= 80 ? '#22c55e' : score >= 60 ? '#eab308' : '#ef4444';
  const statusLabel = score >= 80 ? 'COMPLIANT' : score >= 60 ? 'PARTIAL' : 'NON-COMPLIANT';

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 20 }} animate={isInView ? { opacity: 1, y: 0 } : undefined} transition={{ duration: 0.5 }}>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Gauge */}
        <Card className="flex flex-col items-center justify-center py-10">
          <div className="relative w-36 h-36 mb-6">
            <svg viewBox="0 0 140 140" className="w-full h-full -rotate-90">
              <circle cx="70" cy="70" r={radius} fill="none" stroke="var(--border-subtle)" strokeWidth="6" />
              <motion.circle cx="70" cy="70" r={radius} fill="none" stroke={gaugeColor} strokeWidth="6" strokeDasharray={circumference} initial={{ strokeDashoffset: circumference }} animate={isInView ? { strokeDashoffset } : undefined} transition={{ duration: 1.8, ease: 'easeOut' }} strokeLinecap="round" style={{ filter: `drop-shadow(0 0 8px ${gaugeColor}60)` }} />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-bold text-[var(--text-primary)] tabular-nums"><CountUp target={score} /></span>
              <span className="text-xs text-[var(--text-tertiary)] mt-0.5">/100</span>
            </div>
          </div>
          <div className="px-3 py-1 rounded-full mb-1" style={{ background: `${gaugeColor}20` }}>
            <span className="text-xs font-bold" style={{ color: gaugeColor }}>{statusLabel}</span>
          </div>
          <p className="text-[11px] text-[var(--text-tertiary)]">EU AI Act</p>
        </Card>

        {/* Pillars — spans 2 cols */}
        <div className="lg:col-span-2">
          <Card header={<span className="font-semibold text-[var(--text-primary)] text-sm">Compliance Pillars</span>}>
            <div className="space-y-4">
              {mockComplianceScore.auditPillars.map((pillar, idx) => {
                const pct = pillar.compliancePercentage;
                const barColor = pct < 70 ? 'bg-[var(--critical)]' : pct < 85 ? 'bg-[var(--medium)]' : 'bg-[var(--success)]';
                return (
                  <motion.div key={pillar.check} initial={{ opacity: 0, x: -15 }} animate={isInView ? { opacity: 1, x: 0 } : undefined} transition={{ delay: 0.2 + idx * 0.06 }} className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-[var(--text-primary)]">{pillar.check}</span>
                      <span className="text-sm font-bold text-[var(--text-primary)] tabular-nums">{pct}%</span>
                    </div>
                    <div className="h-1.5 bg-[var(--bg-2)] rounded-full overflow-hidden">
                      <motion.div className={`h-full ${barColor} rounded-full`} initial={{ width: '0%' }} animate={isInView ? { width: `${pct}%` } : undefined} transition={{ duration: 0.8, delay: 0.3 + idx * 0.06 }} />
                    </div>
                    <p className="text-[11px] text-[var(--text-tertiary)]">{pillar.recordsCovering.toLocaleString()} / {pillar.totalRecords.toLocaleString()} records</p>
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
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });
  const nodesByType = {
    department: mockDataFlow.nodes.filter(n => n.type === 'department'),
    tool: mockDataFlow.nodes.filter(n => n.type === 'tool'),
    model: mockDataFlow.nodes.filter(n => n.type === 'model'),
    region: mockDataFlow.nodes.filter(n => n.type === 'region'),
  };
  const typeColors: Record<string, string> = { department: '#1e3a8a', tool: '#0284c7', model: '#0d9488', region: '#16a34a' };
  const typeLabels: Record<string, string> = { department: 'Departments', tool: 'Tools', model: 'Models', region: 'Regions' };

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 20 }} animate={isInView ? { opacity: 1, y: 0 } : undefined} transition={{ duration: 0.5 }}>
      <Card header={<div><span className="font-semibold text-[var(--text-primary)] text-sm">Data Flow Architecture</span><p className="text-[11px] text-[var(--text-tertiary)] mt-0.5">Department → Tool → Model → Region</p></div>}>
        <div className="space-y-6">
          <div className="grid grid-cols-4 gap-4">
            {(Object.entries(nodesByType) as Array<[keyof typeof nodesByType, typeof nodesByType.department]>).map(([type, nodes]) => (
              <div key={type} className="space-y-2">
                <p className="text-[10px] font-semibold text-[var(--text-tertiary)] uppercase tracking-wider text-center">{typeLabels[type]}</p>
                <div className="space-y-1.5">
                  {nodes.map((node, idx) => (
                    <motion.div key={node.id} initial={{ opacity: 0, scale: 0.9 }} animate={isInView ? { opacity: 1, scale: 1 } : undefined} transition={{ delay: 0.2 + idx * 0.04 }} whileHover={{ scale: 1.03 }}
                      className="px-2.5 py-1.5 rounded-md text-[11px] font-medium text-center border cursor-pointer transition-all"
                      style={{ backgroundColor: `${typeColors[type]}12`, color: typeColors[type], borderColor: `${typeColors[type]}30` }}
                    >
                      {node.label}
                    </motion.div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="flex flex-wrap justify-center gap-5 pt-3 border-t border-[var(--border-subtle)]">
            {Object.entries(typeColors).map(([type, color]) => (
              <div key={type} className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full" style={{ background: color }} /><span className="text-[11px] text-[var(--text-secondary)]">{typeLabels[type as keyof typeof typeLabels]}</span></div>
            ))}
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

function ProviderComplianceTable() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });
  const providers = mockProviderDPA.slice(0, 5);
  const riskVariant = (r: string): 'critical' | 'medium' | 'success' => r === 'high' ? 'critical' : r === 'medium' ? 'medium' : 'success';

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 20 }} animate={isInView ? { opacity: 1, y: 0 } : undefined} transition={{ duration: 0.5 }}>
      <Card header={<span className="font-semibold text-[var(--text-primary)] text-sm">Provider Compliance & Data Retention</span>}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--border-subtle)]">
                {['Provider', 'Regions', 'Retention', 'GDPR DPA', 'Risk'].map(h => (
                  <th key={h} className="text-left py-2.5 px-3 text-[10px] font-semibold text-[var(--text-tertiary)] uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {providers.map((p, idx) => (
                <motion.tr key={p.provider} initial={{ opacity: 0 }} animate={isInView ? { opacity: 1 } : undefined} transition={{ delay: 0.2 + idx * 0.04 }} className="border-b border-[var(--border-subtle)] hover:bg-white/[0.02] transition-colors">
                  <td className="py-2.5 px-3 font-medium text-[var(--text-primary)]">{p.provider}</td>
                  <td className="py-2.5 px-3 text-[var(--text-secondary)] text-[13px]">{p.regions.join(', ')}</td>
                  <td className="py-2.5 px-3 text-[var(--text-primary)] text-[13px]">{p.dataRetention.days === 0 ? 'Instant' : `${p.dataRetention.days}d`}</td>
                  <td className="py-2.5 px-3">
                    {p.hasGDPRDPA
                      ? <span className="flex items-center gap-1"><Check className="w-3.5 h-3.5 text-[var(--success)]" /><span className="text-[11px] text-[var(--success)]">Yes</span></span>
                      : <span className="flex items-center gap-1"><AlertCircle className="w-3.5 h-3.5 text-[var(--critical)]" /><span className="text-[11px] text-[var(--critical)]">No</span></span>
                    }
                  </td>
                  <td className="py-2.5 px-3"><Badge variant={riskVariant(p.riskLevel)} size="sm">{p.riskLevel.charAt(0).toUpperCase() + p.riskLevel.slice(1)}</Badge></td>
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
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 20 }} animate={isInView ? { opacity: 1, y: 0 } : undefined} transition={{ duration: 0.5 }}>
      <Card header={<span className="font-semibold text-[var(--text-primary)] text-sm">Shadow AI Detection</span>}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="flex items-center gap-2 mb-3"><CheckCircle className="w-4 h-4 text-[var(--success)]" /><span className="font-semibold text-sm text-[var(--text-primary)]">Approved</span></div>
            <div className="space-y-1.5">
              {approvedProviders.map((p, i) => (
                <motion.div key={p} initial={{ opacity: 0, x: -8 }} animate={isInView ? { opacity: 1, x: 0 } : undefined} transition={{ delay: 0.2 + i * 0.04 }}
                  className="flex items-center gap-2.5 p-2.5 rounded-lg" style={{ background: 'rgba(34,197,94,0.06)', border: '1px solid rgba(34,197,94,0.12)' }}
                >
                  <Check className="w-3.5 h-3.5 text-[var(--success)]" /><span className="text-[13px] text-[var(--text-primary)]">{p}</span>
                </motion.div>
              ))}
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-3"><AlertTriangle className="w-4 h-4 text-[var(--critical)]" /><span className="font-semibold text-sm text-[var(--text-primary)]">Unapproved</span></div>
            <div className="space-y-1.5">
              {violations.map((v, i) => (
                <motion.div key={v.provider} initial={{ opacity: 0, x: 8 }} animate={isInView ? { opacity: 1, x: 0 } : undefined} transition={{ delay: 0.2 + i * 0.04 }}
                  className="p-2.5 rounded-lg" style={{ background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.12)' }}
                >
                  <p className="text-[13px] font-semibold text-[var(--critical)]">{v.provider}</p>
                  <p className="text-[11px] text-[var(--text-secondary)] mt-0.5">{v.eventCount} events · {v.departments.join(', ')}</p>
                  <p className="text-[11px] font-medium text-[var(--critical)] mt-0.5">€{v.totalCost.toFixed(2)}</p>
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
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });
  const checks = [
    { status: 'pass', label: 'All prompts logged with purpose', coverage: '92%' },
    { status: 'pass', label: 'Model names tracked in all sessions', coverage: '98%' },
    { status: 'warning', label: '24% of sessions missing region data', coverage: '76%' },
    { status: 'pass', label: 'User IDs properly pseudonymized', coverage: '88%' },
    { status: 'warning', label: 'Vendor compliance verification needed for 2 providers', coverage: '60%' },
    { status: 'pass', label: 'Audit trail maintained for all findings', coverage: '100%' },
  ];

  return (
    <motion.div ref={ref} initial={{ opacity: 0, y: 20 }} animate={isInView ? { opacity: 1, y: 0 } : undefined} transition={{ duration: 0.5 }}>
      <Card header={<span className="font-semibold text-[var(--text-primary)] text-sm">Compliance Checklist</span>}>
        <div className="space-y-2">
          {checks.map((c, idx) => (
            <motion.div key={idx} initial={{ opacity: 0, x: -10 }} animate={isInView ? { opacity: 1, x: 0 } : undefined} transition={{ delay: 0.2 + idx * 0.06 }}
              className={`flex items-center gap-3 p-3 rounded-lg border ${
                c.status === 'pass' ? 'border-[var(--success)]/20' : 'border-[var(--medium)]/20'
              }`}
              style={{ background: c.status === 'pass' ? 'rgba(34,197,94,0.04)' : 'rgba(234,179,8,0.04)' }}
            >
              {c.status === 'pass' ? (
                <motion.svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-[var(--success)] flex-shrink-0">
                  <motion.polyline points="20 6 9 17 4 12" initial={{ pathLength: 0, opacity: 0 }} animate={isInView ? { pathLength: 1, opacity: 1 } : undefined} transition={{ duration: 0.5, delay: 0.4 + idx * 0.06 }} />
                </motion.svg>
              ) : (
                <AlertTriangle className="w-5 h-5 text-[var(--medium)] flex-shrink-0" />
              )}
              <span className={`text-[13px] font-medium flex-1 ${c.status === 'pass' ? 'text-[var(--text-primary)]' : 'text-[var(--medium)]'}`}>{c.label}</span>
              <span className="text-xs font-semibold text-[var(--text-secondary)] tabular-nums">{c.coverage}</span>
            </motion.div>
          ))}
        </div>
      </Card>
    </motion.div>
  );
}

export default function Compliance() {
  const headerRef = useRef(null);
  const headerInView = useInView(headerRef, { once: true });

  return (
    <motion.div className="p-6 lg:p-8 relative min-h-full" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
      <div className="space-y-6 relative z-10">
        {/* Header */}
        <motion.div ref={headerRef} initial={{ opacity: 0, y: -15 }} animate={headerInView ? { opacity: 1, y: 0 } : undefined} transition={{ duration: 0.5 }}
          className="flex items-center justify-between"
        >
          <div>
            <h1 className="text-3xl lg:text-4xl font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-3">
              <Scale size={28} className="text-[var(--accent)]" />
              EU AI Act Compliance
            </h1>
            <p className="text-sm text-[var(--text-tertiary)] mt-1">Monitor regulatory requirements and audit readiness</p>
          </div>
          <Badge variant="info" size="md">{mockComplianceScore.overallScore}/100</Badge>
        </motion.div>

        <ComplianceGauge />
        <DataFlowVisualization />
        <ProviderComplianceTable />
        <ShadowAIDetection />
        <ComplianceChecklist />
      </div>
    </motion.div>
  );
}
