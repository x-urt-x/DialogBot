from boundary.infra.apiRegistry import ApiRegistry
from zonelogger import logger
import asyncio

class ApiManager:
    def __init__(self, registry: ApiRegistry):
        self._registry = registry

    async def run_all(self):
        for api in self._registry.get_all_lifecycle():
            await api.run()

    async def loop(self):
        while True:
            try:
                await self._process_all()
                await asyncio.sleep(0.01)
            except Exception:
                logger.exception("error on ApiManager")

    async def _process_all(self):
        for api in self._registry.get_all_lifecycle():
            await api.process()

    async def stop_all(self):
        for api in self._registry.get_all_lifecycle():
            await api.stop()