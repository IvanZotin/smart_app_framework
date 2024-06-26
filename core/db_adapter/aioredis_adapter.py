import copy
import importlib
from typing import Optional

from core.db_adapter import error
from core.db_adapter.db_adapter import AsyncDBAdapter
from core.logging.logger_utils import log
from core.monitoring.monitoring import monitoring


class AIORedisAdapter(AsyncDBAdapter):
    def __init__(self, config=None):
        super().__init__(config)
        self.aioredis = importlib.import_module("redis", "asyncio")
        redis_type = self.aioredis.Redis
        self._redis: Optional[redis_type] = None

        try:
            del self.config["type"]
        except KeyError:
            pass

    @monitoring.got_histogram("save_time")
    async def save(self, id, data):
        return await self._async_run(self._save, id, data)

    @monitoring.got_histogram("save_time")
    async def replace_if_equals(self, id, sample, data):
        return await self._async_run(self._replace_if_equals, id, sample, data)

    @monitoring.got_histogram("get_time")
    async def get(self, id):
        return await self._async_run(self._get, id)

    async def path_exists(self, path):
        return await self._async_run(self._path_exists, path)

    async def connect(self):
        print("Here is the content of REDIS_CONFIG:", self.config)
        print("Connecting to a single redis server")
        config = copy.deepcopy(self.config)
        redis_url = config.pop("redis", None)
        if not isinstance(redis_url, str):
            raise ValueError(
                "redis should be specified like redis://[[username]:[password]]@localhost:6379/0")
        self._redis = self.aioredis.from_url(redis_url, **config)

    def _open(self, filename, *args, **kwargs):
        pass

    async def _save(self, id, data):
        return await self._redis.set(id, data)

    async def _replace_if_equals(self, id, sample, data):
        log("no replace_if_equals method. running save instead", level="WARNING")
        await self.save(id, data)

    async def _get(self, id):
        data = await self._redis.get(id)
        return data

    async def _list_dir(self, path):
        raise error.NotSupportedOperation

    async def _glob(self, path, pattern):
        raise error.NotSupportedOperation

    async def _path_exists(self, path):
        return await self._redis.exists(path)

    async def _on_prepare(self):
        pass

    async def is_alive(self) -> Optional[bool]:
        try:
            return self._redis.ping()
        except Exception:
            log("AIORedisAdapter is not alive", level="INFO")
