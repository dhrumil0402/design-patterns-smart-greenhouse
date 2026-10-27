import { useEffect, useState } from "react";
import {
  fetchLocations,
  fetchOverview,
  type LocationOverviewDto,
  type LocationSummaryDto,
  type OverviewZoneDto,
} from "../../services/api";

interface Props {
  refreshKey?: number;
}

export default function OverviewPanel({ refreshKey = 0 }: Props) {
  const [locations, setLocations] = useState<LocationSummaryDto[]>([]);
  const [locationId, setLocationId] = useState("");
  const [overview, setOverview] = useState<LocationOverviewDto | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLocations()
      .then((data) => {
        setLocations(data);
        // If the selected location was deleted, clear the selection and the old snapshot.
        if (!data.some((location) => location.id === locationId)) {
          setLocationId("");
          setOverview(null);
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load locations"));
  }, [refreshKey]);

  // The whole snapshot comes from ONE overview request; Refresh repeats the same request.
  async function load(id: string) {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      setOverview(await fetchOverview(id));
    } catch (err) {
      setOverview(null);
      setError(err instanceof Error ? err.message : "Failed to load overview");
    } finally {
      setLoading(false);
    }
  }

  function handleLocationChange(id: string) {
    setLocationId(id);
    setOverview(null);
    load(id);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-2">
        <div className="min-w-48 flex-1 space-y-1">
          <label htmlFor="overview-location" className="text-xs font-medium text-gray-700">
            Location
          </label>
          <select
            id="overview-location"
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
        <button
          type="button"
          onClick={() => load(locationId)}
          disabled={!locationId || loading}
          className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}
      {!locationId && locations.length === 0 && (
        <p className="text-sm text-gray-500">No locations yet. Create one in Configuration first.</p>
      )}
      {!locationId && locations.length > 0 && (
        <p className="text-sm text-gray-500">Select a location to see its overview.</p>
      )}

      {overview && (
        <div className="space-y-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2">
              <p className="text-xs font-medium text-gray-500">Assigned devices</p>
              <p className="text-sm text-gray-800">
                <span className="text-lg font-semibold">{overview.device_counts.sensor}</span>{" "}
                sensors ·{" "}
                <span className="text-lg font-semibold">{overview.device_counts.actuator}</span>{" "}
                actuators
              </p>
            </div>
            <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2">
              <p className="text-xs font-medium text-gray-500">Strategy</p>
              {overview.strategy_key ? (
                <p className="text-sm font-semibold text-gray-800">{overview.strategy_key}</p>
              ) : (
                <p className="text-sm text-gray-500">No strategy saved</p>
              )}
            </div>
            <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2">
              <p className="text-xs font-medium text-gray-500">Recommendation</p>
              {overview.last_recommendation ? (
                <>
                  <span
                    className={
                      overview.last_recommendation.action === "irrigate"
                        ? "rounded bg-amber-100 px-1.5 py-0.5 text-xs font-medium text-amber-800"
                        : "rounded bg-gray-200 px-1.5 py-0.5 text-xs font-medium text-gray-700"
                    }
                  >
                    {overview.last_recommendation.action}
                  </span>
                  <p className="mt-1 text-xs text-gray-700">{overview.last_recommendation.reason}</p>
                </>
              ) : (
                <p className="text-sm text-gray-500">No recommendation (save a strategy first)</p>
              )}
            </div>
          </div>

          {overview.zones.length === 0 && (
            <p className="text-sm text-gray-500">This location has no zones.</p>
          )}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {overview.zones.map((zone) => (
              <ZoneCard key={zone.id} zone={zone} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ZoneCard({ zone }: { zone: OverviewZoneDto }) {
  return (
    <div className="rounded-md border border-gray-200 px-3 py-2">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-gray-800">{zone.name}</h4>
        <span className="text-xs text-gray-500">
          moisture {zone.moisture_threshold_low} – {zone.moisture_threshold_high}
        </span>
      </div>
      {zone.devices.length === 0 ? (
        <p className="mt-2 text-xs text-gray-500">No devices assigned to this zone.</p>
      ) : (
        <ul className="mt-2 space-y-1.5">
          {zone.devices.map((device) => {
            const reading = zone.latest_readings.find((r) => r.device_id === device.id);
            return (
              <li key={device.id} className="text-xs">
                <p className="text-gray-800">
                  <span className="font-medium">{device.display_name}</span>{" "}
                  <span className="text-gray-500">
                    · {device.role} · {device.device_type}
                  </span>
                </p>
                {reading ? (
                  <p className="text-gray-600">
                    {reading.value} {reading.unit} · tracking{" "}
                    {reading.tracking_enabled ? "on" : "off"} · every{" "}
                    {reading.sampling_interval_seconds}s ·{" "}
                    {new Date(reading.recorded_at).toLocaleString()}
                  </p>
                ) : (
                  <p className="text-gray-400">No reading yet</p>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
