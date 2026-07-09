from apps.base.core.depend_inject import Autowired, Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.models.source import Source
from apps.base.utils.oss_util import DirType, OssUtil
from apps.web.core.context_vars import ContextVars
from apps.web.dto.oss_dto import SignatureResultDTO
from apps.web.vo.oss_vo import GetSignatureVO


@Component()
class OssService:
    oss_util: OssUtil = Autowired()

    async def get_signature_url(self, get_signature_vo: GetSignatureVO) -> SignatureResultDTO:
        """
        获取签名 URL 并记录待确认资源。

        :param get_signature_vo: 获取签名参数。
        :return: OSS 上传签名结果。
        """
        user_id = ContextVars.token_user_id.get()
        signature_result = await self.oss_util.get_signature(
            DirType[get_signature_vo.dir_type.upper()], get_signature_vo.file_name
        )
        source = Source(user_id=user_id, url=signature_result.url)
        await db.create(source, return_value=False)
        return signature_result
