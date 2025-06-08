import asyncio
import time
from core.userRepository import UserRepository
from enums.languages import Language
from enums.roles import Roles
from models.user import User
from zonelogger import logger, LogZone
from enums.apiIDs import ApiId
from core.userCache import UserCache

class UserManager:
    def __init__(self, user_repository: UserRepository, cache_size, save_interval: float = 5.0):
        self._user_repository = user_repository
        self._users = UserCache(cache_size)
        self._save_interval = save_interval
        self._sync_queue: dict[User, float] = {}
        self._sync_loop_task: asyncio.Task | None = None
        self._running = False

    async def getUserOrCreate(self, api: ApiId, ID) -> User:
        user = await self.getUser(api, ID)
        if user is None:
            logger.debug(LogZone.USERS, f"{api} {ID} user was not find")
            user = await self._user_repository.createUser(api, ID)
            self._users[(api, ID)] = user
        return user

    async def getUser(self, api: ApiId, ID) -> User | None:
        user = self._users.get((api,ID))
        if user:
            logger.debug(LogZone.USERS, f"{api} {ID} user was in cache")
            return user
        user = await self._user_repository.getUserDB(api,ID)
        if user:
            logger.debug(LogZone.USERS, f"{api} {ID} user was in DB")
            self._users[(api, ID)] = user
            return user
        return None

    async def setRoles(self, api:ApiId, ID, roles: Roles):
        if roles is None:
            return
        if roles == 0:
            logger.warning(LogZone.USERS, f"set no roles for {api}:{ID} user")
        user = await self.getUserOrCreate(api, ID)
        user._data["roles"] = roles
        user._setDirty("data", "roles")
        user.dirty_force = True
        role = user.role
        if roles != 0:
            if not (roles & role):
                user.role = roles & -roles
                user.stackClear()
        await self._user_repository.saveUserDirty(user)

    def remove_user_from_cache(self, key: tuple):
        del self._users[key]

    def clear_user_cache(self):
        self._users.clear()

    def dump_user_cache(self) -> dict:
        return dict(self._users._cache)


    async def trySaveUserDirty(self, user: User):
        if user.dirty_force:
            if user.is_dirty():
                await self._user_repository.saveUserDirty(user)
            user.clear_dirty()
            user.dirty_force = False
        else:
            self._sync_queue[user] = time.monotonic()

    def run_sync_loop(self):
        if not self._running:
            self._running = True
            self._sync_loop_task = asyncio.create_task(self._sync_loop())

    async def _sync_loop(self):
        try:
            while self._running:
                now = time.monotonic()
                to_remove = []

                for user, ts in self._sync_queue.items():
                    if now - ts >= self._save_interval:
                        if user.is_dirty():
                            await self._user_repository.saveUserDirty(user)
                        user.clear_dirty()
                        to_remove.append(user)

                for user in to_remove:
                    self._sync_queue.pop(user, None)

                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            pass

    async def stop_sync_loop(self):
        self._running = False
        if self._sync_loop_task:
            self._sync_loop_task.cancel()
            try:
                await self._sync_loop_task
            except asyncio.CancelledError:
                pass