import React, { useCallback } from "react";
import { useSwitchSocket } from "./useSwitchSocket.js";
import PortTile from "./PortTile.jsx";

export default function SwitchPanel({ label, wsUrl, apiUrl }) {
  const { hostname, ports, logs, connected } = useSwitchSocket(wsUrl);

  const onAction = useCallback(
    async (action, portName) => {
      const endpoint = `${apiUrl}/faults/${action}`;
      const body =
        action === "insert_sfp"
          ? { port: portName, sfp_type: "16G_SW" }
          : { port: portName };
      try {
        await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
      } catch (e) {
        console.error("Fault injection failed", e);
      }
    },
    [apiUrl]
  );

  const failPsu = async (n) => {
    await fetch(`${apiUrl}/faults/fail_psu/${n}`, { method: "POST" });
  };
  const failFan = async () => {
    await fetch(`${apiUrl}/faults/fail_fan`, { method: "POST" });
  };

  return (
    <div style={styles.panel}>
      <div style={styles.header}>
        <div>
          <span style={styles.hostname}>{hostname || label}</span>
          <span
            style={{
              ...styles.badge,
              background: connected ? "#2ecc7133" : "#e74c3c33",
              color: connected ? "#2ecc71" : "#e74c3c",
            }}
          >
            {connected ? "connected" : "disconnected"}
          </span>
        </div>
        <div style={styles.chassisActions}>
          <button style={styles.chassisBtn} onClick={() => failPsu(1)}>
            Fail PSU1
          </button>
          <button style={styles.chassisBtn} onClick={() => failPsu(2)}>
            Fail PSU2
          </button>
          <button style={styles.chassisBtn} onClick={failFan}>
            Fail Fan
          </button>
        </div>
      </div>

      <div style={styles.grid}>
        {Object.entries(ports).map(([name, port]) => (
          <PortTile key={name} name={name} port={port} onAction={onAction} />
        ))}
      </div>

      <div style={styles.logHeader}>Live Event Log</div>
      <div style={styles.logBox}>
        {logs.slice(-30).map((line, i) => (
          <div key={i} style={styles.logLine}>
            {line}
          </div>
        ))}
      </div>
    </div>
  );
}

const styles = {
  panel: {
    background: "#12141a",
    border: "1px solid #23262e",
    borderRadius: 10,
    padding: 16,
    marginBottom: 24,
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 14,
  },
  hostname: { fontSize: 18, fontWeight: 700, marginRight: 10 },
  badge: {
    fontSize: 11,
    padding: "3px 8px",
    borderRadius: 12,
  },
  chassisActions: { display: "flex", gap: 8 },
  chassisBtn: {
    background: "#2a2e37",
    color: "#e6e6e6",
    border: "1px solid #3a3f4a",
    borderRadius: 6,
    padding: "6px 10px",
    fontSize: 12,
    cursor: "pointer",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(110px, 1fr))",
    gap: 8,
    marginBottom: 16,
  },
  logHeader: { fontSize: 12, color: "#888", marginBottom: 6, textTransform: "uppercase" },
  logBox: {
    background: "#0a0b0e",
    borderRadius: 6,
    padding: 10,
    maxHeight: 180,
    overflowY: "auto",
    fontFamily: "monospace",
    fontSize: 11,
  },
  logLine: { color: "#8fd694", marginBottom: 2, whiteSpace: "pre-wrap" },
};
