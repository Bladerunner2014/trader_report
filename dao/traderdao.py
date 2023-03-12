import pymongo
import logging
import pymongo.errors

from db.db_connection import DBconnect
from constants.error_message import ErrorMessage


class TraderDao:

    def __init__(self, collection_name):
        self.db = DBconnect(collection_name).connect()
        self.logger = logging.getLogger(__name__)

    # def insert_one(self, query):
    #     try:
    #         return self.db.insert_one(query)
    #     except pymongo.errors as error:
    #         self.logger.error(ErrorMessage.DB_INSERT)
    #         self.logger.error(error)
    #         raise error

    def insert_many(self, collection_names: list):
        try:
            return self.db.insert_many(collection_names)
        except pymongo.errors as error:
            self.logger.error(ErrorMessage.DB_INSERT)
            self.logger.error(error)
            raise error

    def find_one(self, query):
        try:
            return self.db.find_one(query)
        except pymongo.errors as error:
            self.logger.error(ErrorMessage.DB_INSERT)
            self.logger.error(error)
            raise error

    def find(self, condition: dict):
        # try:
        return list(self.db.find(condition))
        # except pymongo.errors as error:
        #     self.logger.error(ErrorMessage.DB_SELECT)
        #     self.logger.error(error)
        #     raise error
