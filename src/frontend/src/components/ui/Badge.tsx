import { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';

type BadgeVariant = 'critical' | 'high' | 'medium' | 'success' | 'info' | 'neutral';
type BadgeSize = 'sm' | 'md';

interface BadgeProps {
  variant: BadgeVariant;
  children: ReactNode;
  size?: BadgeSize;
  dot?: boolean;
  icon?: LucideIcon;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  critical:
    'bg-[var(--critical-muted)] text-[var(--critical)] border border-[var(--critical)]/30',
  high:
    'bg-[var(--high-muted)] text-[var(--high)] border border-[var(--high)]/30',
  medium:
    'bg-[var(--medium-muted)] text-[var(--medium)] border border-[var(--medium)]/30',
  success:
    'bg-[var(--success-muted)] text-[var(--success)] border border-[var(--success)]/30',
  info:
    'bg-[var(--info-muted)] text-[var(--info)] border border-[var(--info)]/30',
  neutral:
    'bg-[var(--accent-muted)] text-[var(--text-secondary)] border border-[var(--border-default)]',
};

const sizeStyles: Record<BadgeSize, string> = {
  sm: 'text-[10px] px-2 py-0.5',
  md: 'text-xs px-2.5 py-1',
};

const dotColors: Record<BadgeVariant, string> = {
  critical: 'bg-[var(--critical)]',
  high: 'bg-[var(--high)]',
  medium: 'bg-[var(--medium)]',
  success: 'bg-[var(--success)]',
  info: 'bg-[var(--info)]',
  neutral: 'bg-[var(--text-secondary)]',
};

export default function Badge({
  variant,
  children,
  size = 'md',
  dot = false,
  icon: Icon,
  className = '',
}: BadgeProps) {
  return (
    <motion.span
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      whileHover={{ scale: 1.05 }}
      className={`
        inline-flex items-center gap-1.5 rounded-full
        font-medium tracking-wide font-semibold
        border transition-all
        ${sizeStyles[size]}
        ${variantStyles[variant]}
        ${variant === 'critical' ? 'pulse-critical' : ''}
        ${className}
      `}
    >
      {dot && (
        <motion.div
          animate={{ scale: [1, 1.2, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
          className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${dotColors[variant]}`}
        />
      )}

      {Icon && (
        <Icon className="flex-shrink-0" size={size === 'sm' ? 12 : 14} />
      )}

      {children}
    </motion.span>
  );
}
