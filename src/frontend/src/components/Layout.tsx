import { useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  Shield,
  DollarSign,
  Brain,
  Scale,
  Bell,
  Sun,
  Moon,
  ChevronLeft,
  ChevronRight,
  Search,
} from 'lucide-react';
import { motion } from 'framer-motion';
import { useTheme } from '../hooks/useTheme.tsx';

interface NavItem {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  path: string;
  hasAlert?: boolean;
  isPulsing?: boolean;
}

const navItems: NavItem[] = [
  { label: 'Command Center', icon: LayoutDashboard, path: '/' },
  { label: 'Security Intel', icon: Shield, path: '/leaks', hasAlert: false },
  { label: 'Cost Analytics', icon: DollarSign, path: '/costs' },
  { label: 'Model Analytics', icon: Brain, path: '/models' },
  { label: 'Compliance', icon: Scale, path: '/compliance' },
  { label: 'Alert Feed', icon: Bell, path: '/alerts', isPulsing: true },
];

const pageNames: Record<string, string> = {
  '/': 'Command Center',
  '/leaks': 'Security Intelligence',
  '/costs': 'Cost Analytics',
  '/models': 'Model Intelligence',
  '/compliance': 'Compliance',
  '/alerts': 'Alert Feed',
};

export default function Layout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();
  const [notificationCount] = useState(3);

  const currentPageName = pageNames[location.pathname] || 'Argus';

  return (
    <div className="flex h-screen bg-[var(--bg-0)] text-[var(--text-primary)]">
      {/* Sidebar */}
      <motion.div
        animate={{ width: collapsed ? 72 : 260 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="fixed left-0 top-0 h-full bg-[var(--bg-1)] border-r border-[var(--border-subtle)] flex flex-col overflow-hidden"
        style={{
          backgroundImage: `repeating-radial-gradient(circle at 20% 50%, rgba(99,102,241,0.03) 0, transparent 50px), repeating-radial-gradient(circle at 80% 80%, rgba(6,182,212,0.02) 0, transparent 50px)`,
        }}
      >
        {/* Logo Area */}
        <div className="relative flex items-center justify-center h-24 border-b border-[var(--border-subtle)]">
          <div className="flex items-center gap-2">
            <motion.div
              animate={{ opacity: [0.6, 1, 0.6] }}
              transition={{ duration: 3, repeat: Infinity }}
              className="absolute inset-0 top-0 left-1/2 transform -translate-x-1/2 h-1 bg-gradient-to-r from-transparent via-[var(--accent)] to-transparent"
              style={{
                background: 'linear-gradient(90deg, transparent, var(--accent), transparent)',
                opacity: 0.3,
              }}
            />
            <Shield
              size={24}
              className="text-[var(--accent)] relative z-10"
              strokeWidth={3}
            />
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                transition={{ delay: 0.1 }}
                className="flex flex-col"
              >
                <span className="font-mono font-bold text-lg tracking-widest gradient-text">
                  ARGUS
                </span>
                <span className="text-[10px] text-[var(--text-tertiary)] font-medium tracking-wide">
                  AI Intelligence
                </span>
              </motion.div>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <motion.div
                key={item.path}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
              >
                <Link
                  to={item.path}
                  className={`
                    relative flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all
                    ${
                      isActive
                        ? 'bg-[var(--accent-muted)] border-l-3 border-[var(--accent)] text-[var(--accent)]'
                        : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface-hover)]'
                    }
                  `}
                >
                  <Icon size={20} className="flex-shrink-0" />
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.05 }}
                      className="text-sm font-medium flex-1"
                    >
                      {item.label}
                    </motion.span>
                  )}

                  {/* Alert indicator */}
                  {item.hasAlert && !collapsed && (
                    <div className="w-2 h-2 rounded-full bg-[var(--critical)] flex-shrink-0" />
                  )}

                  {item.isPulsing && (
                    <motion.div
                      animate={{ opacity: [0.5, 1, 0.5] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="w-2 h-2 rounded-full bg-[var(--critical)] flex-shrink-0"
                    />
                  )}

                  {/* Collapsed state tooltip */}
                  {collapsed && (
                    <motion.div
                      initial={{ opacity: 0, x: -8 }}
                      whileHover={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.2 }}
                      className="absolute left-full ml-3 px-3 py-1.5 bg-[var(--bg-elevated)] rounded-md whitespace-nowrap text-xs font-medium text-[var(--text-primary)] shadow-lg border border-[var(--border-default)] pointer-events-none z-50"
                    >
                      {item.label}
                    </motion.div>
                  )}
                </Link>
              </motion.div>
            );
          })}
        </nav>

        {/* Bottom Section */}
        <div className="border-t border-[var(--border-subtle)] p-3 space-y-3">
          {/* Theme toggle pill */}
          <motion.div
            className="relative inline-flex items-center gap-1.5 bg-[var(--bg-2)] border border-[var(--border-default)] rounded-full p-1 w-full justify-center"
          >
            <motion.button
              onClick={toggleTheme}
              className={`flex items-center justify-center w-7 h-7 rounded-full transition-all ${
                theme === 'dark' ? 'bg-[var(--accent-muted)]' : ''
              }`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Sun size={16} className="text-[var(--accent)]" />
            </motion.button>

            <motion.button
              onClick={toggleTheme}
              className={`flex items-center justify-center w-7 h-7 rounded-full transition-all ${
                theme === 'light' ? 'bg-[var(--accent-muted)]' : ''
              }`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Moon size={16} className="text-[var(--accent)]" />
            </motion.button>
          </motion.div>

          {/* Version badge */}
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center"
            >
              <span className="text-[10px] font-mono font-medium text-[var(--text-tertiary)] bg-[var(--bg-2)] px-2 py-1 rounded-full border border-[var(--border-subtle)] inline-block">
                v0.2.0
              </span>
            </motion.div>
          )}

          {/* Collapse button */}
          <motion.button
            onClick={() => setCollapsed(!collapsed)}
            className="w-full flex items-center justify-center p-2 rounded-lg hover:bg-[var(--bg-surface-hover)] transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <motion.div
              animate={{ rotate: collapsed ? 180 : 0 }}
              transition={{ duration: 0.3 }}
            >
              {collapsed ? (
                <ChevronRight size={20} className="text-[var(--text-secondary)]" />
              ) : (
                <ChevronLeft size={20} className="text-[var(--text-secondary)]" />
              )}
            </motion.div>
          </motion.button>
        </div>
      </motion.div>

      {/* Main content */}
      <motion.div
        animate={{ marginLeft: collapsed ? 72 : 260 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="flex-1 flex flex-col overflow-hidden"
      >
        {/* Top Bar */}
        <motion.div
          className="h-14 border-b border-[var(--border-subtle)] flex items-center justify-between px-6 bg-[var(--bg-1)] glass"
          initial={{ y: -10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          {/* Left: Page title */}
          <motion.div
            key={currentPageName}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            transition={{ duration: 0.2 }}
          >
            <h1 className="text-base font-semibold text-[var(--text-primary)]">
              {currentPageName}
            </h1>
          </motion.div>

          {/* Right: Actions */}
          <div className="flex items-center gap-4">
            {/* Search icon */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
              aria-label="Search"
            >
              <Search size={20} />
            </motion.button>

            {/* Notification bell */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="relative p-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
              aria-label="Notifications"
            >
              <Bell size={20} />
              {notificationCount > 0 && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute top-1 right-1 min-w-5 h-5 bg-[var(--critical)] rounded-full flex items-center justify-center text-white text-[10px] font-bold"
                >
                  {notificationCount}
                </motion.div>
              )}
            </motion.button>

            {/* User avatar */}
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="w-8 h-8 rounded-full bg-gradient-to-br from-[var(--accent)] to-[#06b6d4] flex items-center justify-center text-white text-xs font-bold cursor-pointer"
            >
              IA
            </motion.div>
          </div>
        </motion.div>

        {/* Main content area */}
        <main className="flex-1 overflow-y-auto bg-[var(--bg-0)]">
          {children}
        </main>
      </motion.div>
    </div>
  );
}
