import json
from typing import Any

import aiohttp
from sqlalchemy import func, select

from apps.base.constant.email_constant import EmailConstant
from apps.base.constant.sms_constant import SmsConstant
from apps.base.core.depend_inject import Autowired, Component, RefreshScope, Value, logger
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.common import FeedbackTypeEnum, VerifyCodeTypeEnum
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.user import User
from apps.base.utils.ip_util import IpUtil
from apps.base.utils.random_util import RandomUtil
from apps.base.utils.redis_util import RedisUtil
from apps.web.core.context_vars import ContextVars
from apps.web.core.kafka.util import KafkaUtil
from apps.web.vo.common_vo import EmailCodeVO, FeedbackVO, MobileCodeVO, UserEmailCodeVO, UserMobileCodeVO
from apps.web.vo.user_vo import ValidateAccountExistVO


@Component()
@RefreshScope("github")
class CommonService:
    redis_util: RedisUtil = Autowired()
    kafka_util: KafkaUtil = Autowired()
    github_config: dict[str, Any] | None = Value("github")

    async def get_github_commits(self, repo: str, page: int, size: int) -> dict[str, Any]:
        """
        分页获取指定仓库的 GitHub 提交动态。

        :param repo: GitHub 仓库名
        :param page: 页码
        :param size: 每页数量
        :return: GitHub 提交动态分页数据
        """
        github_config = self.github_config or {}
        owner = github_config.get("owner")
        branch = github_config.get("branch")
        if not owner or not branch:
            raise MyException(ErrorCode.SERVICE_ERROR)

        cache_ttl = int(github_config.get("cache-ttl") or 600)
        cache_key = f"github:commits:{owner}:{repo}:{branch}:{page}:{size}"
        try:
            cached_data = await self.redis_util.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception:
            logger.warning("读取 GitHub Commit 缓存失败，将回源查询", exc_info=True)

        github_commits, has_next = await self._fetch_github_commits(owner, repo, branch, page, size)
        result = {
            "repo": repo,
            "branch": branch,
            "page": page,
            "size": size,
            "has_next": has_next,
            "commits": [self._format_github_commit(commit) for commit in github_commits],
        }
        try:
            await self.redis_util.set(cache_key, json.dumps(result, ensure_ascii=False), ex=cache_ttl)
        except Exception:
            logger.warning("写入 GitHub Commit 缓存失败", exc_info=True)
        return result

    async def _fetch_github_commits(
        self,
        owner: str,
        repo: str,
        branch: str,
        page: int,
        size: int,
    ) -> tuple[list[dict[str, Any]], bool]:
        """
        请求 GitHub Commit API。

        :param owner: GitHub 用户名
        :param repo: GitHub 仓库名
        :param branch: 固定分支名
        :param page: 页码
        :param size: 每页数量
        :return: GitHub 原始提交列表及是否存在下一页
        """
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ltw-blog-web",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        token = (self.github_config or {}).get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        params = {"sha": branch, "page": page, "per_page": size}

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, params=params, timeout=timeout) as response:
                    if response.status == 404:
                        raise MyException(ErrorCode.DATA_NOT_EXISTS)
                    if response.status in (403, 429):
                        raise MyException(ErrorCode.SERVICE_ERROR)
                    if response.status != 200:
                        raise MyException(ErrorCode.SERVICE_ERROR)
                    data = await response.json()
                    if not isinstance(data, list):
                        raise MyException(ErrorCode.SERVICE_ERROR)
                    has_next = 'rel="next"' in response.headers.get("Link", "")
                    return data, has_next
        except MyException:
            raise
        except (aiohttp.ClientError, TimeoutError, TypeError, ValueError) as exc:
            logger.warning("请求 GitHub Commit API 失败", exc_info=True)
            raise MyException(ErrorCode.SERVICE_ERROR) from exc

    @staticmethod
    def _format_github_commit(commit: dict[str, Any]) -> dict[str, Any]:
        """
        将 GitHub Commit 数据转换为前端展示结构。

        :param commit: GitHub 原始 Commit 数据
        :return: 前端 Commit 动态数据
        """
        sha = commit.get("sha") or ""
        author = commit.get("author") or {}
        commit_data = commit.get("commit") or {}
        commit_author = commit_data.get("author") or {}
        return {
            "message": commit_data.get("message"),
            "commit_time": commit_author.get("date"),
            "avatar_url": author.get("avatar_url"),
            "html_url": commit.get("html_url"),
            "sha": sha,
            "short_sha": sha[:7],
        }

    async def get_website_view_count(self):
        """
        获取网站访问量
        :return:
        """
        return await self.redis_util.Website.get_website_view_count()

    async def add_website_view_count(self):
        """
        增加网站访问量
        :return:
        """
        request = ContextVars.request.get()
        ip_address = IpUtil.get_ip_address(request)
        await self.redis_util.Website.incr_website_view_count(ip_address)

    async def get_email_code(self, email_code_vo: EmailCodeVO):
        """
        获取邮箱验证码(无需登录)
        :param email_code_vo:
        :return:
        """
        if email_code_vo.code_type == VerifyCodeTypeEnum.REGISTER:
            title = EmailConstant.REGISTER_TITLE
            content = EmailConstant.REGISTER_CONTENT
        elif email_code_vo.code_type == VerifyCodeTypeEnum.FIND_PASSWORD:
            title = EmailConstant.FIND_PASSWORD_TITLE
            content = EmailConstant.FIND_PASSWORD_CONTENT
        else:
            raise MyException(ErrorCode.PARAM_ERROR)
        email = email_code_vo.email
        code = RandomUtil.random_numbers(6)
        await self.kafka_util.send_email(email, title, content.format(code))
        await self.redis_util.VerifyCode.save_verify_code(email, code, email_code_vo.code_type)

    async def get_user_email_code(self, email_code_vo: UserEmailCodeVO):
        """
        获取邮箱验证码(需登录)
        :param email_code_vo:
        :return:
        """
        if email_code_vo.code_type == VerifyCodeTypeEnum.CHANGE_BIND:
            title = EmailConstant.CHANGE_BIND_TITLE
            content = EmailConstant.CHANGE_BIND_CONTENT
        elif email_code_vo.code_type == VerifyCodeTypeEnum.CHANGE_PASSWORD:
            title = EmailConstant.CHANGE_PASSWORD_TITLE
            content = EmailConstant.CHANGE_PASSWORD_CONTENT
        else:
            raise MyException(ErrorCode.PARAM_ERROR)
        user_id = ContextVars.token_user_id.get()
        user = await db.model_first(select(User).where(User.id == user_id))
        code = RandomUtil.random_numbers(6)
        await self.kafka_util.send_email(user.email, title, content.format(code))
        await self.redis_util.VerifyCode.save_verify_code(user.email, code, email_code_vo.code_type)

    async def valid_user_email_code(self, email_code_vo: UserEmailCodeVO):
        """
        验证邮箱验证码(需登录)
        :param email_code_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        user = await db.model_first(select(User).where(User.id == user_id))
        return await self.redis_util.VerifyCode.check_verify_code(
            user.email, email_code_vo.code, email_code_vo.code_type
        )

    async def get_mobile_code(self, mobile_code_vo: MobileCodeVO):
        """
        获取手机号验证码(无需登录)
        :param mobile_code_vo:
        :return:
        """
        mobile = mobile_code_vo.mobile
        code = RandomUtil.random_numbers(6)
        if mobile_code_vo.code_type == VerifyCodeTypeEnum.REGISTER:
            sms_type = SmsConstant.TYPE_REGISTER
        elif mobile_code_vo.code_type == VerifyCodeTypeEnum.LOGIN:
            sms_type = SmsConstant.TYPE_LOGIN
        elif mobile_code_vo.code_type == VerifyCodeTypeEnum.FIND_PASSWORD:
            sms_type = SmsConstant.TYPE_FIND_PASSWORD
        else:
            raise MyException(ErrorCode.PARAM_ERROR)
        await self.kafka_util.send_sms(mobile, sms_type, code)
        await self.redis_util.VerifyCode.save_verify_code(mobile, code, mobile_code_vo.code_type)

    async def get_user_mobile_code(self, mobile_code_vo: UserMobileCodeVO):
        """
        获取手机号验证码(需登录)
        :param mobile_code_vo:
        :return:
        """
        if mobile_code_vo.code_type == VerifyCodeTypeEnum.CHANGE_BIND:
            sms_type = SmsConstant.TYPE_CHANGE_BIND
        elif mobile_code_vo.code_type == VerifyCodeTypeEnum.CHANGE_PASSWORD:
            sms_type = SmsConstant.TYPE_CHANGE_PASSWORD
        else:
            raise MyException(ErrorCode.PARAM_ERROR)
        user_id = ContextVars.token_user_id.get()
        user = await db.model_first(select(User).where(User.id == user_id))
        code = RandomUtil.random_numbers(6)
        await self.kafka_util.send_sms(user.mobile, sms_type, code)
        await self.redis_util.VerifyCode.save_verify_code(user.mobile, code, mobile_code_vo.code_type)

    async def valid_mobile_code(self, mobile_code_vo: MobileCodeVO):
        """
        验证手机号验证码(无需登录)
        :param mobile_code_vo:
        :return:
        """
        if mobile_code_vo.code_type not in (
            VerifyCodeTypeEnum.FIND_PASSWORD,
            VerifyCodeTypeEnum.REGISTER,
            VerifyCodeTypeEnum.LOGIN,
        ):
            raise MyException(ErrorCode.PARAM_ERROR)
        return await self.redis_util.VerifyCode.check_verify_code(
            mobile_code_vo.mobile, mobile_code_vo.code, mobile_code_vo.code_type
        )

    async def valid_user_mobile_code(self, mobile_code_vo: UserMobileCodeVO):
        """
        验证手机号验证码(需登录)
        :param mobile_code_vo:
        :return:
        """
        if mobile_code_vo.code_type not in (VerifyCodeTypeEnum.CHANGE_BIND, VerifyCodeTypeEnum.CHANGE_PASSWORD):
            raise MyException(ErrorCode.PARAM_ERROR)
        user_id = ContextVars.token_user_id.get()
        user = await db.model_first(select(User).where(User.id == user_id))
        return await self.redis_util.VerifyCode.check_verify_code(
            user.mobile, mobile_code_vo.code, mobile_code_vo.code_type
        )

    async def valid_account_exists(self, validate_account_exist_vo: ValidateAccountExistVO):
        """
        验证账户是否已存在
        :param validate_account_exist_vo:
        :return:
        """
        query_dict = validate_account_exist_vo.model_dump(exclude_none=True)
        if not query_dict:
            raise MyException(ErrorCode.PARAM_ERROR)
        total = await db.scalar(select(func.count()).select_from(User).filter_by(**query_dict))
        return total > 0

    async def add_feedback(self, feedback_vo: FeedbackVO):
        """
        用户反馈
        :param feedback_vo:
        :return:
        """
        # 反馈暂时先发送至邮箱
        feedback_type = "需求" if feedback_vo.feedback_type == FeedbackTypeEnum.REQUIREMENT else "缺陷"
        content = f"""
        <html>
            <body>
                <p>用户邮箱: {feedback_vo.email}</p>
                <p>反馈类型: {feedback_type}</p>
                <p>需求: {feedback_vo.title}</p>
                <p>反馈内容: {feedback_vo.content}</p>
            </body>
        </html>
        """
        await self.kafka_util.send_email(EmailConstant.SELF_MAIL, f"心悦心享-用户反馈", content)
