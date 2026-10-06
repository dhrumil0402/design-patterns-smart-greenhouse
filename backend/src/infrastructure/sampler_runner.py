from __future__ import annotations

import asyncio
import logging
from contextlib import contextmanager
from datetime import datetime, timezone

from application.readings.sampler import SimulationSampler
from application.readings.service import ReadingIngest
from infrastructure.adapters.selector import select_sensor_adapter
from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository

logger = logging.getLogger(__name__)
TICK_SECONDS = 1.0


@contextmanager
def _session():
    gen = get_db()
    db = next(gen)
    try:
        yield db
    finally:
        gen.close()


def run_tick() -> int:
    with _session() as db:
        devices = DeviceRepository(db)
        readings = ReadingRepository(db)
        ingest = ReadingIngest(devices, readings, select_sensor_adapter)
        sampler = SimulationSampler(devices, readings, ingest, select_sensor_adapter)
        return sampler.run_once(datetime.now(timezone.utc))


async def sampler_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(run_tick)
        except Exception:
            logger.exception("sampler tick failed")
        await asyncio.sleep(TICK_SECONDS)
