import React, { useState } from "react";
import SwitchPanel from "./SwitchPanel.jsx";

/**
 * Configure one entry per switch instance in your lab. For a local
 * single-switch run: instructor API on :8000, WebSocket at /ws.
 * For docker-compose two_switch_fabric: switch1 -> :18001, switch2 -> :18002
 * (see docker-compose.yml port mappings for INSTRUCTOR_PORT).
 */
const DEFAULT_SWITCHES = [
  { label: "Switch 1", host: "localhost", port: 8000 },
  { label: "Switch 2", host: "localhost", port: 8001 },
];

export default function App() {
  const [switches, setSwitches] = useState(DEFAULT_SWITCHES);
  const [newHost, setNewHost] = useState("localhost");
  const [newPort, setNewPort] = useState(8002);

  const addSwitch = () => {
    setSwitches([
      ...switches,
      { label: `Switch ${switches.length + 1}`, host: newHost, port: Number(newPort) },
    ]);
  };

  const removeSwitch = (idx) => {
    setSwitches(switches.filter((_, i) => i !== idx));
  };

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <h1 style={styles.title}>MDS Simulator &mdash; Instructor Dashboard</h1>
        <div style={styles.addRow}>
          <input
            style={styles.input}
            value={newHost}
            onChange={(e) => setNewHost(e.target.value)}
            placeholder="host"
          />
          <input
            style={{ ...styles.input, width: 80 }}
            value={newPort}
            onChange={(e) => setNewPort(e.target.value)}
            placeholder="port"
          />
          <button style={styles.addBtn} onClick={addSwitch}>
            + Add Switch
          </button>
        </div>
      </header>

      {switches.map((sw, idx) => (
        <div key={idx} style={{ position: "relative" }}>
          <button style={styles.removeBtn} onClick={() => removeSwitch(idx)}>
            remove
          </button>
          <SwitchPanel
            label={sw.label}
            wsUrl={`ws://${sw.host}:${sw.port}/ws`}
            apiUrl={`http://${sw.host}:${sw.port}`}
          />
        </div>
      ))}
    </div>
  );
}

const styles = {
  app: { maxWidth: 1100, margin: "0 auto", padding: "24px 16px" },
  header: { marginBottom: 20 },
  title: { fontSize: 22, marginBottom: 12 },
  addRow: { display: "flex", gap: 8, alignItems: "center" },
  input: {
    background: "#1a1d24",
    border: "1px solid #333",
    borderRadius: 6,
    padding: "6px 10px",
    color: "#e6e6e6",
    fontSize: 13,
  },
  addBtn: {
    background: "#2ecc71",
    color: "#0a0b0e",
    border: "none",
    borderRadius: 6,
    padding: "7px 14px",
    fontSize: 13,
    fontWeight: 600,
    cursor: "pointer",
  },
  removeBtn: {
    position: "absolute",
    top: 8,
    right: 8,
    zIndex: 5,
    background: "transparent",
    color: "#e74c3c",
    border: "1px solid #e74c3c55",
    borderRadius: 6,
    padding: "4px 8px",
    fontSize: 11,
    cursor: "pointer",
  },
};
