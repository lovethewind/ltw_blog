"""
为历史文章封面和图库图片生成缩略图。

默认 dry-run，仅输出待处理记录；传入 --execute 后才会下载原图、生成 WebP 缩略图、上传 OSS 并回写数据库。
"""

import argparse
import asyncio
import io
import sys
from pathlib import Path
from typing import Iterable

import aiohttp
from PIL import Image, ImageOps

PROJECT_PATH = Path(__file__).resolve().parents[3]
if str(PROJECT_PATH) not in sys.path:
    sys.path.append(str(PROJECT_PATH))

from apps.base.core.depend_inject import GetBean  # noqa: E402
from apps.base.core.tortoise import tortoise_context  # noqa: E402
from apps.base.enum.oss import DirType  # noqa: E402
from apps.base.models.article import Article  # noqa: E402
from apps.base.models.picture import Picture  # noqa: E402
from apps.base.models.source import Source  # noqa: E402
from apps.base.utils.oss_util import OssUtil  # noqa: E402


class ThumbnailTarget:
    """
    缩略图处理目标。

    :param name: 目标名称。
    :param model: Tortoise 模型类。
    :param source_field: 原图字段名。
    :param thumb_field: 缩略图字段名。
    """

    def __init__(self, name: str, model: type, source_field: str, thumb_field: str) -> None:
        self.name = name
        self.model = model
        self.source_field = source_field
        self.thumb_field = thumb_field


TARGETS = (
    ThumbnailTarget("文章封面", Article, "cover", "cover_thumb"),
    ThumbnailTarget("图库图片", Picture, "url", "thumb_url"),
)


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数。

    :return: 命令行参数命名空间。
    """
    parser = argparse.ArgumentParser(description="为历史图片生成缩略图")
    parser.add_argument("--execute", action="store_true", help="实际执行上传和数据库更新")
    parser.add_argument("--limit", type=int, default=0, help="最多处理多少条记录，0 表示不限制")
    parser.add_argument("--max-width", type=int, default=640, help="缩略图最大宽度")
    parser.add_argument("--quality", type=int, default=82, help="WebP 图片质量")
    return parser.parse_args()


def should_generate_thumb(source_url: str | None, thumb_url: str | None) -> bool:
    """
    判断是否需要生成缩略图。

    :param source_url: 原图地址。
    :param thumb_url: 缩略图地址。
    :return: 需要生成时返回 True。
    """
    return bool(source_url) and (not thumb_url or thumb_url == source_url)


def iter_targets(names: set[str] | None = None) -> Iterable[ThumbnailTarget]:
    """
    迭代待处理目标。

    :param names: 指定目标名称集合。
    :return: 目标迭代器。
    """
    for target in TARGETS:
        if names and target.name not in names:
            continue
        yield target


def resolve_image_url(url: str, oss_util: OssUtil) -> str:
    """
    将图片地址转换为可下载的完整 URL。

    :param url: 数据库存储的图片地址。
    :param oss_util: OSS 工具实例。
    :return: 可下载图片地址。
    """
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return f"{oss_util.get_cname()}/{url.lstrip('/')}"


def make_thumb_name(source_url: str) -> str:
    """
    生成缩略图文件名。

    :param source_url: 原图地址。
    :return: 缩略图文件名。
    """
    name = source_url.rsplit("/", 1)[-1].split("?", 1)[0] or "image"
    stem = name.rsplit(".", 1)[0]
    return f"{stem}_thumb.webp"


def build_thumbnail(image_bytes: bytes, max_width: int, quality: int) -> bytes:
    """
    生成 WebP 缩略图。

    :param image_bytes: 原图字节。
    :param max_width: 缩略图最大宽度。
    :param quality: WebP 图片质量。
    :return: WebP 缩略图字节。
    """
    with Image.open(io.BytesIO(image_bytes)) as image:
        image = ImageOps.exif_transpose(image)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
        image.thumbnail((max_width, max_width * 10))
        output = io.BytesIO()
        image.save(output, format="WEBP", quality=quality, method=6)
        return output.getvalue()


async def download_image(session: aiohttp.ClientSession, url: str) -> bytes:
    """
    下载原图。

    :param session: aiohttp 会话。
    :param url: 原图完整地址。
    :return: 原图字节。
    :raises RuntimeError: 下载失败时抛出。
    """
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
        if response.status != 200:
            raise RuntimeError(f"下载失败: HTTP {response.status}")
        return await response.read()


async def process_record(
        record: object,
        target: ThumbnailTarget,
        session: aiohttp.ClientSession,
        oss_util: OssUtil,
        max_width: int,
        quality: int,
        execute: bool,
) -> bool:
    """
    处理单条记录。

    :param record: 数据库记录。
    :param target: 缩略图目标配置。
    :param session: aiohttp 会话。
    :param oss_util: OSS 工具实例。
    :param max_width: 缩略图最大宽度。
    :param quality: WebP 图片质量。
    :param execute: 是否实际执行。
    :return: 处理成功或 dry-run 命中时返回 True。
    """
    source_url = getattr(record, target.source_field)
    thumb_url = getattr(record, target.thumb_field)
    if not should_generate_thumb(source_url, thumb_url):
        return False

    label = f"{target.name}#{record.id}"
    if not execute:
        print(f"[DRY-RUN] {label}: {source_url}")
        return True

    download_url = resolve_image_url(source_url, oss_util)
    image_bytes = await download_image(session, download_url)
    thumb_bytes = build_thumbnail(image_bytes, max_width, quality)
    thumb_url = await oss_util.upload_file(thumb_bytes, make_thumb_name(source_url), dir_type=DirType.THUMB)
    if not thumb_url:
        raise RuntimeError("上传缩略图失败")

    setattr(record, target.thumb_field, thumb_url)
    await record.save(update_fields=[target.thumb_field])
    await Source.get_or_create(user_id=record.user_id, url=thumb_url)
    print(f"[OK] {label}: {thumb_url}")
    return True


async def process_target(
        target: ThumbnailTarget,
        session: aiohttp.ClientSession,
        oss_util: OssUtil,
        max_width: int,
        quality: int,
        execute: bool,
        limit: int,
) -> int:
    """
    处理一类历史图片记录。

    :param target: 缩略图目标配置。
    :param session: aiohttp 会话。
    :param oss_util: OSS 工具实例。
    :param max_width: 缩略图最大宽度。
    :param quality: WebP 图片质量。
    :param execute: 是否实际执行。
    :param limit: 最大处理条数。
    :return: 命中或处理的记录数量。
    """
    handled = 0
    records = await target.model.all()
    for record in records:
        if limit and handled >= limit:
            break
        try:
            if await process_record(record, target, session, oss_util, max_width, quality, execute):
                handled += 1
        except Exception as exc:
            print(f"[ERROR] {target.name}#{record.id}: {exc}")
    return handled


async def main() -> None:
    """
    执行历史缩略图生成任务。

    :return: None。
    """
    args = parse_args()
    async with tortoise_context():
        oss_util = GetBean(OssUtil)
        total = 0
        async with aiohttp.ClientSession() as session:
            for target in iter_targets():
                count = await process_target(
                    target,
                    session,
                    oss_util,
                    args.max_width,
                    args.quality,
                    args.execute,
                    args.limit,
                )
                total += count
                print(f"{target.name}: {count}")
        print(f"合计: {total}")
        if not args.execute:
            print("当前为 dry-run，传入 --execute 才会上传缩略图并更新数据库。")


if __name__ == "__main__":
    asyncio.run(main())
