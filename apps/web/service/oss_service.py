# @Time    : 2024/9/1 19:28
# @Author  : frank
# @File    : oss_service.py
from apps.base.core.depend_inject import Component, Autowired
from apps.base.models.source import Source
from apps.base.utils.oss_util import OssUtil, DirType
from apps.web.core.context_vars import ContextVars
from apps.web.vo.oss_vo import GetSignatureVO


@Component()
class OssService:
    oss_util: OssUtil = Autowired()

    async def get_signature_url(self, get_signature_vo: GetSignatureVO):
        """
        获取签名url
        :param get_signature_vo:
        :return:
        """
        user_id = ContextVars.token_user_id.get()
        signature_result = self.oss_util.get_signature(DirType[get_signature_vo.dir_type.upper()], get_signature_vo.file_name)
        source = Source()
        source.user_id = user_id
        source.url = signature_result.url
        await source.save()
        return signature_result
