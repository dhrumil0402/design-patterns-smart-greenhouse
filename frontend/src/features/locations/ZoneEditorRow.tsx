import { useState } from "react";
import { deleteZone, updateZone, type ZoneDto } from "../../services/api";

interface Props {
  zone: ZoneDto;
  canDelete: boolean;
  onChanged: () => void;
  onError: (message: string | null) => void;
}

export default function ZoneEditorRow({ zone, canDelete, onChanged, onError }: Props) {
  const [name, setName] = useState(zone.name);
  const [low, setLow] = useState(zone.moisture_threshold_low);
  const [high, setHigh] = useState(zone.moisture_threshold_high);
  const [watering, setWatering] = useState(String(zone.schedule?.watering ?? ""));
  const [busy, setBusy] = useState(false);

  async function handleSave() {
    if (!name.trim()) {
      onError("Zone name is required.");
      return;
    }
    if (low >= high) {
      onError(`Zone "${name}": low threshold must be less than high threshold.`);
      return;
    }
    setBusy(true);
    onError(null);
    try {
      const schedule: Record<string, unknown> = { ...zone.schedule };
      if (watering.trim()) schedule.watering = watering.trim();
      else delete schedule.watering;
      await updateZone(zone.location_id, zone.id, {
        name,
        moisture_threshold_low: low,
        moisture_threshold_high: high,
        schedule,
      });
      onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Failed to save zone");
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (!window.confirm(`Delete zone "${zone.name}"? Devices in it become unassigned.`)) return;
    setBusy(true);
    onError(null);
    try {
      await deleteZone(zone.location_id, zone.id);
      onChanged();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Failed to delete zone");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-2 rounded-md border border-gray-200 bg-white p-3">
      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
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
            value={low}
            onChange={(e) => setLow(Number(e.target.value))}
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
            value={high}
            onChange={(e) => setHigh(Number(e.target.value))}
            className="mt-0.5 w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
          />
        </label>
        <label className="flex-1 text-xs text-gray-600">
          Watering time
          <input
            type="text"
            placeholder="08:00"
            value={watering}
            onChange={(e) => setWatering(e.target.value)}
            className="mt-0.5 w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
          />
        </label>
      </div>
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={handleSave}
          disabled={busy}
          className="rounded-md bg-emerald-600 px-3 py-1 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          Save zone
        </button>
        <button
          type="button"
          onClick={handleDelete}
          disabled={busy || !canDelete}
          title={canDelete ? undefined : "A location must keep at least one zone"}
          className="text-xs text-red-600 hover:underline disabled:no-underline disabled:opacity-40"
        >
          Delete zone
        </button>
      </div>
    </div>
  );
}