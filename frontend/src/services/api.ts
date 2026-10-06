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
export interface ZoneCreateInput {
  name: string;
  moisture_threshold_low: number;
  moisture_threshold_high: number;
  schedule?: Record<string, unknown>;
}

export interface ZoneDto {
  id: string;
  location_id: string;
  name: string;
  moisture_threshold_low: number;
  moisture_threshold_high: number;
  schedule: Record<string, unknown>;
}

export interface LocationSummaryDto {
  id: string;
  name: string;
}

export interface LocationConfigDto {
  location: LocationSummaryDto;
  zones: ZoneDto[];
}

export async function createLocationConfig(
  locationName: string,
  zones: ZoneCreateInput[],
): Promise<LocationConfigDto> {
  const response = await fetch(`${API_BASE_URL}/api/locations/config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ location_name: locationName, zones }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Failed to create location config: ${response.status}`);
  }
  return (await response.json()) as LocationConfigDto;
}

export async function fetchLocationConfig(locationId: string): Promise<LocationConfigDto> {
  const response = await fetch(`${API_BASE_URL}/api/locations/${locationId}/config`);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Failed to load location config: ${response.status}`);
  }
  return (await response.json()) as LocationConfigDto;
}

export interface ReadingDto {
  device_id: string;
  value: number;
  unit: string;
  source: "simulation" | "mqtt" | "vendor" | string;
  recorded_at: string;
}

export interface SamplingDto {
  sampling_interval_seconds: number;
  tracking_enabled: boolean;
}

async function getErrorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  const body = await response.json().catch(() => ({}));
  return body.detail ?? `${fallback}: ${response.status}`;
}

export async function readSensor(sensorId: string): Promise<ReadingDto> {
  const response = await fetch(`${API_BASE_URL}/api/sensors/${sensorId}/read`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(await getErrorMessage(response, "Failed to read sensor"));
  }

  return (await response.json()) as ReadingDto;
}

export async function fetchSensorReadings(
  sensorId: string,
  limit = 1,
): Promise<ReadingDto[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/sensors/${sensorId}/readings?limit=${limit}`,
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, "Failed to load sensor readings"),
    );
  }

  return (await response.json()) as ReadingDto[];
}

export async function fetchSampling(
  deviceId: string,
): Promise<SamplingDto> {
  const response = await fetch(
    `${API_BASE_URL}/api/devices/${deviceId}/sampling`,
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, "Failed to load sampling settings"),
    );
  }

  return (await response.json()) as SamplingDto;
}

export async function updateSampling(
  deviceId: string,
  settings: SamplingDto,
): Promise<SamplingDto> {
  const response = await fetch(
    `${API_BASE_URL}/api/devices/${deviceId}/sampling`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(settings),
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response, "Failed to update sampling settings"),
    );
  }

  return (await response.json()) as SamplingDto;
}