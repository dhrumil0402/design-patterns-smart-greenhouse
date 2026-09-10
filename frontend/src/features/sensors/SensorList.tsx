import { useEffect, useState } from "react";
import { createSensor, fetchSensors, type SensorDto, type SensorType } from "../../services/api";

type LoadState = "loading" | "loaded" | "error";

export default function SensorList() {
  const [sensors, setSensors] = useState<SensorDto[]>([]);
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState<SensorType | null>(null);

  async function loadSensors() {
    setState("loading");
    setError(null);
    try {
      const data = await fetchSensors();
      setSensors(data);
      setState("loaded");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sensors");
      setState("error");
    }
  }

  useEffect(() => {
    loadSensors();
  }, []);

  async function handleAdd(type: SensorType) {
    setCreating(type);
    setError(null);
    try {
      await createSensor(type);
      await loadSensors();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create sensor");
    } finally {
      setCreating(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => handleAdd("moisture")}
          disabled={creating !== null}
          className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {creating === "moisture" ? "Adding..." : "Add moisture sensor"}
        </button>
        <button
          type="button"
          onClick={() => handleAdd("light")}
          disabled={creating !== null}
          className="rounded-md bg-amber-500 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50"
        >
          {creating === "light" ? "Adding..." : "Add light sensor"}
        </button>
      </div>

      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {state === "loading" && <p className="text-sm text-gray-500">Loading sensors...</p>}

      {state === "loaded" && sensors.length === 0 && (
        <p className="text-sm text-gray-500">No sensors yet. Add one above.</p>
      )}

      {state === "loaded" && sensors.length > 0 && (
        <ul className="space-y-2">
          {sensors.map((sensor) => (
            <li
              key={sensor.id}
              className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-900">{sensor.display_name}</span>
                <span className="text-xs text-gray-500">{sensor.device_type}</span>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                {Object.entries(sensor.default_config)
                  .map(([key, value]) => `${key}: ${value}`)
                  .join(" · ")}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
