import redis
import logging
from dotenv import dotenv_values

from constants.error_message import ErrorMessage


class CacheManager:
    def __init__(self, key_prefix):
        self.logger = logging.getLogger(__name__)
        self.config = dotenv_values(".env")
        self.key_prefix = key_prefix
        self.cache = None
        self.connect()

    def __call__(self, *args, **kwargs):
        return self.cache

    def connect(self):
        try:
            pool = redis.ConnectionPool(host=self.config["REDIS_HOST"], port=self.config["REDIS_PORT"],
                                        db=self.config["REDIS_DB"])
            self.cache = redis.Redis(connection_pool=pool)

        except Exception as error:
            self.logger.error(ErrorMessage.REDIS_CONNECTION)
            self.logger.error(error)
            raise Exception

    def get(self, key):
        try:
            value = self.cache.get(self.key_prefix + key)
        except Exception as error:
            self.logger.error(ErrorMessage.REDIS_GET)
            self.logger.error(error)
            raise Exception
        return str(value)

    def set(self, key, value, ttl):
        try:
            return self.cache.set(self.key_prefix + key, value, ex=ttl)
        except Exception as error:
            self.logger.error(ErrorMessage.REDIS_SET)
            self.logger.error(error)
            raise Exception


