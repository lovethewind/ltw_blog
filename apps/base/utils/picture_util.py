import io
import json
from json import JSONDecodeError

import aiohttp
from PIL import Image, ImageOps

from apps.base.core.depend_inject import Autowired, Component, RefreshScope, Value, logger
from apps.base.enum.oss import DirType
from apps.base.utils.oss_util import OssUtil


@Component()
@RefreshScope(["app.web.random-img-url-api-list", "app.web.random-avatar-url-api-list"])
class PictureUtil:
    """获取随机头像或图片，并按需生成压缩图。"""

    oss_util: OssUtil = Autowired()
    random_img_url_api_list: list[str] = Value("app.web.random-img-url-api-list")
    random_avatar_url_api_list: list[str] = Value("app.web.random-avatar-url-api-list")

    async def get_random_avatar_url(self, with_thumb: bool = False, only_thumb: bool = False) -> str | tuple[str, str]:
        """
        获取随机头像地址。

        :param with_thumb: 是否同时返回原图和压缩图地址。
        :param only_thumb: 是否只返回压缩图地址。
        :return: 图片地址或原图、压缩图地址元组，获取失败时返回空值。
        :raises ValueError: with_thumb 和 only_thumb 同时为 True 时抛出。
        """
        self._validate_thumb_options(with_thumb, only_thumb)
        return await self._get_random_url(
            api_list=self.random_avatar_url_api_list,
            json_key="avatar",
            source_dir_type=DirType.AVATAR,
            thumb_dir_type=DirType.AVATAR,
            max_width=320,
            with_thumb=with_thumb,
            only_thumb=only_thumb,
        )

    async def get_random_img_url(self, with_thumb: bool = False, only_thumb: bool = False) -> str | tuple[str, str]:
        """
        获取随机普通图片地址。

        :param with_thumb: 是否同时返回原图和压缩图地址。
        :param only_thumb: 是否只返回压缩图地址。
        :return: 图片地址或原图、压缩图地址元组，获取失败时返回空值。
        :raises ValueError: with_thumb 和 only_thumb 同时为 True 时抛出。
        """
        self._validate_thumb_options(with_thumb, only_thumb)
        return await self._get_random_url(
            api_list=self.random_img_url_api_list,
            json_key="imgurl",
            source_dir_type=DirType.IMAGE,
            thumb_dir_type=DirType.THUMB,
            max_width=640,
            with_thumb=with_thumb,
            only_thumb=only_thumb,
        )

    async def _get_random_url(
        self,
        api_list: list[str],
        json_key: str,
        source_dir_type: DirType,
        thumb_dir_type: DirType,
        max_width: int,
        with_thumb: bool,
        only_thumb: bool,
    ) -> str | tuple[str, str]:
        """
        遍历随机图片接口并生成所需返回结果。

        :param api_list: 随机图片接口列表。
        :param json_key: JSON 响应中的图片地址字段。
        :param source_dir_type: 原图上传目录类型。
        :param thumb_dir_type: 压缩图上传目录类型。
        :param max_width: 压缩图最大宽度。
        :param with_thumb: 是否同时返回原图和压缩图地址。
        :param only_thumb: 是否只返回压缩图地址。
        :return: 图片地址或原图、压缩图地址元组。
        """
        async with aiohttp.ClientSession() as session:
            for api_url in api_list:
                try:
                    body, remote_url = await self._fetch_random_source(session, api_url, json_key)
                    if not body and not remote_url:
                        continue
                    return await self._prepare_result(
                        session=session,
                        body=body,
                        remote_url=remote_url,
                        source_dir_type=source_dir_type,
                        thumb_dir_type=thumb_dir_type,
                        max_width=max_width,
                        with_thumb=with_thumb,
                        only_thumb=only_thumb,
                    )
                except Exception as exc:
                    logger.exception(f"{api_url}随机图片获取失败: {exc}")
        return self._format_result("", "", with_thumb, only_thumb)

    async def _fetch_random_source(
        self, session: aiohttp.ClientSession, api_url: str, json_key: str
    ) -> tuple[bytes, str]:
        """
        从随机图片接口读取二进制图片或远程图片地址。

        :param session: aiohttp 会话。
        :param api_url: 随机图片接口地址。
        :param json_key: JSON 响应中的图片地址字段。
        :return: 图片二进制内容和远程图片地址，未获取到时返回空值。
        """
        async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status >= 400:
                logger.warning(f"{api_url}随机图片接口请求失败，状态码: {response.status}")
                return b"", ""
            body = await response.read()
            location = response.headers.get("Location") or ""

        if body:
            try:
                json_data = json.loads(body)
                remote_url = json_data.get(json_key, "") if isinstance(json_data, dict) else ""
                if isinstance(remote_url, str) and remote_url:
                    return b"", remote_url
            except JSONDecodeError, UnicodeDecodeError:
                return body, ""
        if self._is_img_url(location):
            return b"", location
        logger.warning(f"{api_url}随机图片地址无法使用，请确认")
        return b"", ""

    async def _prepare_result(
        self,
        session: aiohttp.ClientSession,
        body: bytes,
        remote_url: str,
        source_dir_type: DirType,
        thumb_dir_type: DirType,
        max_width: int,
        with_thumb: bool,
        only_thumb: bool,
    ) -> str | tuple[str, str]:
        """
        上传原图并按返回模式生成压缩图。

        :param session: aiohttp 会话。
        :param body: 图片二进制内容。
        :param remote_url: 远程原图地址。
        :param source_dir_type: 原图上传目录类型。
        :param thumb_dir_type: 压缩图上传目录类型。
        :param max_width: 压缩图最大宽度。
        :param with_thumb: 是否同时返回原图和压缩图地址。
        :param only_thumb: 是否只返回压缩图地址。
        :return: 图片地址或原图、压缩图地址元组。
        """
        if remote_url and not with_thumb and not only_thumb:
            return remote_url

        file_name = self._get_image_name_from_url(remote_url) if remote_url else self._random_image_name()
        if remote_url and not body:
            body = await self._download_image(session, remote_url)
            if not body:
                return self._format_result(remote_url, "", with_thumb, only_thumb)

        original_url = remote_url
        if not only_thumb:
            original_url = await self.oss_util.upload_file(body, file_name, dir_type=source_dir_type) or remote_url
            if not with_thumb:
                return original_url
            if not original_url:
                return "", ""

        try:
            thumb_body = self._build_thumbnail(body, max_width=max_width)
            thumb_url = await self.oss_util.upload_file(
                thumb_body, self._get_thumb_name(file_name), dir_type=thumb_dir_type
            )
        except Exception as exc:
            logger.exception(f"生成或上传压缩图失败: {exc}")
            thumb_url = ""
        if only_thumb and not thumb_url and not original_url:
            original_url = await self.oss_util.upload_file(body, file_name, dir_type=source_dir_type) or ""
        return self._format_result(original_url, thumb_url or "", with_thumb, only_thumb)

    async def _download_image(self, session: aiohttp.ClientSession, url: str) -> bytes:
        """
        下载远程图片。

        :param session: aiohttp 会话。
        :param url: 远程图片地址。
        :return: 图片二进制内容，下载失败时返回空字节。
        """
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    logger.warning(f"{url}图片下载失败，状态码: {response.status}")
                    return b""
                return await response.read()
        except Exception as exc:
            logger.exception(f"{url}图片下载失败: {exc}")
            return b""

    def _format_result(
        self, original_url: str, thumb_url: str, with_thumb: bool, only_thumb: bool
    ) -> str | tuple[str, str]:
        """
        按调用参数格式化图片地址。

        :param original_url: 原图地址。
        :param thumb_url: 压缩图地址。
        :param with_thumb: 是否同时返回原图和压缩图地址。
        :param only_thumb: 是否只返回压缩图地址。
        :return: 图片地址或原图、压缩图地址元组。
        """
        resolved_thumb_url = thumb_url or original_url
        if with_thumb:
            return original_url, resolved_thumb_url
        if only_thumb:
            return resolved_thumb_url
        return original_url

    def _validate_thumb_options(self, with_thumb: bool, only_thumb: bool) -> None:
        """
        校验压缩图返回参数。

        :param with_thumb: 是否同时返回原图和压缩图地址。
        :param only_thumb: 是否只返回压缩图地址。
        :return: None。
        :raises ValueError: 两个参数同时为 True 时抛出。
        """
        if with_thumb and only_thumb:
            raise ValueError("with_thumb 和 only_thumb 不能同时为 True")

    def _build_thumbnail(self, body: bytes, max_width: int, quality: int = 82) -> bytes:
        """
        生成 WebP 压缩图。

        :param body: 原始图片二进制内容。
        :param max_width: 压缩图最大宽度。
        :param quality: WebP 图片质量。
        :return: 压缩图二进制内容。
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
        根据原图文件名生成压缩图文件名。

        :param file_name: 原图文件名。
        :return: 压缩图文件名。
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
        path = url.split("?", 1)[0].lower()
        return path.endswith((".jpg", ".png", ".jpeg", ".gif", ".bmp", ".webp"))

    def _random_image_name(self) -> str:
        """
        返回随机图片上传时使用的基础文件名。

        :return: 图片文件名。
        """
        return "r.jpg"
