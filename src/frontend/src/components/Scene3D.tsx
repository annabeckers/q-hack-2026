import { useState, useCallback, useRef } from "react";
import { Canvas, useFrame, type ThreeEvent } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";
import * as THREE from "three";

export interface DataPoint3D {
  x: number;
  y: number;
  z: number;
  value: number;
  label: string;
}

interface Scene3DProps {
  data: DataPoint3D[];
}

function valueToColor(value: number, min: number, max: number): THREE.Color {
  const t = max === min ? 0.5 : (value - min) / (max - min);
  const r = t;
  const g = 0.1;
  const b = 1 - t;
  return new THREE.Color(r, g, b);
}

interface DataSphereProps {
  point: DataPoint3D;
  color: THREE.Color;
  onHover: (label: string | null) => void;
}

function DataSphere({ point, color, onHover }: DataSphereProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  useFrame((_, delta) => {
    if (!meshRef.current) return;
    meshRef.current.rotation.y += delta * 0.3;
  });

  const handlePointerOver = useCallback(
    (e: ThreeEvent<PointerEvent>) => {
      e.stopPropagation();
      setHovered(true);
      onHover(point.label);
      document.body.style.cursor = "pointer";
    },
    [onHover, point.label],
  );

  const handlePointerOut = useCallback(() => {
    setHovered(false);
    onHover(null);
    document.body.style.cursor = "auto";
  }, [onHover]);

  const scale = hovered ? 1.3 : 1;
  const radius = 0.15 + (point.value / 100) * 0.25;

  return (
    <mesh
      ref={meshRef}
      position={[point.x, point.y, point.z]}
      scale={scale}
      onPointerOver={handlePointerOver}
      onPointerOut={handlePointerOut}
    >
      <sphereGeometry args={[radius, 24, 24]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={hovered ? 0.6 : 0.2}
        roughness={0.3}
        metalness={0.4}
      />
      {hovered && (
        <Html distanceFactor={8} style={{ pointerEvents: "none" }}>
          <div
            style={{
              background: "rgba(0, 0, 0, 0.85)",
              color: "#fafafa",
              padding: "6px 12px",
              borderRadius: 6,
              fontSize: 12,
              fontWeight: 600,
              whiteSpace: "nowrap",
              border: "1px solid #333",
            }}
          >
            {point.label} ({point.value})
          </div>
        </Html>
      )}
    </mesh>
  );
}

function SceneContent({ data }: { data: DataPoint3D[] }) {
  const [, setHoveredLabel] = useState<string | null>(null);

  const values = data.map((d) => d.value);
  const minVal = values.length > 0 ? Math.min(...values) : 0;
  const maxVal = values.length > 0 ? Math.max(...values) : 1;

  const handleHover = useCallback((label: string | null) => {
    setHoveredLabel(label);
  }, []);

  return (
    <>
      <ambientLight intensity={0.4} />
      <pointLight position={[10, 10, 10]} intensity={1.2} />
      <pointLight position={[-10, -10, -5]} intensity={0.5} color="#4466ff" />

      {data.map((point, i) => (
        <DataSphere
          key={`${point.label}-${i}`}
          point={point}
          color={valueToColor(point.value, minVal, maxVal)}
          onHover={handleHover}
        />
      ))}

      <OrbitControls
        enableDamping
        dampingFactor={0.05}
        minDistance={2}
        maxDistance={30}
      />

      <gridHelper args={[20, 20, "#222", "#111"]} />
    </>
  );
}

export default function Scene3D({ data }: Scene3DProps) {
  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "#080808",
        borderRadius: 12,
        overflow: "hidden",
      }}
    >
      <Canvas
        camera={{ position: [5, 5, 5], fov: 60 }}
        gl={{ antialias: true }}
        style={{ width: "100%", height: "100%" }}
      >
        <color attach="background" args={["#080808"]} />
        <SceneContent data={data} />
      </Canvas>
    </div>
  );
}
