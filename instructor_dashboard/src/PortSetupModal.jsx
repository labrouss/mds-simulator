import React, { useState, useEffect } from "react";

const MODES = ["auto", "F", "E", "TE"];
const SPEEDS = ["auto", "1000", "2000", "4000", "8000", "16000", "32000", "64000", "128000"];

export default function PortSetupModal({ apiUrl, portName, currentPort, onClose, onApplied }) {
  const [mode, setMode] = useState(currentPort?.mode || "auto");
  const [vsan, setVsan] = useState(currentPort?.vsan ?? 1);
  const [speed, setSpeed] = useState("auto");
  const [trunkVsans, setTrunkVsans] = useState("1");
  const [adminState, setAdminState] = useState(
    currentPort?.admin === "up" ? "up" : "down"
  );
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    fetch(`${apiUrl}/config/port/${portName}`)
      .then((r) => r.json())
      .then((data) => {
        if (data && !data.error) {
          setMode(data.port_mode || "auto");
          setVsan(data.vsan ?? 1);
          setSpeed(data.speed_config || "auto");
          setTrunkVsans((data.trunk_allowed_vsans || [1]).join(","));
          setAdminState(data.admin_state || "down");
        }
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [portName]);

  const apply = async () => {
    setSubmitting(true);
    setResult(null);
    try {
      const res = await fetch(`${apiUrl}/config/port`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          port: portName,
          mode,
          vsan: Number(vsan),
          speed,
          trunk_allowed_vsan: mode === "E" || mode === "TE" ? trunkVsans : undefined,
          admin_state: adminState,
        }),
      });
      const data = await res.json();
      setResult(data);
      onApplied && onApplied();
    } catch (e) {
      setResult({ status: "error", message: String(e) });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div style={styles.header}>
          <h3 style={styles.title}>Configure {portName}</h3>
          <button style={styles.closeBtn} onClick={onClose} aria-label="Close">
            &times;
          </button>
        </div>

        <div style={styles.field}>
          <label style={styles.label}>Port mode</label>
          <select style={styles.select} value={mode} onChange={(e) => setMode(e.target.value)}>
            {MODES.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>

        <div style={styles.field}>
          <label style={styles.label}>Speed</label>
          <select style={styles.select} value={speed} onChange={(e) => setSpeed(e.target.value)}>
            {SPEEDS.map((s) => (
              <option key={s} value={s}>
                {s === "auto" ? "auto" : `${s} Mbps`}
              </option>
            ))}
          </select>
        </div>

        {(mode === "E" || mode === "TE") ? (
          <div style={styles.field}>
            <label style={styles.label}>Trunk allowed VSANs</label>
            <input
              style={styles.input}
              value={trunkVsans}
              onChange={(e) => setTrunkVsans(e.target.value)}
              placeholder="e.g. 1,10,20"
            />
          </div>
        ) : (
          <div style={styles.field}>
            <label style={styles.label}>VSAN</label>
            <input
              style={styles.input}
              type="number"
              min="1"
              max="4093"
              value={vsan}
              onChange={(e) => setVsan(e.target.value)}
            />
          </div>
        )}

        <div style={styles.field}>
          <label style={styles.label}>Admin state</label>
          <div style={styles.toggleRow}>
            <button
              style={{
                ...styles.toggleBtn,
                ...(adminState === "up" ? styles.toggleBtnActiveUp : {}),
              }}
              onClick={() => setAdminState("up")}
            >
              no shutdown
            </button>
            <button
              style={{
                ...styles.toggleBtn,
                ...(adminState === "down" ? styles.toggleBtnActiveDown : {}),
              }}
              onClick={() => setAdminState("down")}
            >
              shutdown
            </button>
          </div>
        </div>

        <button style={styles.applyBtn} onClick={apply} disabled={submitting}>
          {submitting ? "Applying..." : "Apply Configuration"}
        </button>

        {result && (
          <div style={styles.resultBox}>
            {result.status === "ok" ? (
              <span style={{ color: "#2ecc71" }}>Applied successfully.</span>
            ) : (
              <span style={{ color: "#e74c3c" }}>
                {result.message || "Failed to apply configuration."}
              </span>
            )}
            {result.output && result.output.length > 0 && (
              <pre style={styles.pre}>{result.output.join("\n")}</pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,0.6)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 100,
  },
  modal: {
    background: "#171a20",
    border: "1px solid #2a2e37",
    borderRadius: 10,
    padding: 20,
    width: 340,
    maxHeight: "80vh",
    overflowY: "auto",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 14,
  },
  title: { fontSize: 16, margin: 0 },
  closeBtn: {
    background: "transparent",
    border: "none",
    color: "#999",
    fontSize: 20,
    cursor: "pointer",
    lineHeight: 1,
  },
  field: { marginBottom: 12 },
  label: {
    display: "block",
    fontSize: 11,
    color: "#999",
    marginBottom: 4,
    textTransform: "uppercase",
  },
  select: {
    width: "100%",
    background: "#1f232b",
    border: "1px solid #333",
    borderRadius: 6,
    padding: "6px 8px",
    color: "#e6e6e6",
    fontSize: 13,
  },
  input: {
    width: "100%",
    background: "#1f232b",
    border: "1px solid #333",
    borderRadius: 6,
    padding: "6px 8px",
    color: "#e6e6e6",
    fontSize: 13,
  },
  toggleRow: { display: "flex", gap: 8 },
  toggleBtn: {
    flex: 1,
    background: "#1f232b",
    border: "1px solid #333",
    borderRadius: 6,
    padding: "6px 8px",
    color: "#ccc",
    fontSize: 12,
    cursor: "pointer",
  },
  toggleBtnActiveUp: { background: "#2ecc7133", borderColor: "#2ecc71", color: "#2ecc71" },
  toggleBtnActiveDown: { background: "#e74c3c33", borderColor: "#e74c3c", color: "#e74c3c" },
  applyBtn: {
    width: "100%",
    background: "#2ecc71",
    color: "#0a0b0e",
    border: "none",
    borderRadius: 6,
    padding: "10px",
    fontSize: 13,
    fontWeight: 600,
    cursor: "pointer",
    marginTop: 4,
  },
  resultBox: { marginTop: 12, fontSize: 12 },
  pre: {
    background: "#0a0b0e",
    borderRadius: 6,
    padding: 8,
    marginTop: 6,
    fontSize: 11,
    whiteSpace: "pre-wrap",
    maxHeight: 120,
    overflowY: "auto",
  },
};
