import { useState, useEffect, useRef } from 'react';
import { useLocation, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  Shield,
  DollarSign,
  Brain,
  Scale,
  Bell,
  Lightbulb,
  ChevronLeft,
  ChevronRight,
  Activity,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import AnimatedBackground from './AnimatedBackground';

interface NavItem {
  label: string;
  icon: React.ComponentType<{ className?: string; size?: number }>;
  path: string;
  hasAlert?: boolean;
  isPulsing?: boolean;
}

const navItems: NavItem[] = [
  { label: 'Command Center', icon: LayoutDashboard, path: '/' },
  { label: 'Security Intel', icon: Shield, path: '/leaks' },
  { label: 'Cost Analytics', icon: DollarSign, path: '/costs' },
  { label: 'Model Analytics', icon: Brain, path: '/models' },
  { label: 'Compliance', icon: Scale, path: '/compliance' },
  { label: 'Alert Feed', icon: Bell, path: '/alerts', isPulsing: true },
  { label: 'Recommendations', icon: Lightbulb, path: '/recommendations' },
];

const pageNames: Record<string, string> = {
  '/': 'Command Center',
  '/leaks': 'Security Intelligence',
  '/costs': 'Cost Analytics',
  '/models': 'Model Intelligence',
  '/compliance': 'Compliance',
  '/alerts': 'Alert Feed',
  '/recommendations': 'Recommendations',
};

export default function Layout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const mainRef = useRef<HTMLElement>(null);

  const currentPageName = pageNames[location.pathname] || 'Argus';

  // Scroll to top on every route change
  useEffect(() => {
    mainRef.current?.scrollTo(0, 0);
  }, [location.pathname]);

  return (
    <div className="flex h-screen w-full bg-[var(--bg-0)] text-[var(--text-primary)] overflow-hidden">
      {/* Animated particle background */}
      <AnimatedBackground />

      {/* Sidebar — clean white enterprise style */}
      <motion.div
        animate={{ width: collapsed ? 72 : 260 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="fixed left-0 top-0 h-full flex flex-col overflow-hidden z-30"
        style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(24px) saturate(180%)',
          borderRight: '1px solid rgba(20, 27, 65, 0.08)',
          boxShadow: '2px 0 12px rgba(20, 27, 65, 0.03)',
        }}
      >
        {/* Logo Area */}
        <div className="relative flex items-center h-16 px-5 border-b border-[var(--border-subtle)] overflow-hidden">
          {/* Accent line */}
          <motion.div
            className="absolute top-0 left-0 right-0 h-[2px]"
            style={{
              background: 'linear-gradient(90deg, #1e3a8a, #3b82f6, #1e3a8a)',
              backgroundSize: '200% 100%',
            }}
            animate={{ backgroundPosition: ['0% 50%', '200% 50%'] }}
            transition={{ duration: 6, repeat: Infinity, ease: 'linear' }}
          />

          <div className="flex items-center gap-3 relative z-10">
            <div className="relative flex-shrink-0">
              <Shield size={28} className="text-[#1e3a8a]" strokeWidth={2.5} />
            </div>
            <AnimatePresence>
              {!collapsed && (
                <motion.div
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: 'auto' }}
                  exit={{ opacity: 0, width: 0 }}
                  transition={{ delay: 0.05, duration: 0.2 }}
                  className="flex items-baseline gap-2 overflow-hidden"
                >
                  <span className="font-mono font-bold text-lg tracking-[0.15em] text-[#141B41]">
                    ARGUS
                  </span>
                  <span className="text-[10px] text-[var(--text-tertiary)] font-medium whitespace-nowrap">
                    AI Intelligence
                  </span>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-3 px-2.5 space-y-0.5">
          {navItems.map((item, idx) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <motion.div
                key={item.path}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.04, duration: 0.25 }}
              >
                <Link
                  to={item.path}
                  className={`
                    relative flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group
                    ${
                      isActive
                        ? 'text-[#1e3a8a]'
                        : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-2)]'
                    }
                  `}
                >
                  {/* Active background */}
                  {isActive && (
                    <motion.div
                      layoutId="navActiveBackground"
                      className="absolute inset-0 rounded-lg"
                      style={{
                        background: 'linear-gradient(135deg, rgba(30, 58, 138, 0.08) 0%, rgba(59, 130, 246, 0.04) 100%)',
                        border: '1px solid rgba(30, 58, 138, 0.12)',
                      }}
                      transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                    />
                  )}

                  {/* Active left indicator */}
                  {isActive && (
                    <motion.div
                      layoutId="navActiveIndicator"
                      className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full"
                      style={{ background: '#1e3a8a' }}
                      transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                    />
                  )}

                  <Icon size={18} className="flex-shrink-0 relative z-10" />

                  <AnimatePresence>
                    {!collapsed && (
                      <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ delay: 0.03 }}
                        className="text-[13px] font-medium flex-1 relative z-10"
                      >
                        {item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>

                  {/* Pulsing dot for alerts */}
                  {item.isPulsing && (
                    <motion.div
                      animate={{ opacity: [0.4, 1, 0.4] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="w-1.5 h-1.5 rounded-full bg-[var(--critical)] flex-shrink-0 relative z-10"
                    />
                  )}

                  {/* Collapsed tooltip */}
                  {collapsed && (
                    <div className="absolute left-full ml-3 px-2.5 py-1.5 bg-white rounded-md whitespace-nowrap text-xs font-medium text-[var(--text-primary)] shadow-lg border border-[var(--border-default)] pointer-events-none z-50 opacity-0 group-hover:opacity-100 transition-opacity">
                      {item.label}
                    </div>
                  )}
                </Link>
              </motion.div>
            );
          })}
        </nav>

        {/* Bottom Section */}
        <div className="border-t border-[var(--border-subtle)] p-2.5 space-y-2">
          {/* System status */}
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="flex items-center gap-2 px-3 py-2 rounded-lg"
                style={{ background: 'rgba(22, 163, 74, 0.06)', border: '1px solid rgba(22, 163, 74, 0.12)' }}
              >
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="w-1.5 h-1.5 rounded-full bg-[var(--success)] flex-shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-[10px] font-semibold text-[var(--success)] tracking-wide">SYSTEMS ACTIVE</p>
                </div>
                <Activity size={12} className="text-[var(--success)] opacity-60" />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Collapse button */}
          <motion.button
            onClick={() => setCollapsed(!collapsed)}
            className="w-full flex items-center justify-center p-1.5 rounded-lg hover:bg-[var(--bg-2)] transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <motion.div animate={{ rotate: collapsed ? 180 : 0 }} transition={{ duration: 0.2 }}>
              {collapsed ? (
                <ChevronRight size={16} className="text-[var(--text-tertiary)]" />
              ) : (
                <ChevronLeft size={16} className="text-[var(--text-tertiary)]" />
              )}
            </motion.div>
          </motion.button>
        </div>
      </motion.div>

      {/* Main content */}
      <motion.div
        animate={{ marginLeft: collapsed ? 72 : 260 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="flex-1 flex flex-col overflow-hidden relative z-10"
      >
        {/* Top Bar — clean and minimal */}
        <div
          className="h-12 border-b flex items-center justify-between px-6 relative z-20 flex-shrink-0"
          style={{
            background: 'rgba(255, 255, 255, 0.85)',
            backdropFilter: 'blur(20px) saturate(180%)',
            borderColor: 'rgba(20, 27, 65, 0.06)',
          }}
        >
          {/* Left: breadcrumb */}
          <AnimatePresence mode="wait">
            <motion.div
              key={currentPageName}
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              transition={{ duration: 0.2 }}
              className="flex items-center gap-2"
            >
              <span className="text-xs text-[var(--text-tertiary)] font-medium">ARGUS</span>
              <span className="text-[var(--text-tertiary)]">/</span>
              <span className="text-sm font-semibold text-[var(--text-primary)]">{currentPageName}</span>
            </motion.div>
          </AnimatePresence>

          {/* Right: live indicator */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="relative">
                <motion.div
                  className="w-1.5 h-1.5 bg-[var(--success)] rounded-full"
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              </div>
              <span className="text-xs text-[var(--text-tertiary)] font-medium">Live</span>
            </div>
          </div>
        </div>

        {/* Main content area */}
        <main ref={mainRef} className="flex-1 overflow-y-auto bg-transparent relative">
          {children}
        </main>
      </motion.div>
    </div>
  );
}
