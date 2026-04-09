import { useRef, useEffect } from 'react';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  opacity: number;
}

export default function AnimatedBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particlesRef = useRef<Particle[]>([]);
  const mouseRef = useRef({ x: -1000, y: -1000 });
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = 0;
    let height = 0;

    const resizeCanvas = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.scale(dpr, dpr);
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Particles — subtle floating nodes
    const count = Math.min(50, Math.floor((width * height) / 28000));
    particlesRef.current = Array.from({ length: count }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.1,
      vy: (Math.random() - 0.5) * 0.1,
      radius: Math.random() * 1.5 + 0.5,
      opacity: Math.random() * 0.12 + 0.03,
    }));

    const handleMouseMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };
    window.addEventListener('mousemove', handleMouseMove);

    const connectionDistance = 160;

    const animate = (timestamp: number) => {
      ctx.clearRect(0, 0, width, height);

      // Soft gradient orbs — very subtle, professional
      const t = timestamp * 0.00006;

      // Navy blue orb (top-left)
      const g1x = width * (0.12 + 0.08 * Math.sin(t));
      const g1y = height * (0.18 + 0.06 * Math.cos(t * 0.7));
      const g1 = ctx.createRadialGradient(g1x, g1y, 0, g1x, g1y, 400);
      g1.addColorStop(0, 'rgba(30, 58, 138, 0.04)');
      g1.addColorStop(1, 'rgba(30, 58, 138, 0)');
      ctx.fillStyle = g1;
      ctx.fillRect(0, 0, width, height);

      // Sky blue orb (center-right)
      const g2x = width * (0.82 + 0.06 * Math.cos(t * 0.5));
      const g2y = height * (0.55 + 0.08 * Math.sin(t * 0.8));
      const g2 = ctx.createRadialGradient(g2x, g2y, 0, g2x, g2y, 350);
      g2.addColorStop(0, 'rgba(59, 130, 246, 0.03)');
      g2.addColorStop(1, 'rgba(59, 130, 246, 0)');
      ctx.fillStyle = g2;
      ctx.fillRect(0, 0, width, height);

      // Subtle slate orb (bottom)
      const g3x = width * (0.45 + 0.1 * Math.sin(t * 0.3));
      const g3y = height * (0.88 + 0.05 * Math.cos(t * 0.6));
      const g3 = ctx.createRadialGradient(g3x, g3y, 0, g3x, g3y, 300);
      g3.addColorStop(0, 'rgba(100, 116, 139, 0.025)');
      g3.addColorStop(1, 'rgba(100, 116, 139, 0)');
      ctx.fillStyle = g3;
      ctx.fillRect(0, 0, width, height);

      const particles = particlesRef.current;
      const mouse = mouseRef.current;

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        // Gentle mouse attraction
        const dx = mouse.x - p.x;
        const dy = mouse.y - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 220 && dist > 0) {
          p.vx += (dx / dist) * 0.002;
          p.vy += (dy / dist) * 0.002;
        }

        // Damping
        p.vx *= 0.997;
        p.vy *= 0.997;

        p.x += p.vx;
        p.y += p.vy;

        // Wrap around
        if (p.x < -20) p.x = width + 20;
        if (p.x > width + 20) p.x = -20;
        if (p.y < -20) p.y = height + 20;
        if (p.y > height + 20) p.y = -20;

        // Draw particle — navy blue dots
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(30, 58, 138, ${p.opacity})`;
        ctx.fill();

        // Connections — very subtle lines
        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const cdx = p.x - p2.x;
          const cdy = p.y - p2.y;
          const cdist = Math.sqrt(cdx * cdx + cdy * cdy);

          if (cdist < connectionDistance) {
            const lineOpacity = (1 - cdist / connectionDistance) * 0.04;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(30, 58, 138, ${lineOpacity})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }

        // Mouse proximity glow — subtle blue
        if (dist < 180 && dist > 0) {
          const glowOpacity = (1 - dist / 180) * 0.08;
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.radius + 4, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(59, 130, 246, ${glowOpacity})`;
          ctx.fill();
        }
      }

      rafRef.current = requestAnimationFrame(animate);
    };

    rafRef.current = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener('resize', resizeCanvas);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        pointerEvents: 'none',
      }}
    />
  );
}
