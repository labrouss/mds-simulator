import { useEffect, useRef, useState, useCallback } from "react";

/**
 * Connects to one switch's instructor WebSocket endpoint and keeps
 * live port state + event log in sync. Reconnects automatically.
 */
export function useSwitchSocket(wsUrl) {
  const [hostname, setHostname] = useState("");
  const [ports, setPorts] = useState({});
  const [logs, setLogs] = useState([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    let retryTimer = null;

    function connect() {
      if (cancelled) return;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => setConnected(true);

      ws.onmessage = (evt) => {
        const msg = JSON.parse(evt.data);
        if (msg.type === "init") {
          setHostname(msg.hostname);
          setPorts(msg.ports || {});
          setLogs(msg.logs || []);
        } else if (msg.type === "ports") {
          setPorts(msg.ports || {});
        } else if (msg.type === "log") {
          setLogs((prev) => [...prev.slice(-199), msg.message]);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        if (!cancelled) retryTimer = setTimeout(connect, 2000);
      };

      ws.onerror = () => ws.close();
    }

    connect();
    return () => {
      cancelled = true;
      clearTimeout(retryTimer);
      wsRef.current?.close();
    };
  }, [wsUrl]);

  return { hostname, ports, logs, connected };
}
