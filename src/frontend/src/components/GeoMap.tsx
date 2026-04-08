import { useState, useCallback } from "react";
import DeckGL from "@deck.gl/react";
import { ScatterplotLayer } from "@deck.gl/layers";

export interface MapPoint {
  position: [number, number]; // [lng, lat]
  color: [number, number, number, number?]; // RGBA 0-255
  radius: number;
}

interface GeoMapProps {
  points: MapPoint[];
}

const INITIAL_VIEW_STATE = {
  longitude: 0,
  latitude: 20,
  zoom: 1.5,
  pitch: 0,
  bearing: 0,
};

const CARTO_DARK_MATTER =
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

export default function GeoMap({ points }: GeoMapProps) {
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);

  const layers = [
    new ScatterplotLayer<MapPoint>({
      id: "scatterplot",
      data: points,
      getPosition: (d) => d.position,
      getFillColor: (d) => {
        const c = d.color;
        return [c[0], c[1], c[2], c[3] ?? 200];
      },
      getRadius: (d) => d.radius,
      radiusMinPixels: 3,
      radiusMaxPixels: 30,
      pickable: true,
      opacity: 0.8,
      stroked: true,
      getLineColor: [255, 255, 255, 80],
      lineWidthMinPixels: 1,
    }),
  ];

  const handleViewStateChange = useCallback(
    ({ viewState: vs }: { viewState: typeof INITIAL_VIEW_STATE }) => {
      setViewState(vs);
    },
    [],
  );

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        background: "#0a0a0a",
        borderRadius: 12,
        overflow: "hidden",
        position: "relative",
      }}
    >
      <DeckGL
        viewState={viewState}
        onViewStateChange={handleViewStateChange}
        controller={true}
        layers={layers}
        style={{ width: "100%", height: "100%" }}
      >
        {/*
          CARTO Dark Matter basemap requires maplibre-gl or similar.
          For a lightweight setup, we render points on a dark canvas.
          To add a full basemap tile layer, install maplibre-gl and
          add: <Map mapStyle={CARTO_DARK_MATTER} />
        */}
      </DeckGL>

      <div
        style={{
          position: "absolute",
          bottom: 12,
          left: 12,
          background: "rgba(0, 0, 0, 0.7)",
          color: "#666",
          padding: "4px 10px",
          borderRadius: 6,
          fontSize: 11,
        }}
      >
        deck.gl | {points.length} points
      </div>
    </div>
  );
}

// Re-export for convenience
export { CARTO_DARK_MATTER };
