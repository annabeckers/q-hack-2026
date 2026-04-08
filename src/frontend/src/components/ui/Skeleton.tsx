import { CSSProperties } from 'react';
import { motion } from 'framer-motion';

type SkeletonVariant = 'text' | 'heading' | 'card' | 'chart' | 'circle';

interface SkeletonProps {
  variant?: SkeletonVariant;
  className?: string;
  count?: number;
  width?: string | number;
  height?: string | number;
  size?: number; // for circle variant
}

const variantDefaults: Record<SkeletonVariant, CSSProperties> = {
  text: {
    height: 16,
    borderRadius: 6,
    marginBottom: 8,
  },
  heading: {
    height: 24,
    borderRadius: 6,
    marginBottom: 16,
  },
  card: {
    height: 200,
    borderRadius: 14,
  },
  chart: {
    height: 300,
    borderRadius: 14,
  },
  circle: {
    width: 48,
    height: 48,
    borderRadius: '50%',
  },
};

export default function Skeleton({
  variant = 'text',
  className = '',
  count = 1,
  width,
  height,
  size = 48,
}: SkeletonProps) {
  const baseStyle = variantDefaults[variant];

  // Random width for text lines for more natural appearance
  const getRandomWidth = () => {
    if (variant === 'text') {
      return `${Math.random() * 30 + 60}%`;
    }
    return width;
  };

  return (
    <>
      {Array.from({ length: count }).map((_, i) => {
        const customStyle: CSSProperties = {
          ...baseStyle,
          ...(width && { width }),
          ...(height && { height }),
          ...(variant === 'circle' && { width: size, height: size }),
          width: variant === 'text' ? getRandomWidth() : width || baseStyle.width,
        };

        return (
          <motion.div
            key={i}
            initial={{ opacity: 0.6 }}
            animate={{ opacity: 1 }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              repeatType: 'reverse',
            }}
            className={`skeleton ${className}`}
            style={customStyle}
          />
        );
      })}
    </>
  );
}
