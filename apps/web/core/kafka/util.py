# @Time    : 2024/10/18 14:43
# @Author  : frank
# @File    : util.py
import asyncio
import json
from typing import Any, Coroutine

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from dependency_injector.providers import Callable
from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

from apps.base.core.depend_inject import Autowired, Component, Value, logger
from apps.base.models.notice import Notice
from apps.base.utils.email_util import EmailUtil
from apps.base.utils.sms_util import SmsUtil
from apps.web.core.kafka.config import KafkaConfig
from apps.web.dto.notice_dto import NoticeSaveDTO


@Component()
class KafkaUtil:
    bootstrap_servers: str = Value("kafka.bootstrap_servers")
    email_util: EmailUtil = Autowired()
    sms_util: SmsUtil = Autowired()

    def __init__(self) -> None:
        """
        初始化 Kafka 工具类。

        :return: None
        """
        self.client = KafkaAdminClient(bootstrap_servers=self.bootstrap_servers)
        self._create_topics()
        self.producer_started = False
        self.producer: AIOKafkaProducer | None = None
        self._consumer_dict: dict[str, AIOKafkaConsumer] = {}
        self._consumer_task_list: list[asyncio.Task] = []

    def __del__(self) -> None:
        """
        释放 Kafka 客户端资源。

        :return: None
        """
        client = getattr(self, "client", None)
        if client:
            client.close()

    def _create_topics(self):
        try:
            self.client.create_topics(
                [
                    NewTopic(KafkaConfig.SEND_MAIL_TOPIC, num_partitions=1, replication_factor=1),
                    NewTopic(KafkaConfig.SEND_SMS_TOPIC, num_partitions=1, replication_factor=1),
                    NewTopic(KafkaConfig.SEND_NOTICE_TOPIC, num_partitions=1, replication_factor=1),
                ]
            )
        except TopicAlreadyExistsError:
            pass

    async def _init_consumer(self, key: str, topic: str, group_id: str) -> AIOKafkaConsumer:
        """
        初始化 Kafka 消费者。

        :param key: 消费者缓存键
        :param topic: Kafka topic
        :param group_id: Kafka 消费组
        :return: Kafka 消费者实例
        """
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id=group_id,
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        )
        try:
            await consumer.start()
        except BaseException:
            await consumer.stop()
            raise
        self._consumer_dict[key] = consumer
        return consumer

    async def send_message(self, topic: str, message: Any) -> None:
        """
        发送 Kafka 消息。

        :param topic: Kafka topic
        :param message: 消息内容
        :return: None
        """
        if not self.producer:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers, value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
        if not self.producer_started:
            await self.producer.start()
            self.producer_started = True
        await self.producer.send(topic, message)

    async def _consume_messages(self, topic: str, group_id: str, callback: Callable[Coroutine]) -> None:
        """
        持续消费指定 topic 的消息。

        :param topic: Kafka topic
        :param group_id: Kafka 消费组
        :param callback: 消息处理回调函数
        :return: None
        """
        key = f"{topic}:{group_id}"
        consumer = self._consumer_dict.get(key)
        if not consumer:
            consumer = await self._init_consumer(key, topic, group_id)
        try:
            async for message in consumer:
                logger.info(f"======consume_messages: {message.value}======")
                asyncio.create_task(callback(message.value))
        finally:
            consumer = self._consumer_dict.pop(key, None)
            if consumer:
                await consumer.stop()

    async def start_consumer(self) -> None:
        """
        启动 Kafka 消费者任务。

        :return: None
        """
        if self._consumer_task_list:
            return
        logger.info(f"========kafka: start_consumer...========")
        loop = asyncio.get_running_loop()
        await self._init_consumer(
            f"{KafkaConfig.SEND_MAIL_TOPIC}:{KafkaConfig.SEND_MAIL_GROUP}",
            KafkaConfig.SEND_MAIL_TOPIC,
            KafkaConfig.SEND_MAIL_GROUP,
        )
        await self._init_consumer(
            f"{KafkaConfig.SEND_SMS_TOPIC}:{KafkaConfig.SEND_SMS_GROUP}",
            KafkaConfig.SEND_SMS_TOPIC,
            KafkaConfig.SEND_SMS_GROUP,
        )
        await self._init_consumer(
            f"{KafkaConfig.SEND_NOTICE_TOPIC}:{KafkaConfig.SEND_NOTICE_GROUP}",
            KafkaConfig.SEND_NOTICE_TOPIC,
            KafkaConfig.SEND_NOTICE_GROUP,
        )
        self._consumer_task_list.extend(
            [
                loop.create_task(
                    self._consume_messages(
                        KafkaConfig.SEND_MAIL_TOPIC, KafkaConfig.SEND_MAIL_GROUP, self.email_util.send_email
                    )
                ),
                loop.create_task(
                    self._consume_messages(
                        KafkaConfig.SEND_SMS_TOPIC, KafkaConfig.SEND_SMS_GROUP, self.sms_util.send_sms
                    )
                ),
                loop.create_task(
                    self._consume_messages(
                        KafkaConfig.SEND_NOTICE_TOPIC, KafkaConfig.SEND_NOTICE_GROUP, AsyncTask.send_notice
                    )
                ),
            ]
        )

    async def stop(self) -> None:
        """
        停止 Kafka 消费者和生产者。

        :return: None
        """
        for task in self._consumer_task_list:
            task.cancel()
        if self._consumer_task_list:
            await asyncio.gather(*self._consumer_task_list, return_exceptions=True)
            self._consumer_task_list.clear()
        for consumer in list(self._consumer_dict.values()):
            await consumer.stop()
        self._consumer_dict.clear()
        if self.producer:
            await self.producer.stop()
            self.producer = None
            self.producer_started = False
        self.client.close()

    async def send_email(self, to: str, subject: str, content: Any):
        await self.send_message(KafkaConfig.SEND_MAIL_TOPIC, {"to": to, "subject": subject, "content": content})

    async def send_sms(self, mobile: str, sms_type: str, code: str):
        await self.send_message(KafkaConfig.SEND_SMS_TOPIC, {"mobile": mobile, "sms_type": sms_type, "code": code})

    async def send_notice(self, notice_dto: NoticeSaveDTO):
        await self.send_message("send_notice", notice_dto.model_dump(exclude_none=True))


class AsyncTask:

    @classmethod
    async def send_notice(cls, message: dict[str, Any]):
        await Notice.create(**message)
