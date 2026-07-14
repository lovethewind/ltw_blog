from fastapi.routing import APIRouter
from starlette.responses import Response

from apps.admin.vo.common_vo import AdminUploadSignatureVO
from apps.base.core.depend_inject import Autowired, Controller
from apps.base.enum.oss import DirType
from apps.base.utils.oss_util import OssUtil
from apps.base.utils.response_util import ResponseUtil

router = APIRouter(prefix="/common", tags=["后台公共接口"])


@Controller(router)
class AdminCommonController:
    """
    后台公共接口控制器。
    """

    oss_util: OssUtil = Autowired()

    @router.get("/health", summary="后台健康检查")
    async def health(self) -> Response:
        """
        检查后台管理服务健康状态。

        :return: 健康状态
        """
        return ResponseUtil.success({"status": "ok"})

    @router.post("/upload/signature", summary="获取后台上传签名")
    async def get_upload_signature(self, signature_vo: AdminUploadSignatureVO) -> Response:
        """
        获取后台文件上传签名。

        :param signature_vo: 上传签名参数
        :return: 上传签名信息
        """
        ret = await self.oss_util.get_signature(
            DirType[signature_vo.dir_type.upper()],
            signature_vo.file_name,
        )
        return ResponseUtil.success(ret)
