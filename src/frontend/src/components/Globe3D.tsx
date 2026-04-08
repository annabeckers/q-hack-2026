import { useEffect, useRef, useState, useCallback } from "react";
import ReactGlobe, { type GlobeMethods } from "react-globe.gl";

export interface GlobePoint {
  lat: number;
  lng: number;
  label: string;
  size: number;
  color: string;
}

interface Globe3DProps {
  points: GlobePoint[];
}

export default function Globe3D({ points }: Globe3DProps) {
  const globeRef = useRef<GlobeMethods | undefined>(undefined);
  const [selectedLabel, setSelectedLabel] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (entry) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });

    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const globe = globeRef.current;
    if (!globe) return;

    globe.controls().autoRotate = true;
    globe.controls().autoRotateSpeed = 0.8;
    globe.controls().enableZoom = true;
  }, []);

  const handlePointClick = useCallback((point: object) => {
    const p = point as GlobePoint;
    setSelectedLabel(p.label);
    setTimeout(() => setSelectedLabel(null), 3000);
  }, []);

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        height: "100%",
        background: "#000",
        position: "relative",
        borderRadius: 12,
        overflow: "hidden",
      }}
    >
      <ReactGlobe
        ref={globeRef}
        width={dimensions.width}
        height={dimensions.height}
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
        backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
        pointsData={points}
        pointLat="lat"
        pointLng="lng"
        pointLabel="label"
        pointRadius="size"
        pointColor="color"
        pointAltitude={0.01}
        pointsMerge={false}
        onPointClick={handlePointClick}
        atmosphereColor="#3a7bd5"
        atmosphereAltitude={0.2}
      />

      {selectedLabel && (
        <div
          style={{
            position: "absolute",
            top: 16,
            left: "50%",
            transform: "translateX(-50%)",
            background: "rgba(0, 0, 0, 0.85)",
            color: "#fafafa",
            padding: "8px 16px",
            borderRadius: 8,
            fontSize: 14,
            fontWeight: 600,
            border: "1px solid #333",
            pointerEvents: "none",
          }}
        >
          {selectedLabel}
        </div>
      )}
    </div>
  );
}
