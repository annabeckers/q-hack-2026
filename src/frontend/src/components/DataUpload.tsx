import { useState, useRef, type DragEvent, type ChangeEvent } from "react";

const ACCEPTED_TYPES = [".pdf", ".csv", ".json"];
const ACCEPT_STRING = ".pdf,.csv,.json";

type UploadStatus = "idle" | "uploading" | "success" | "error";

export default function DataUpload() {
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [fileName, setFileName] = useState("");
  const [error, setError] = useState("");
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const upload = async (file: File) => {
    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (!ACCEPTED_TYPES.includes(ext)) {
      setError(`Unsupported file type: ${ext}. Use PDF, CSV, or JSON.`);
      setStatus("error");
      return;
    }

    setFileName(file.name);
    setStatus("uploading");
    setProgress(0);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const xhr = new XMLHttpRequest();
      await new Promise<void>((resolve, reject) => {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) setProgress(Math.round((e.loaded / e.total) * 100));
        };
        xhr.onload = () => (xhr.status < 400 ? resolve() : reject(new Error(xhr.statusText)));
        xhr.onerror = () => reject(new Error("Upload failed"));
        xhr.open("POST", "/api/v1/data/upload");
        const token = localStorage.getItem("token");
        if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
        xhr.send(formData);
      });
      setStatus("success");
      setProgress(100);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setStatus("error");
    }
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) upload(file);
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) upload(file);
  };

  return (
    <div style={containerStyle}>
      <h3 style={{ fontSize: 16, marginBottom: 12, color: "#fafafa" }}>Upload Data</h3>
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        style={{
          ...dropZoneStyle,
          borderColor: isDragOver ? "#3b82f6" : "#333",
          background: isDragOver ? "#1e3a5f" : "#0a0a0a",
        }}
      >
        <input ref={inputRef} type="file" accept={ACCEPT_STRING} onChange={handleChange} style={{ display: "none" }} />
        <p style={{ color: "#a3a3a3", fontSize: 14 }}>
          {status === "idle" && "Drop a file here or click to browse"}
          {status === "uploading" && `Uploading ${fileName}...`}
          {status === "success" && `${fileName} uploaded successfully`}
          {status === "error" && (error || "Upload failed")}
        </p>
        <p style={{ color: "#525252", fontSize: 12, marginTop: 4 }}>PDF, CSV, JSON</p>
      </div>

      {status === "uploading" && (
        <div style={progressBarBg}>
          <div style={{ ...progressBarFill, width: `${progress}%` }} />
        </div>
      )}

      {status === "success" && (
        <div style={{ marginTop: 8, color: "#4ade80", fontSize: 13 }}>Upload complete</div>
      )}
      {status === "error" && (
        <div style={{ marginTop: 8, color: "#f87171", fontSize: 13 }}>{error}</div>
      )}
    </div>
  );
}

const containerStyle: React.CSSProperties = {
  background: "#1a1a1a",
  borderRadius: 12,
  padding: 20,
};

const dropZoneStyle: React.CSSProperties = {
  border: "2px dashed #333",
  borderRadius: 8,
  padding: 32,
  textAlign: "center",
  cursor: "pointer",
  transition: "border-color 0.2s, background 0.2s",
};

const progressBarBg: React.CSSProperties = {
  marginTop: 12,
  height: 6,
  background: "#0a0a0a",
  borderRadius: 3,
  overflow: "hidden",
};

const progressBarFill: React.CSSProperties = {
  height: "100%",
  background: "#3b82f6",
  borderRadius: 3,
  transition: "width 0.2s",
};
