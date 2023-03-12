import pymongo
import logging
from dotenv import dotenv_values

from constants.error_message import ErrorMessage


class DBconnect:
    def __init__(self, collection):
        self.collection = collection
        self.logger = logging.getLogger(__name__)
        self.config = dotenv_values(".env")

    def connect(self):

        try:
            client = pymongo.MongoClient(
                "mongodb://{user}:{password}@{host}:{port}".format(user=self.config["DB_USERNAME"],
                                                                   password=self.config["DB_PASSWORD"],
                                                                   host=self.config["DB_HOST"], port=self.config["DB_PORT"])) 

            # client = pymongo.MongoClient(host=self.config["DB_HOST"], port=int(self.config["DB_PORT"]), connect=True)
        except Exception as error:
            self.logger.error(ErrorMessage.DB_CONNECTION)
            self.logger.error(error)
            raise Exception
        try:
            database = client[self.config["DB_NAME"]]
            collection = database[self.collection]
        except Exception as error:
            self.logger.error(ErrorMessage.DB_CONNECTION)
            self.logger.error(error)
            raise Exception

        return collection
