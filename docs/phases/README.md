# Phase order

This project is built incrementally, one design pattern per phase.

- **Phase 1 — Skeleton**: three-tier project setup, no design pattern.
- **Phase 2 — Factory Method**: adds the `devices` table, sensor creators, and
  `/api/sensors`; fills in the Sensors dashboard section.
- **Phase 3 — Abstract Factory** (current state): adds `device_family` to the
  `devices` table, `DeviceFamilyFactory` (simulation/edge), and
  `/api/devices` + `/api/devices/provision`; fills in the Devices dashboard
  section.
- Later phases continue to add one pattern at a time on top of this
  foundation, without restructuring the repo.
  