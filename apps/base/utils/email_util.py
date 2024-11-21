# @Time    : 2024/10/18 15:17
# @Author  : frank
# @File    : email_util.py
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from apps.base.core.depend_inject import Component, Value, logger, RefreshScope


@Component()
@RefreshScope("mail")
class EmailUtil:
    hostname: str = Value("mail.host")
    port: int = Value("mail.port")
    username: str = Value("mail.username")
    password: str = Value("mail.password")
    from_: str = Value("mail.from")

    async def send_email(self, message: dict[str, str]):
        logger.info(f"======send email: {message}======")
        e_message = MIMEMultipart("alternative")
        e_message['Subject'] = message.get("subject")
        e_message['From'] = self.from_
        e_message['To'] = message.get("to")
        e_message.attach(MIMEText(message.get("content"), "html"))

        await aiosmtplib.send(
            e_message,
            hostname=self.hostname,
            port=self.port,
            username=self.username,
            password=self.password,
            start_tls=True,
        )
