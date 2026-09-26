export interface HealthResponse {
  status: string;
  db: "ok" | "fail";
}

export interface SensorDto {
  id: string;
  device_type: string;
  display_name: string;
  default_config: Record<string, unknown>;
}

export type SensorType = "moisture" | "light";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }
  return (await response.json()) as HealthResponse;
}

export async function fetchSensors(): Promise<SensorDto[]> {
  const response = await fetch(`${API_BASE_URL}/api/sensors`);
  if (!response.ok) {
    throw new Error(`Failed to load sensors: ${response.status}`);
  }
  return (await response.json()) as SensorDto[];
}

export async function createSensor(
  type: SensorType,
  displayName?: string,
): Promise<SensorDto> {
  const response = await fetch(`${API_BASE_URL}/api/sensors`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type, display_name: displayName ?? null }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Failed to create sensor: ${response.status}`);
  }
  return (await response.json()) as SensorDto;
}
export interface DeviceDto {
  id: string;
  device_type: string;
  role: "sensor" | "actuator";
  device_family: string;
  display_name: string;
  default_config: Record<string, unknown>;
}

export type DeviceFamily = "simulation" | "edge";

export async function fetchDevices(params: {
  family?: string;
  role?: string;
} = {}): Promise<DeviceDto[]> {
  const query = new URLSearchParams();
  if (params.family) query.set("family", params.family);
  if (params.role) query.set("role", params.role);
  const queryString = query.toString();
  const url = `${API_BASE_URL}/api/devices${queryString ? `?${queryString}` : ""}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load devices: ${response.status}`);
  }
  return (await response.json()) as DeviceDto[];
}

export async function provisionDeviceFamily(family: DeviceFamily): Promise<DeviceDto[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/devices/provision?family=${family}`,
    { method: "POST" },
  );
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Failed to provision ${family}: ${response.status}`);
  }
  return (await response.json()) as DeviceDto[];
}