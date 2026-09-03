import { useEffect, useState } from "react";
import { fetchHealth, type HealthResponse } from "../services/api";

type LoadState = "loading" | "loaded" | "error";

export default function HealthStatus() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [state, setState] = useState<LoadState>("loading");

  useEffect(() => {
    let cancelled = false;

    fetchHealth()
      .then((data) => {
        if (!cancelled) {
          setHealth(data);
          setState("loaded");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setState("error");
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const isHealthy = state === "loaded" && health?.status === "ok" && health?.db === "ok";

  const label =
    state === "loading"
      ? "Checking..."
      : state === "error"
        ? "API unreachable"
        : `API: ${health!.status} · DB: ${health!.db}`;

  const badgeClasses = isHealthy
    ? "bg-green-100 text-green-800 border-green-300"
    : state === "loading"
      ? "bg-gray-100 text-gray-600 border-gray-300"
      : "bg-red-100 text-red-800 border-red-300";

  const dotClasses = isHealthy
    ? "bg-green-500"
    : state === "loading"
      ? "bg-gray-400"
      : "bg-red-500";

  return (
    <span
      id="health-badge"
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm font-medium ${badgeClasses}`}
    >
      <span className={`h-2 w-2 rounded-full ${dotClasses}`} />
      {label}
    </span>
  );
}
