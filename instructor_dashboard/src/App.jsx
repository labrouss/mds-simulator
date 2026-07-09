import React, { useState } from "react";
import SwitchPanel from "./SwitchPanel.jsx";

const pageHost = window.location.hostname;
const pageProto = window.location.protocol === "https:" ? "wss" : "ws";
const pageHttpProto = window.location.protocol === "https:" ? "https" : "http";

const DEFAULT_SWITCHES = [
  { label: "Switch 1", host: pageHost, port: 18001 },
];

export default function App() {
  const [switches, setSwitches] = useState(DEFAULT_SWITCHES);
  const [newHost, setNewHost] = useState(pageHost);
  const [newPort, setNewPort] = useState(18002);

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

      <div style={{ marginBottom: 12, color: '#9ca3af', fontSize: 12 }}>
        Add additional switch panels by entering the host and instructor port. The dashboard defaults to one switch to avoid connection noise.
      </div>

      {switches.map((sw, idx) => (
        <div key={idx} style={{ position: "relative" }}>
          <button style={styles.removeBtn} onClick={() => removeSwitch(idx)}>
            remove
          </button>
          <SwitchPanel
            label={sw.label}
            wsUrl={`${pageProto}://${sw.host}:${sw.port}/ws`}
            apiUrl={`${pageHttpProto}://${sw.host}:${sw.port}`}
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
