import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isRegister) {
        await register(email, password, name);
      } else {
        await login(email, password);
      }
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
      <form onSubmit={handleSubmit} style={{ width: 360, padding: 32 }}>
        <h1 style={{ fontSize: 24, marginBottom: 24 }}>{isRegister ? "Register" : "Login"}</h1>

        {error && (
          <div style={{ background: "#3b1219", color: "#f87171", padding: 12, borderRadius: 8, marginBottom: 16 }}>
            {error}
          </div>
        )}

        {isRegister && (
          <input
            type="text"
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required={isRegister}
            style={inputStyle}
          />
        )}

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={inputStyle}
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={inputStyle}
        />

        <button type="submit" disabled={loading} style={buttonStyle}>
          {loading ? "..." : isRegister ? "Register" : "Login"}
        </button>

        <button type="button" onClick={() => setIsRegister(!isRegister)} style={linkStyle}>
          {isRegister ? "Already have an account? Login" : "Need an account? Register"}
        </button>
      </form>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: 12,
  marginBottom: 12,
  borderRadius: 8,
  border: "1px solid #333",
  background: "#1a1a1a",
  color: "#fafafa",
  fontSize: 14,
  outline: "none",
};

const buttonStyle: React.CSSProperties = {
  width: "100%",
  padding: 12,
  borderRadius: 8,
  border: "none",
  background: "#3b82f6",
  color: "#fff",
  fontSize: 14,
  fontWeight: 600,
  cursor: "pointer",
  marginBottom: 12,
};

const linkStyle: React.CSSProperties = {
  width: "100%",
  padding: 8,
  border: "none",
  background: "transparent",
  color: "#60a5fa",
  fontSize: 13,
  cursor: "pointer",
  display: "block",
  textAlign: "center",
};
