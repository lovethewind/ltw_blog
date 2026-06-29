import io
import json
from json import JSONDecodeError

import aiohttp
from PIL import Image, ImageOps

from apps.base.core.depend_inject import Component, RefreshScope, Autowired, Value, logger
from apps.base.enum.oss import DirType
from apps.base.utils.oss_util import OssUtil


@Component()
@RefreshScope(["app.web.random-img-url-api-list", "app.web.random-avatar-url-api-list"])
class PictureUtil:
    """
    从指定网址获取随机图片并保存，返回url
    """

    oss_util: OssUtil = Autowired()
    random_img_url_api_list: list[str] = Value("app.web.random-img-url-api-list")
    random_avatar_url_api_list: list[str] = Value("app.web.random-avatar-url-api-list")

    async def get_random_img_url(self, avatar=False):
        if avatar:
            return await self._get_random_img_url("avatar", "头像", dir_type=DirType.AVATAR)
        return await self._get_random_img_url("imgurl", "图片")

    async def get_random_avatar_url(self) -> str | None:
        """
        获取随机头像，压缩为 WebP 后上传到 OSS。

        :return: 压缩头像地址，获取失败时返回 None。
        """
        async with aiohttp.ClientSession() as session:
            for url in self.random_avatar_url_api_list:
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        body = await response.read()
                        location = response.headers.get("Location")
                    if not body:
                        if self._is_img_url(location):
                            return await self._upload_remote_avatar(session, location)
                        logger.warning(f"{url}头像地址无法使用，请确认")
                        continue
                    try:
                        json_data: dict = json.loads(body)
                        avatar_url = json_data.get("avatar")
                        if avatar_url:
                            return await self._upload_remote_avatar(session, avatar_url)
                    except JSONDecodeError, UnicodeDecodeError:
                        avatar_url = await self._upload_avatar_image(body)
                        if avatar_url:
                            return avatar_url
                except Exception as e:
                    logger.exception(f"{url}随机头像获取失败: {e}")
            return None

    async def get_random_cover_urls(self) -> tuple[str | None, str | None]:
        """
        获取随机文章封面，并尽量同步生成缩略图。

        :return: 原图地址和缩略图地址，缩略图生成失败时回退为原图地址。
        """
        min_length = 10000
        async with aiohttp.ClientSession() as session:
            for url in self.random_img_url_api_list:
                response = await session.get(url)
                body = await response.content.read()
                if not body or len(body) < min_length:
                    location = response.headers.get("Location")
                    if self._is_img_url(location):
                        return await self._upload_remote_image_with_thumb(session, location)
                    logger.warning(f"{url}图片地址无法使用，请确认")
                    continue
                try:
                    json_data: dict = json.loads(body)
                    img_url = json_data.get("imgurl")
                    if img_url:
                        return await self._upload_remote_image_with_thumb(session, img_url)
                except JSONDecodeError, UnicodeDecodeError:
                    return await self._upload_image_with_thumb(body, self._random_image_name())
            return None, None

    async def _get_random_img_url(self, key: str, description: str, dir_type=DirType.IMAGE):
        """
        获取图片
        """
        min_length = 10000
        async with aiohttp.ClientSession() as session:
            for url in self.random_img_url_api_list:
                response = await session.get(url)
                body = await response.content.read()
                if not body or len(body) < min_length:
                    if self.is_img_url(response.headers.get("Location")):
                        return response.headers.get("Location")
                    logger.warning(f"{url}{description}地址无法使用，请确认")
                    continue
                try:
                    json_data: dict = json.loads(body)
                    return json_data.get(key)
                except (JSONDecodeError, UnicodeDecodeError) as e:
                    # 返回的是图片二进制流，上传到oss
                    return await self.oss_util.upload_file(body, self._random_image_name(), dir_type=dir_type)
            return None

    async def _upload_remote_image_with_thumb(
        self, session: aiohttp.ClientSession, url: str
    ) -> tuple[str | None, str | None]:
        """
        下载远程图片并上传原图和缩略图。

        :param session: aiohttp 会话。
        :param url: 远程图片地址。
        :return: 原图地址和缩略图地址，失败时回退为远程原图地址。
        """
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    logger.warning(f"{url}图片下载失败，状态码: {response.status}")
                    return url, url
                body = await response.read()
            file_name = self._get_image_name_from_url(url)
            return await self._upload_image_with_thumb(body, file_name)
        except Exception as e:
            logger.exception(f"{url}图片下载或上传失败: {e}")
            return url, url

    async def _upload_remote_avatar(self, session: aiohttp.ClientSession, url: str) -> str | None:
        """
        下载远程头像并上传压缩版本。

        :param session: aiohttp 会话。
        :param url: 远程头像地址。
        :return: 压缩头像地址，处理失败时回退为远程地址。
        """
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    logger.warning(f"{url}头像下载失败，状态码: {response.status}")
                    return url
                body = await response.read()
            return await self._upload_avatar_image(body) or url
        except Exception as e:
            logger.exception(f"{url}头像下载或上传失败: {e}")
            return url

    async def _upload_avatar_image(self, body: bytes) -> str | None:
        """
        将头像压缩为最大 320px 的 WebP 并上传。

        :param body: 原始头像二进制内容。
        :return: 压缩头像地址，处理失败时返回 None。
        """
        try:
            avatar_body = self._build_thumbnail(body, max_width=320, quality=82)
            return await self.oss_util.upload_file(avatar_body, "avatar.webp", dir_type=DirType.AVATAR)
        except Exception as e:
            logger.exception(f"生成或上传压缩头像失败: {e}")
            return None

    async def _upload_image_with_thumb(self, body: bytes, file_name: str) -> tuple[str | None, str | None]:
        """
        上传图片原图，并为其生成 WebP 缩略图。

        :param body: 原图二进制内容。
        :param file_name: 原图文件名。
        :return: 原图地址和缩略图地址，缩略图失败时回退为原图地址。
        """
        cover_url = await self.oss_util.upload_file(body, file_name, dir_type=DirType.COVER)
        if not cover_url:
            return None, None
        try:
            thumb_body = self._build_thumbnail(body)
            thumb_url = await self.oss_util.upload_file(
                thumb_body, self._get_thumb_name(file_name), dir_type=DirType.THUMB
            )
            return cover_url, thumb_url or cover_url
        except Exception as e:
            logger.exception(f"生成或上传缩略图失败: {e}")
            return cover_url, cover_url

    def _build_thumbnail(self, body: bytes, max_width: int = 640, quality: int = 82) -> bytes:
        """
        生成 WebP 缩略图。

        :param body: 原图二进制内容。
        :param max_width: 缩略图最大宽度。
        :param quality: WebP 图片质量。
        :return: 缩略图二进制内容。
        """
        with Image.open(io.BytesIO(body)) as image:
            image = ImageOps.exif_transpose(image)
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGB")
            image.thumbnail((max_width, max_width * 10))
            output = io.BytesIO()
            image.save(output, format="WEBP", quality=quality, method=6)
            return output.getvalue()

    def _get_image_name_from_url(self, url: str) -> str:
        """
        从图片地址中提取文件名。

        :param url: 图片地址。
        :return: 图片文件名。
        """
        name = url.rsplit("/", 1)[-1].split("?", 1)[0]
        return name or self._random_image_name()

    def _get_thumb_name(self, file_name: str) -> str:
        """
        根据原图文件名生成缩略图文件名。

        :param file_name: 原图文件名。
        :return: 缩略图文件名。
        """
        name = file_name.rsplit("/", 1)[-1].split("?", 1)[0] or "image"
        stem = name.rsplit(".", 1)[0]
        return f"{stem}.webp"

    def _is_img_url(self, url: str | None) -> bool:
        """
        判断地址是否是常见图片地址。

        :param url: 待判断地址。
        :return: 是图片地址时返回 True。
        """
        if not url:
            return False
        return self.is_img_url(url)

    def is_img_url(self, url: str):
        return (
            url.endswith(".jpg")
            or url.endswith(".png")
            or url.endswith(".jpeg")
            or url.endswith(".gif")
            or url.endswith(".bmp")
            or url.endswith(".webp")
        )

    def _random_image_name(self):
        return f"r.jpg"
