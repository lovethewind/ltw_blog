import json
from json import JSONDecodeError

import aiohttp

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
                    return self.oss_util.upload_file(body, self._random_image_name(), dir_type=dir_type)

    def is_img_url(self, url: str):
        return url.endswith(".jpg") or url.endswith(".png") or url.endswith(".jpeg") or \
            url.endswith(".gif") or url.endswith(".bmp") or url.endswith(".webp")

    def _random_image_name(self):
        return f"r.jpg"
