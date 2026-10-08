import { useEffect, useState } from "react";
import {
  assignDeviceZone,
  fetchAllLocationConfigs,
  fetchDevices,
  provisionDeviceFamily,
  type DeviceDto,
  type DeviceFamily,
  type LocationConfigDto,
} from "../../services/api";
import DeviceFamilySwitcher from "./DeviceFamilySwitcher";

type LoadState = "loading" | "loaded" | "error";

interface Props {
  refreshKey?: number;
}

export default function DeviceList({ refreshKey = 0 }: Props) {
  const [family, setFamily] = useState<DeviceFamily>("simulation");
  const [devices, setDevices] = useState<DeviceDto[]>([]);
  const [configs, setConfigs] = useState<LocationConfigDto[]>([]);
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [provisioning, setProvisioning] = useState(false);
  const [assigningId, setAssigningId] = useState<string | null>(null);

  async function loadDevices(selectedFamily: DeviceFamily) {
    setState("loading");
    setError(null);
    try {
      const data = await fetchDevices({ family: selectedFamily });
      setDevices(data);
      setState("loaded");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load devices");
      setState("error");
    }
  }

  async function loadConfigs() {
    try {
      setConfigs(await fetchAllLocationConfigs());
    } catch (err) {
      setConfigs([]);
      setError(err instanceof Error ? err.message : "Failed to load locations");
    }
  }

  useEffect(() => {
    loadDevices(family);
    loadConfigs();
  }, [family, refreshKey]);

  async function handleProvision() {
    setProvisioning(true);
    setError(null);
    try {
      await provisionDeviceFamily(family);
      await loadDevices(family);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to provision family");
    } finally {
      setProvisioning(false);
    }
  }

  async function handleAssign(deviceId: string, zoneId: string | null) {
    setAssigningId(deviceId);
    setError(null);
    try {
      const updated = await assignDeviceZone(deviceId, zoneId);
      setDevices((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to assign zone");
    } finally {
      setAssigningId(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <DeviceFamilySwitcher selected={family} onSelect={setFamily} disabled={provisioning} />
        <button
          type="button"
          onClick={handleProvision}
          disabled={provisioning}
          className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {provisioning ? "Provisioning..." : `Provision ${family} kit`}
        </button>
      </div>

      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {state === "loading" && <p className="text-sm text-gray-500">Loading devices...</p>}

      {state === "loaded" && devices.length === 0 && (
        <p className="text-sm text-gray-500">
          No {family} devices yet. Provision a kit above.
        </p>
      )}

      {state === "loaded" && devices.length > 0 && (
        <ul className="space-y-2">
          {devices.map((device) => (
            <li
              key={device.id}
              className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-900">{device.display_name}</span>
                <span className="flex gap-1">
                  <span className="rounded bg-gray-200 px-1.5 py-0.5 text-xs text-gray-700">
                    {device.role}
                  </span>
                  <span className="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700">
                    {device.device_family}
                  </span>
                </span>
              </div>
              <p className="mt-1 text-xs text-gray-500">
                {Object.entries(device.default_config)
                  .map(([key, value]) => `${key}: ${value}`)
                  .join(" · ")}
              </p>
              <select
                value={device.zone_id ?? ""}
                onChange={(e) => handleAssign(device.id, e.target.value || null)}
                disabled={assigningId === device.id}
                className="mt-2 w-full rounded-md border border-gray-300 bg-white px-2 py-1 text-xs"
              >
                <option value="">Unassigned</option>
                {configs.map((config) => (
                  <optgroup key={config.location.id} label={config.location.name}>
                    {config.zones.map((zone) => (
                      <option key={zone.id} value={zone.id}>
                        {config.location.name} {"\u2014"} {zone.name}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
              {configs.length === 0 && (
                <p className="mt-1 text-xs text-gray-400">
                  Create a location in Configuration to assign zones.
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}