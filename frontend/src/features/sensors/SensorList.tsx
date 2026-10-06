import { useEffect, useState } from "react";
import {
  createSensor,
  fetchSensorReadings,
  fetchSampling,
  fetchSensors,
  readSensor,
  updateSampling,
  type ReadingDto,
  type SamplingDto,
  type SensorDto,
  type SensorType,
} from "../../services/api";

type LoadState = "loading" | "loaded" | "error";

interface SensorCardProps {
  sensor: SensorDto;
}

function SensorCard({ sensor }: SensorCardProps) {
  const [reading, setReading] = useState<ReadingDto | null>(null);
  const [sampling, setSampling] = useState<SamplingDto | null>(null);
  const [intervalText, setIntervalText] = useState("");
  const [loadingReading, setLoadingReading] = useState(false);
  const [savingSampling, setSavingSampling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadReading() {
    try {
      const readings = await fetchSensorReadings(sensor.id, 1);
      setReading(readings[0] ?? null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load latest reading",
      );
    }
  }

  async function loadSampling() {
    try {
      const settings = await fetchSampling(sensor.id);
      setSampling(settings);
      setIntervalText(String(settings.sampling_interval_seconds));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load sampling settings",
      );
    }
  }

  useEffect(() => {
    void loadReading();
    void loadSampling();

    // Temporary Phase 5 polling. Phase 12 replaces this with WebSocket updates.
    const timer = window.setInterval(() => {
      void loadReading();
    }, 5000);

    return () => window.clearInterval(timer);
  }, [sensor.id]);

  async function handleReadNow() {
    setLoadingReading(true);
    setError(null);

    try {
      const latest = await readSensor(sensor.id);
      setReading(latest);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to read sensor",
      );
    } finally {
      setLoadingReading(false);
    }
  }

  async function handleSaveSampling() {
    const interval = Number(intervalText);

    if (!Number.isInteger(interval) || interval < 5) {
      setError("Sampling interval must be an integer of at least 5 seconds.");
      return;
    }

    if (sampling === null) {
      return;
    }

    setSavingSampling(true);
    setError(null);

    try {
      const updated = await updateSampling(sensor.id, {
        sampling_interval_seconds: interval,
        tracking_enabled: sampling.tracking_enabled,
      });

      setSampling(updated);
      setIntervalText(String(updated.sampling_interval_seconds));
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to update sampling settings",
      );
    } finally {
      setSavingSampling(false);
    }
  }

  function handleTrackingChange(
    event: React.ChangeEvent<HTMLInputElement>,
  ) {
    setSampling((current) =>
      current === null
        ? current
        : {
            ...current,
            tracking_enabled: event.target.checked,
          },
    );
  }

  return (
    <li className="rounded-md border border-gray-200 bg-gray-50 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-medium text-gray-900">
            {sensor.display_name}
          </h3>
          <p className="text-xs text-gray-500">{sensor.device_type}</p>
        </div>

        {reading && (
          <span className="rounded-full bg-blue-100 px-2 py-1 text-xs font-medium text-blue-800">
            {reading.source}
          </span>
        )}
      </div>

      <div className="mt-3">
        {reading ? (
          <p className="text-lg font-semibold text-gray-900">
            {reading.value} {reading.unit}
          </p>
        ) : (
          <p className="text-sm text-gray-500">No stored reading yet.</p>
        )}

        {reading && (
          <p className="text-xs text-gray-500">
            Recorded {new Date(reading.recorded_at).toLocaleString()}
          </p>
        )}
      </div>

      <div className="mt-4 flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-xs text-gray-600">
          Sampling interval in seconds
          <input
            type="number"
            min={5}
            value={intervalText}
            onChange={(event) => setIntervalText(event.target.value)}
            disabled={sampling === null || savingSampling}
            className="w-32 rounded border border-gray-300 px-2 py-1 text-sm"
          />
        </label>

        <label className="flex items-center gap-2 pb-1 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={sampling?.tracking_enabled ?? false}
            onChange={handleTrackingChange}
            disabled={sampling === null || savingSampling}
          />
          Tracking enabled
        </label>

        <button
          type="button"
          onClick={() => void handleSaveSampling()}
          disabled={sampling === null || savingSampling}
          className="rounded-md bg-gray-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
        >
          {savingSampling ? "Saving..." : "Save sampling"}
        </button>

        <button
          type="button"
          onClick={() => void handleReadNow()}
          disabled={loadingReading}
          className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {loadingReading ? "Reading..." : "Read now"}
        </button>
      </div>

      {error && (
        <p className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}
    </li>
  );
}

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
      setError(
        err instanceof Error ? err.message : "Failed to load sensors",
      );
      setState("error");
    }
  }

  useEffect(() => {
    void loadSensors();
  }, []);

  async function handleAdd(type: SensorType) {
    setCreating(type);
    setError(null);

    try {
      await createSensor(type);
      await loadSensors();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create sensor",
      );
    } finally {
      setCreating(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => void handleAdd("moisture")}
          disabled={creating !== null}
          className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {creating === "moisture" ? "Adding..." : "Add moisture sensor"}
        </button>

        <button
          type="button"
          onClick={() => void handleAdd("light")}
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

      {state === "loading" && (
        <p className="text-sm text-gray-500">Loading sensors...</p>
      )}

      {state === "error" && (
        <button
          type="button"
          onClick={() => void loadSensors()}
          className="rounded-md bg-gray-700 px-3 py-1.5 text-sm text-white"
        >
          Retry
        </button>
      )}

      {state === "loaded" && sensors.length === 0 && (
        <p className="text-sm text-gray-500">
          No sensors yet. Add one above.
        </p>
      )}

      {state === "loaded" && sensors.length > 0 && (
        <ul className="space-y-3">
          {sensors.map((sensor) => (
            <SensorCard key={sensor.id} sensor={sensor} />
          ))}
        </ul>
      )}
    </div>
  );
}