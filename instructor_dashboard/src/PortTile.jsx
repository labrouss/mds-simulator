import React from "react";

const STATUS_COLORS = {
  UP: "#2ecc71",
  TRUNKING: "#27ae60",
  FLOGI_PENDING: "#f1c40f",
  ELP_NEGOTIATE: "#f1c40f",
  DOMAIN_MERGE: "#f39c12",
  INITIALIZING: "#3498db",
  LINK_DOWN: "#e67e22",
  OFFLINE: "#7f8c8d",
  ERR_DISABLED: "#e74c3c",
};

export default function PortTile({ name, port, onAction, onConfigure }) {
  const color = STATUS_COLORS[port.status] || "#7f8c8d";
  const [open, setOpen] = React.useState(false);

  return (
    <div style={styles.tile} onClick={() => setOpen(!open)}>
      <div style={{ ...styles.dot, background: color }} />
      <div style={styles.name}>{name}</div>
      <div style={styles.status}>{port.status}</div>
      <div style={styles.meta}>
        vsan {port.vsan} &middot; {port.speed || "--"}
      </div>

      {open && (
        <div style={styles.menu} onClick={(e) => e.stopPropagation()}>
          <button style={styles.btn} onClick={() => onAction("unplug_sfp", name)}>
            Unplug SFP
          </button>
          <button style={styles.btn} onClick={() => onAction("insert_sfp", name)}>
            Insert SFP (16G)
          </button>
          <button style={styles.btn} onClick={() => onAction("flap_link", name)}>
            Flap Link
          </button>
          <button style={styles.btn} onClick={() => onAction("degrade_signal", name)}>
            Degrade Signal
          </button>
          <div style={styles.divider} />
          <button
            style={{ ...styles.btn, ...styles.configureBtn }}
            onClick={() => onConfigure(name)}
          >
            Configure Port...
          </button>
        </div>
      )}
    </div>
  );
}

const styles = {
  tile: {
    position: "relative",
    background: "#1a1d24",
    border: "1px solid #2a2e37",
    borderRadius: 8,
    padding: "10px 12px",
    cursor: "pointer",
    minWidth: 110,
    userSelect: "none",
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: "50%",
    marginBottom: 6,
  },
  name: { fontWeight: 600, fontSize: 13 },
  status: { fontSize: 11, color: "#aaa", marginTop: 2 },
  meta: { fontSize: 10, color: "#777", marginTop: 4 },
  menu: {
    position: "absolute",
    top: "100%",
    left: 0,
    zIndex: 10,
    background: "#20242c",
    border: "1px solid #333",
    borderRadius: 6,
    padding: 6,
    display: "flex",
    flexDirection: "column",
    gap: 4,
    marginTop: 4,
    boxShadow: "0 4px 12px rgba(0,0,0,0.4)",
  },
  divider: {
    height: 1,
    background: "#333",
    margin: "2px 0",
  },
  configureBtn: {
    background: "#01696f33",
    color: "#4f98a3",
    fontWeight: 600,
  },
  btn: {
    background: "#2a2e37",
    color: "#e6e6e6",
    border: "none",
    borderRadius: 4,
    padding: "6px 10px",
    fontSize: 11,
    cursor: "pointer",
    textAlign: "left",
    whiteSpace: "nowrap",
  },
};
