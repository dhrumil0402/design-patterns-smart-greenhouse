import { useEffect, useState } from "react";
import {
  fetchDevices,
  provisionDeviceFamily,
  type DeviceDto,
  type DeviceFamily,
} from "../../services/api";
import DeviceFamilySwitcher from "./DeviceFamilySwitcher";

type LoadState = "loading" | "loaded" | "error";

export default function DeviceList() {
  const [family, setFamily] = useState<DeviceFamily>("simulation");
  const [devices, setDevices] = useState<DeviceDto[]>([]);
  const [state, setState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [provisioning, setProvisioning] = useState(false);

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

  useEffect(() => {
    loadDevices(family);
  }, [family]);

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
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}