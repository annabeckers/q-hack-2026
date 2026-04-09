import { useEffect, useRef, useState } from 'react';
import { motion, animate, useInView } from 'framer-motion';

interface CountUpProps {
  target: number;
  duration?: number;
  format?: 'currency' | 'percentage' | 'plain';
  className?: string;
  prefix?: string;
  suffix?: string;
}

function formatNumber(
  value: number,
  format: 'currency' | 'percentage' | 'plain' = 'plain'
): string {
  const rounded = Math.round(value);

  switch (format) {
    case 'currency':
      return `€${new Intl.NumberFormat('en-US').format(rounded)}`;
    case 'percentage':
      return `${rounded}%`;
    case 'plain':
    default:
      return new Intl.NumberFormat('en-US').format(rounded);
  }
}

export default function CountUp({
  target,
  duration = 1.8,
  format = 'plain',
  className = '',
  prefix = '',
  suffix = '',
}: CountUpProps) {
  const [display, setDisplay] = useState('0');
  const [isAnimating, setIsAnimating] = useState(false);
  const containerRef = useRef<HTMLSpanElement>(null);
  const hasAnimated = useRef(false);
  const isInView = useInView(containerRef, { once: true, margin: '-50px' });

  useEffect(() => {
    if (isInView && !hasAnimated.current) {
      hasAnimated.current = true;
      setIsAnimating(true);
      const controls = animate(0, target, {
        duration,
        ease: [0.25, 0.46, 0.45, 0.94],
        onUpdate(value) {
          setDisplay(formatNumber(value, format));
        },
        onComplete() {
          setIsAnimating(false);
        },
      });
      return () => controls.stop();
    }
  }, [isInView, target, duration, format]);

  return (
    <motion.span
      ref={containerRef}
      className={`tabular-nums ${className}`}
      initial={{ opacity: 0, scale: 0.8, filter: 'blur(4px)' }}
      animate={isInView ? { opacity: 1, scale: 1, filter: 'blur(0px)' } : undefined}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      style={{
        textShadow: isAnimating
          ? '0 0 20px var(--accent-glow), 0 0 40px rgba(99, 102, 241, 0.1)'
          : 'none',
        transition: 'text-shadow 0.3s ease',
      }}
    >
      {prefix}{display}{suffix}
    </motion.span>
  );
}
