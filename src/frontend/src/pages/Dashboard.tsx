import { useState, useRef, useEffect, lazy, Suspense, type FormEvent } from "react";
import { useAuth } from "../auth/AuthContext";
import { useAgentStream, type AgentMessage } from "../hooks/useAgentStream";
import DataUpload from "../components/DataUpload";
import DarkModeToggle from "../components/DarkModeToggle";

const Globe3D = lazy(() => import("../components/Globe3D"));
const Scene3D = lazy(() => import("../components/Scene3D"));
const GeoMap = lazy(() => import("../components/GeoMap"));

const FRAMEWORKS = ["strands", "langgraph", "openai", "anthropic", "a2a"] as const;

type ViewMode = "chat" | "globe" | "3d" | "map";

const VIEW_OPTIONS: { key: ViewMode; label: string }[] = [
  { key: "chat", label: "Chat" },
  { key: "globe", label: "Globe" },
  { key: "3d", label: "3D" },
  { key: "map", label: "Map" },
];

const TYPE_COLORS: Record<AgentMessage["type"], string> = {
  thinking: "#a78bfa",
  response: "#60a5fa",
  tool_call: "#fbbf24",
  done: "#4ade80",
};

export default function Dashboard() {
  const { user, logout } = useAuth();
  const { messages, isConnected, send } = useAgentStream();
  const [input, setInput] = useState("");
  const [framework, setFramework] = useState<(typeof FRAMEWORKS)[number]>("strands");
  const [view, setView] = useState<ViewMode>("chat");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;
    send({ message: trimmed, framework });
    setInput("");
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", maxWidth: 960, margin: "0 auto", padding: "16px 16px 0" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12, flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <h1 style={{ fontSize: 20, color: "#fafafa" }}>Agent Chat</h1>
          <span style={{ fontSize: 12, color: isConnected ? "#4ade80" : "#f87171" }}>
            {isConnected ? "Connected" : "Disconnected"}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {/* View mode toggles */}
          <div style={{ display: "flex", gap: 2, background: "#1a1a1a", borderRadius: 8, padding: 2 }}>
            {VIEW_OPTIONS.map((opt) => (
              <button
                key={opt.key}
                onClick={() => setView(opt.key)}
                style={{
                  padding: "5px 10px",
                  borderRadius: 6,
                  border: "none",
                  background: view === opt.key ? "#3b82f6" : "transparent",
                  color: view === opt.key ? "#fff" : "#a3a3a3",
                  fontSize: 12,
                  fontWeight: view === opt.key ? 600 : 400,
                  cursor: "pointer",
                  transition: "background 0.15s, color 0.15s",
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <DarkModeToggle />

          <span style={{ color: "#a3a3a3", fontSize: 13 }}>{user?.name || user?.email}</span>
          <button onClick={logout} style={logoutBtnStyle}>Logout</button>
        </div>
      </div>

      {/* Main content */}
      <div style={{ display: "flex", gap: 16, flex: 1, minHeight: 0 }}>
        {view === "chat" && (
          <>
            {/* Chat panel */}
            <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
              {/* Messages */}
              <div style={messageListStyle}>
                {messages.length === 0 && (
                  <div style={{ color: "#525252", textAlign: "center", marginTop: 64, fontSize: 14 }}>
                    Send a message to start chatting with an agent.
                  </div>
                )}
                {messages.map((msg, i) => (
                  <div key={i} style={messageBubbleStyle}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                      <span style={{ fontWeight: 600, fontSize: 13, color: "#fafafa" }}>{msg.agent}</span>
                      <span style={{
                        fontSize: 11,
                        padding: "2px 8px",
                        borderRadius: 4,
                        background: TYPE_COLORS[msg.type] + "22",
                        color: TYPE_COLORS[msg.type],
                      }}>
                        {msg.type}
                      </span>
                    </div>
                    <div style={{ fontSize: 14, color: "#d4d4d4", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
                      {msg.content}
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <form onSubmit={handleSend} style={{ display: "flex", gap: 8, padding: "12px 0", flexShrink: 0 }}>
                <select
                  value={framework}
                  onChange={(e) => setFramework(e.target.value as typeof framework)}
                  style={selectStyle}
                >
                  {FRAMEWORKS.map((f) => (
                    <option key={f} value={f}>{f}</option>
                  ))}
                </select>
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Send a message..."
                  style={inputStyle}
                />
                <button type="submit" style={sendBtnStyle}>Send</button>
              </form>
            </div>

            {/* Sidebar */}
            <div style={{ width: 280, flexShrink: 0 }}>
              <DataUpload />
            </div>
          </>
        )}

        {view === "globe" && (
          <div style={{ flex: 1, minHeight: 0 }}>
            <Suspense fallback={<LoadingFallback label="Loading Globe..." />}>
              <Globe3D points={[]} />
            </Suspense>
          </div>
        )}

        {view === "3d" && (
          <div style={{ flex: 1, minHeight: 0 }}>
            <Suspense fallback={<LoadingFallback label="Loading 3D Scene..." />}>
              <Scene3D data={[]} />
            </Suspense>
          </div>
        )}

        {view === "map" && (
          <div style={{ flex: 1, minHeight: 0 }}>
            <Suspense fallback={<LoadingFallback label="Loading Map..." />}>
              <GeoMap points={[]} />
            </Suspense>
          </div>
        )}
      </div>
    </div>
  );
}

function LoadingFallback({ label }: { label: string }) {
  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#0a0a0a",
        borderRadius: 12,
        color: "#525252",
        fontSize: 14,
      }}
    >
      {label}
    </div>
  );
}

const messageListStyle: React.CSSProperties = {
  flex: 1,
  overflowY: "auto",
  background: "#0a0a0a",
  borderRadius: 12,
  padding: 16,
};

const messageBubbleStyle: React.CSSProperties = {
  background: "#1a1a1a",
  borderRadius: 8,
  padding: 12,
  marginBottom: 8,
};

const inputStyle: React.CSSProperties = {
  flex: 1,
  padding: 12,
  borderRadius: 8,
  border: "1px solid #333",
  background: "#1a1a1a",
  color: "#fafafa",
  fontSize: 14,
  outline: "none",
};

const selectStyle: React.CSSProperties = {
  padding: "8px 12px",
  borderRadius: 8,
  border: "1px solid #333",
  background: "#1a1a1a",
  color: "#fafafa",
  fontSize: 13,
  outline: "none",
  cursor: "pointer",
};

const sendBtnStyle: React.CSSProperties = {
  padding: "8px 20px",
  borderRadius: 8,
  border: "none",
  background: "#3b82f6",
  color: "#fff",
  fontSize: 14,
  fontWeight: 600,
  cursor: "pointer",
};

const logoutBtnStyle: React.CSSProperties = {
  padding: "6px 14px",
  borderRadius: 8,
  border: "1px solid #333",
  background: "transparent",
  color: "#fafafa",
  cursor: "pointer",
  fontSize: 13,
};
