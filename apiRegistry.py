from api_ids import ApiId
from IApi import IApiSender, IApiLifecycle
from zonelogger import logger, LogZone

class ApiRegistry:
    def __init__(self):
        self._apis: dict[ApiId, object] = {}

    def register(self, api_id: ApiId, api: object):
        if not isinstance(api, IApiLifecycle) or not isinstance(api, IApiSender):
            logger.error(LogZone.API_PROCES, f"API {api_id} must implement both IApiLifecycle and IApiSender")
            raise TypeError
        self._apis[api_id] = api

    def get_sender(self, api_id: ApiId) -> IApiSender:
        api = self._apis.get(api_id)
        if not isinstance(api, IApiSender):
            logger.error(LogZone.API_PROCES, f"API {api_id} does not support sending")
            raise TypeError
        return api

    def get_all_lifecycle(self) -> list[IApiLifecycle]:
        return [api for api in self._apis.values() if isinstance(api, IApiLifecycle)]
