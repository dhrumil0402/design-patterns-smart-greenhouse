import { useEffect, useState } from "react";
import {
  evaluateAutomation,
  fetchLocations,
  saveStrategy,
  type LocationSummaryDto,
  type RecommendationDto,
} from "../../services/api";

const STRATEGY_OPTIONS = [
  { key: "conservative", label: "Conservative (irrigate below the low threshold)" },
  { key: "aggressive", label: "Aggressive (irrigate below the band midpoint)" },
];

type LoadState = "loading" | "loaded" | "error";

interface Props {
  refreshKey?: number;
}

export default function StrategyPanel({ refreshKey = 0 }: Props) {
  const [locations, setLocations] = useState<LocationSummaryDto[]>([]);
  const [state, setState] = useState<LoadState>("loading");
  const [locationId, setLocationId] = useState("");
  const [strategyKey, setStrategyKey] = useState(STRATEGY_OPTIONS[0].key);
  const [result, setResult] = useState<RecommendationDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function loadLocations() {
    try {
      const data = await fetchLocations();
      setLocations(data);
      // If the selected location was deleted, clear the selection and any old result.
      if (!data.some((location) => location.id === locationId)) {
        setLocationId("");
        setResult(null);
      }
      setState("loaded");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load locations");
      setState("error");
    }
  }

  useEffect(() => {
    loadLocations();
  }, [refreshKey]);

  function handleLocationChange(id: string) {
    setLocationId(id);
    setResult(null);
    setError(null);
    setSuccess(null);
  }

  async function handleSave() {
    if (!locationId) {
      setError("Choose a location first.");
      return;
    }
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const saved = await saveStrategy(locationId, strategyKey);
      setSuccess(`Saved "${saved.strategy_key}" for this location.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save strategy");
    } finally {
      setBusy(false);
    }
  }

  async function handleEvaluate() {
    if (!locationId) {
      setError("Choose a location first.");
      return;
    }
    setBusy(true);
    setError(null);
    setSuccess(null);
    setResult(null);
    try {
      setResult(await evaluateAutomation(locationId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to evaluate automation");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}
      {success && (
        <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          {success}
        </p>
      )}

      {state === "loading" && <p className="text-sm text-gray-500">Loading locations...</p>}
      {state === "loaded" && locations.length === 0 && (
        <p className="text-sm text-gray-500">
          No locations yet. Create one in Configuration first.
        </p>
      )}

      {locations.length > 0 && (
        <div className="space-y-3">
          <div className="space-y-1">
            <label htmlFor="automation-location" className="text-xs font-medium text-gray-700">
              Location
            </label>
            <select
              id="automation-location"
              value={locationId}
              onChange={(e) => handleLocationChange(e.target.value)}
              className="w-full rounded-md border border-gray-300 bg-white px-2 py-1 text-sm"
            >
              <option value="">Select a location</option>
              {locations.map((location) => (
                <option key={location.id} value={location.id}>
                  {location.name}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <label htmlFor="automation-strategy" className="text-xs font-medium text-gray-700">
              Strategy
            </label>
            <select
              id="automation-strategy"
              value={strategyKey}
              onChange={(e) => setStrategyKey(e.target.value)}
              className="w-full rounded-md border border-gray-300 bg-white px-2 py-1 text-sm"
            >
              {STRATEGY_OPTIONS.map((option) => (
                <option key={option.key} value={option.key}>
                  {option.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500">
              Evaluate always uses the saved strategy, so save after changing the choice.
            </p>
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleSave}
              disabled={busy}
              className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              Save strategy
            </button>
            <button
              type="button"
              onClick={handleEvaluate}
              disabled={busy}
              className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              {busy ? "Working..." : "Evaluate"}
            </button>
          </div>
        </div>
      )}

      {result && (
        <div className="space-y-1 rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm">
          <div className="flex items-center justify-between">
            <span
              className={
                result.action === "irrigate"
                  ? "rounded bg-amber-100 px-1.5 py-0.5 text-xs font-medium text-amber-800"
                  : "rounded bg-gray-200 px-1.5 py-0.5 text-xs font-medium text-gray-700"
              }
            >
              {result.action}
            </span>
            <span className="text-xs text-gray-500">strategy: {result.strategy_key}</span>
          </div>
          <p className="text-gray-700">{result.reason}</p>
        </div>
      )}
    </div>
  );
}
