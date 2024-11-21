import logging
import time
import random
logger = logging.getLogger(__name__)


class Snowflake:
    def __init__(self, worker_id: int, data_center_id: int):
        """
        生成雪花算法ID
        1符号位+41位时间戳+5位数据中心id+5位机器id+12位序列号
        :param worker_id: 机器ID
        """
        logger.info(f"Snowflake config worker_id: {worker_id} data_center_id: {data_center_id}")
        # 机器标识ID
        self.worker_id = worker_id
        # 数据中心ID
        self.data_center_id = data_center_id
        self.sequence: int = 0
        self.last_timestamp: int = -1
        self.epoch = 1288834974657

    @staticmethod
    def _wait_next_millis(last_timestamp) -> int:
        timestamp = int(time.time() * 1000)
        while timestamp <= last_timestamp:
            timestamp = int(time.time() * 1000)
        return timestamp

    @property
    def generate_id(self) -> int:
        timestamp = int(time.time() * 1000)
        if timestamp < self.last_timestamp:
            raise Exception("Clock moved backwards")
        if timestamp == self.last_timestamp:
            self.sequence = (self.sequence + 1) & 4095
            if self.sequence == 0:
                timestamp = self._wait_next_millis(self.last_timestamp)
        else:
            self.sequence = 0
        self.last_timestamp = timestamp
        snow_id = ((timestamp - self.epoch) << 22) | (self.data_center_id << 17) | (self.worker_id << 12) | self.sequence
        logger.info(f"=====check snowflake id: {(timestamp, self.last_timestamp, self.sequence)} snow_id: {snow_id}")
        return snow_id


class SnowflakeIDGenerator:
    snowflake = Snowflake(random.randint(0, 31), random.randint(0, 31))

    @classmethod
    def generate_id(cls):
        return cls.snowflake.generate_id


if __name__ == "__main__":
    for i in range(1000):
        print(SnowflakeIDGenerator.generate_id())
