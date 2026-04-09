import { motion } from 'framer-motion';
import { ReactNode } from 'react';

type CardVariant = 'default' | 'glass' | 'elevated' | 'critical' | 'premium';

interface CardProps {
  children: ReactNode;
  header?: ReactNode;
  footer?: ReactNode;
  variant?: CardVariant;
  glow?: boolean;
  className?: string;
  onClick?: () => void;
  style?: React.CSSProperties;
}

const variantStyles: Record<CardVariant, string> = {
  default:
    'bg-white border border-[var(--border-subtle)] hover:border-[var(--border-default)] shadow-[var(--shadow-sm)] hover:shadow-[var(--shadow-md)]',
  glass:
    'glass-premium hover:border-[var(--border-default)]',
  elevated:
    'bg-white border border-[var(--border-default)] shadow-[var(--shadow-md)] hover:shadow-[var(--shadow-lg)]',
  critical:
    'bg-white border-l-4 border-l-[var(--critical)] border border-[var(--border-subtle)] shadow-[var(--shadow-sm)]',
  premium:
    'glass-premium animated-border hover-glow',
};

export default function Card({
  children,
  header,
  footer,
  variant = 'default',
  glow = false,
  className = '',
  onClick,
  style,
}: CardProps) {
  return (
    <motion.div
      whileHover={{
        y: -2,
        transition: { type: 'spring', stiffness: 400, damping: 25 },
      }}
      whileTap={onClick ? { scale: 0.99 } : undefined}
      onClick={onClick}
      style={style}
      className={`
        rounded-[var(--radius-lg)] overflow-hidden transition-all duration-300
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
