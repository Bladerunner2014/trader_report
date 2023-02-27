from confluent_kafka import Producer, Consumer, KafkaError
from dotenv import dotenv_values
import logging

from constants.error_message import ErrorMessage
from constants.info_message import InfoMessage


class Broker:
    def __init__(self, topic):
        self.config = dotenv_values(".env")
        self.logger = logging.getLogger(__name__)
        self._config_kafka = {'bootstrap.servers': self.config["KAFKA_BOOTSTRAP_SERVERS"]}
        self.producer = Producer(self._config_kafka)
        self.consumer = Consumer(self._config_kafka)
        self.topic = topic

    def delivery_report(self, err, msg):
        if err is not None:
            self.logger.error(ErrorMessage.KAFKA_PRODUCE)
            self.logger.error(err)
        else:
            self.logger.error(InfoMessage.KAFKA_PRODUCE)
            self.logger.error(msg.topic() + " " + msg.partition())

    def produce_msg(self, data):
        self.producer.poll(timeout=0)
        self.producer.produce(self.topic, data.encode('utf-8'), callback=self.delivery_report)
        self.producer.flush()

    def consume_msg(self):
        self.consumer.subscribe(self.topic)
        while True:
            msg = self.consumer.poll(timeout=1.0)
            if msg is None: continue
            if msg.error():
                if msg.error().code() == KafkaError.PARTITION_EOF:
                    self.logger.error(ErrorMessage.KAFKA_CONSUME)
                    self.logger.error('%% %s [%d] reached end at offset %d\n' %
                                     (msg.topic(), msg.partition(), msg.offset()))
                elif msg.error():
                    continue
            else:
                return msg
