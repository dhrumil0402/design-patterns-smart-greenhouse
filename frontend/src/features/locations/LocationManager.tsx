import { useEffect, useState, type FormEvent } from "react";
import {
  addZone,
  deleteLocation,
  fetchLocationConfig,
  fetchLocations,
  type LocationConfigDto,
  type LocationSummaryDto,
  type ZoneCreateInput,
} from "../../services/api";
import LocationConfigWizard from "./LocationConfigWizard";
import ZoneEditorRow from "./ZoneEditorRow";

type LoadState = "loading" | "loaded" | "error";

interface Props {
  onChanged?: () => void;
}

function emptyZone(): ZoneCreateInput {
  return { name: "", moisture_threshold_low: 0.2, moisture_threshold_high: 0.4 };
}

export default function LocationManager({ onChanged }: Props) {
  const [locations, setLocations] = useState<LocationSummaryDto[]>([]);
  const [state, setState] = useState<LoadState>("loading");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [config, setConfig] = useState<LocationConfigDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [newZone, setNewZone] = useState<ZoneCreateInput>(emptyZone());
  const [busy, setBusy] = useState(false);

  async function loadLocations() {
    try {
      setLocations(await fetchLocations());
      setState("loaded");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load locations");
      setState("error");
    }
  }

  useEffect(() => {
    loadLocations();
  }, []);

  async function selectLocation(id: string) {
    setSelectedId(id);
    setError(null);
    try {
      setConfig(await fetchLocationConfig(id));
    } catch (err) {
      setConfig(null);
      setError(err instanceof Error ? err.message : "Failed to load location");
    }
  }

  async function reloadSelected() {
    if (selectedId) await selectLocation(selectedId);
    onChanged?.();
  }

  async function handleCreated(created: LocationConfigDto) {
    setSelectedId(created.location.id);
    setConfig(created);
    await loadLocations();
    onChanged?.();
  }

  async function handleDeleteLocation() {
    if (!config) return;
    const message = `Delete location "${config.location.name}" and all its zones? Devices in it become unassigned.`;
    if (!window.confirm(message)) return;
    setBusy(true);
    setError(null);
    try {
      await deleteLocation(config.location.id);
      setSelectedId(null);
      setConfig(null);
      await loadLocations();
      onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete location");
    } finally {
      setBusy(false);
    }
  }

  async function handleAddZone(e: FormEvent) {
    e.preventDefault();
    if (!config) return;
    if (!newZone.name.trim()) {
      setError("Zone name is required.");
      return;
    }
    if (newZone.moisture_threshold_low >= newZone.moisture_threshold_high) {
      setError(`Zone "${newZone.name}": low threshold must be less than high threshold.`);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await addZone(config.location.id, newZone);
      setNewZone(emptyZone());
      await reloadSelected();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add zone");
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

      <div className="space-y-2">
        <h4 className="text-sm font-medium text-gray-700">Saved locations</h4>
        {state === "loading" && <p className="text-sm text-gray-500">Loading locations...</p>}
        {state === "loaded" && locations.length === 0 && (
          <p className="text-sm text-gray-500">No locations yet. Create one below.</p>
        )}
        <ul className="flex flex-wrap gap-2">
          {locations.map((location) => (
            <li key={location.id}>
              <button
                type="button"
                onClick={() => selectLocation(location.id)}
                className={
                  location.id === selectedId
                    ? "rounded-md bg-emerald-600 px-3 py-1 text-sm font-medium text-white"
                    : "rounded-md border border-gray-300 bg-white px-3 py-1 text-sm text-gray-700 hover:bg-gray-50"
                }
              >
                {location.name}
              </button>
            </li>
          ))}
        </ul>
      </div>

      {config && (
        <div className="space-y-3 rounded-md border border-gray-200 bg-gray-50 p-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-900">{config.location.name}</span>
            <button
              type="button"
              onClick={handleDeleteLocation}
              disabled={busy}
              className="text-xs text-red-600 hover:underline disabled:opacity-50"
            >
              Delete location
            </button>
          </div>

          {config.zones.map((zone) => (
            <ZoneEditorRow
              key={zone.id}
              zone={zone}
              canDelete={config.zones.length > 1}
              onChanged={reloadSelected}
              onError={setError}
            />
          ))}

          <form onSubmit={handleAddZone} className="space-y-2 border-t border-gray-200 pt-3">
            <span className="text-xs font-medium text-gray-700">Add a zone</span>
            <input
              type="text"
              value={newZone.name}
              onChange={(e) => setNewZone({ ...newZone, name: e.target.value })}
              placeholder="Bench 2"
              className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
            />
            <div className="flex gap-2">
              <input
                type="number"
                step="0.01"
                min="0"
                max="1"
                value={newZone.moisture_threshold_low}
                onChange={(e) =>
                  setNewZone({ ...newZone, moisture_threshold_low: Number(e.target.value) })
                }
                className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
              />
              <input
                type="number"
                step="0.01"
                min="0"
                max="1"
                value={newZone.moisture_threshold_high}
                onChange={(e) =>
                  setNewZone({ ...newZone, moisture_threshold_high: Number(e.target.value) })
                }
                className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
              />
            </div>
            <button
              type="submit"
              disabled={busy}
              className="rounded-md bg-emerald-600 px-3 py-1 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              Add zone
            </button>
          </form>
        </div>
      )}

      <div className="space-y-2 border-t border-gray-200 pt-4">
        <h4 className="text-sm font-medium text-gray-700">New location</h4>
        <LocationConfigWizard onCreated={handleCreated} />
      </div>
    </div>
  );
}