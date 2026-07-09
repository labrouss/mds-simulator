import { useEffect, useRef, useState } from "react";

export function useSwitchSocket(wsUrl) {
  const [hostname, setHostname] = useState("");
  const [ports, setPorts] = useState({});
  const [logs, setLogs] = useState([]);
  const [connected, setConnected] = useState(false);
  const [transport, setTransport] = useState("ws");
  const wsRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    let retryTimer = null;
    let pollTimer = null;
    let failures = 0;
    const apiUrl = wsUrl.replace(/^ws/, "http").replace(/\/ws$/, "");

    async function poll() {
      try {
        const r = await fetch(`${apiUrl}/state/full`);
        const msg = await r.json();
        if (msg.hostname) setHostname(msg.hostname);
        if (msg.ports) setPorts(msg.ports || {});
        if (msg.logs) setLogs(msg.logs || []);
        setConnected(true);
        setTransport("poll");
      } catch (e) {
        setConnected(false);
      }
      if (!cancelled) pollTimer = setTimeout(poll, 2000);
    }

    function connect() {
      if (cancelled) return;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        failures = 0;
        setConnected(true);
        setTransport("ws");
      };

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
        failures += 1;
        setConnected(false);
        if (failures >= 3) {
          poll();
        } else if (!cancelled) {
          retryTimer = setTimeout(connect, 1500);
        }
      };

      ws.onerror = () => ws.close();
    }

    connect();
    return () => {
      cancelled = true;
      clearTimeout(retryTimer);
      clearTimeout(pollTimer);
      wsRef.current?.close();
    };
  }, [wsUrl]);

  return { hostname, ports, logs, connected, transport };
}
