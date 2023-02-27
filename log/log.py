import logging
from dotenv import dotenv_values

config = dotenv_values(".env")


def setup_logger():
    logging.root.handlers = []

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler(config["LOG_PATH"], 'a', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )





