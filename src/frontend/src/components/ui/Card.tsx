import { motion } from 'framer-motion';
import { ReactNode } from 'react';

type CardVariant = 'default' | 'glass' | 'elevated' | 'critical';

interface CardProps {
  children: ReactNode;
  header?: ReactNode;
  footer?: ReactNode;
  variant?: CardVariant;
  glow?: boolean;
  className?: string;
  onClick?: () => void;
}

const variantStyles: Record<CardVariant, string> = {
  default:
    'bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-[var(--border-default)]',
  glass:
    'glass border-[var(--border-subtle)] hover:border-[var(--border-default)]',
  elevated:
    'bg-[var(--bg-elevated)] border border-[var(--border-default)] shadow-lg hover:border-[var(--border-strong)]',
  critical:
    'bg-[var(--bg-surface)] border-l-4 border-l-[var(--critical)] border border-[var(--border-subtle)] shadow-[var(--shadow-critical-glow)]',
};

export default function Card({
  children,
  header,
  footer,
  variant = 'default',
  glow = false,
  className = '',
  onClick,
}: CardProps) {
  return (
    <motion.div
      whileHover={{
        y: -2,
        boxShadow: 'var(--shadow-md)',
        transition: { duration: 0.2 },
      }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`
        rounded-[var(--radius-lg)] overflow-hidden transition-all
        ${variantStyles[variant]}
        ${glow ? 'glow-border' : ''}
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
    >
      {header && (
        <div className="px-5 py-3 border-b border-[var(--border-subtle)]">
          {header}
        </div>
      )}

      <div className="px-5 py-4">
        {children}
      </div>

      {footer && (
        <div className="px-5 py-3 border-t border-[var(--border-subtle)] bg-[var(--bg-2)]">
          {footer}
        </div>
      )}
    </motion.div>
  );
}
