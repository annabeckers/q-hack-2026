import { motion } from 'framer-motion';

interface GlowingOrbProps {
  color?: string;
  size?: number;
  x?: string;
  y?: string;
  delay?: number;
}

export default function GlowingOrb({
  color = 'rgba(99, 102, 241, 0.15)',
  size = 400,
  x = '50%',
  y = '50%',
  delay = 0,
}: GlowingOrbProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{
        opacity: [0.3, 0.5, 0.3],
        scale: [1, 1.15, 1],
      }}
      transition={{
        duration: 6,
        repeat: Infinity,
        ease: 'easeInOut',
        delay,
      }}
      style={{
        position: 'absolute',
        left: x,
        top: y,
        width: size,
        height: size,
        borderRadius: '50%',
        background: `radial-gradient(circle, ${color} 0%, transparent 70%)`,
        filter: 'blur(60px)',
        pointerEvents: 'none',
        transform: 'translate(-50%, -50%)',
        willChange: 'transform, opacity',
        zIndex: 0,
      }}
    />
  );
}
