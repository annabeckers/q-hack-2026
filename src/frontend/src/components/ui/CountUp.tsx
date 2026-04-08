import { useEffect, useRef, useState } from 'react';
import { motion, animate } from 'framer-motion';

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
  duration = 1.5,
  format = 'plain',
  className = '',
  prefix = '',
  suffix = '',
}: CountUpProps) {
  const [display, setDisplay] = useState('0');
  const hasAnimated = useRef(false);

  useEffect(() => {
    if (!hasAnimated.current) {
      hasAnimated.current = true;
      const controls = animate(0, target, {
        duration,
        ease: 'easeOut',
        onUpdate(value) {
          setDisplay(formatNumber(value, format));
        },
      });
      return () => controls.stop();
    }
  }, [target, duration, format]);

  return (
    <motion.span
      className={`tabular-nums font-variant-numeric: tabular-nums ${className}`}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      {prefix}{display}{suffix}
    </motion.span>
  );
}
