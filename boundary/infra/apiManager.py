from boundary.infra.apiRegistry import ApiRegistry

class ApiManager:
    def __init__(self, registry: ApiRegistry):
        self._registry = registry

    async def run_all(self):
        for api in self._registry.get_all_lifecycle():
            await api.run()

    async def process_all(self):
        for api in self._registry.get_all_lifecycle():
            await api.process()

    async def stop_all(self):
        for api in self._registry.get_all_lifecycle():
            await api.stop()