import { useState } from "react";
import {
  createLocationConfig,
  type LocationConfigDto,
  type ZoneCreateInput,
} from "../../services/api";

type SubmitState = "idle" | "submitting" | "error";

function emptyZone(): ZoneCreateInput {
  return { name: "", moisture_threshold_low: 0.2, moisture_threshold_high: 0.4 };
}

export default function LocationConfigWizard() {
  const [locationName, setLocationName] = useState("");
  const [zones, setZones] = useState<ZoneCreateInput[]>([emptyZone()]);
  const [state, setState] = useState<SubmitState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LocationConfigDto | null>(null);

  function updateZone(index: number, patch: Partial<ZoneCreateInput>) {
    setZones((prev) => prev.map((z, i) => (i === index ? { ...z, ...patch } : z)));
  }

  function addZone() {
    setZones((prev) => [...prev, emptyZone()]);
  }

  function removeZone(index: number) {
    setZones((prev) => prev.filter((_, i) => i !== index));
  }

  function clientSideIssue(): string | null {
    if (!locationName.trim()) return "Location name is required.";
    if (zones.length === 0) return "At least one zone is required.";
    for (const zone of zones) {
      if (!zone.name.trim()) return "Every zone needs a name.";
      if (zone.moisture_threshold_low >= zone.moisture_threshold_high) {
        return `Zone "${zone.name}": low threshold must be less than high threshold.`;
      }
    }
    return null;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const issue = clientSideIssue();
    if (issue) {
      setError(issue);
      setState("error");
      return;
    }

    setState("submitting");
    setError(null);
    try {
      const saved = await createLocationConfig(locationName, zones);
      setResult(saved);
      setState("idle");
      setLocationName("");
      setZones([emptyZone()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save location config");
      setState("error");
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Location name</label>
          <input
            type="text"
            value={locationName}
            onChange={(e) => setLocationName(e.target.value)}
            placeholder="Lab Site A"
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm"
          />
        </div>

        <div className="space-y-3">
          {zones.map((zone, index) => (
            <div
              key={index}
              className="rounded-md border border-gray-200 bg-gray-50 p-3 space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Zone {index + 1}</span>
                {zones.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeZone(index)}
                    className="text-xs text-red-600 hover:underline"
                  >
                    Remove
                  </button>
                )}
              </div>
              <input
                type="text"
                value={zone.name}
                onChange={(e) => updateZone(index, { name: e.target.value })}
                placeholder="Bench 1"
                className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
              />
              <div className="flex gap-2">
                <label className="flex-1 text-xs text-gray-600">
                  Low threshold
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={zone.moisture_threshold_low}
                    onChange={(e) =>
                      updateZone(index, { moisture_threshold_low: Number(e.target.value) })
                    }
                    className="mt-0.5 w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
                  />
                </label>
                <label className="flex-1 text-xs text-gray-600">
                  High threshold
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={zone.moisture_threshold_high}
                    onChange={(e) =>
                      updateZone(index, { moisture_threshold_high: Number(e.target.value) })
                    }
                    className="mt-0.5 w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
                  />
                </label>
              </div>
            </div>
          ))}
          <button
            type="button"
            onClick={addZone}
            className="text-sm text-emerald-700 hover:underline"
          >
            + Add another zone
          </button>
        </div>

        {error && (
          <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={state === "submitting"}
          className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {state === "submitting" ? "Saving..." : "Save location config"}
        </button>
      </form>

      {result && (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm">
          <p className="font-medium text-emerald-800">
            Saved: {result.location.name} ({result.location.id})
          </p>
          <ul className="mt-2 space-y-1">
            {result.zones.map((z) => (
              <li key={z.id} className="text-emerald-700">
                {z.name}: {z.moisture_threshold_low}–{z.moisture_threshold_high}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}