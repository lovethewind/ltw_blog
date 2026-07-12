from apps.admin.dao.comment_dao import AdminCommentDao
from apps.admin.dto.comment_dto import AdminCommentDTO
from apps.admin.service.base_service import AdminBaseService
from apps.admin.vo.comment_vo import AdminCommentQueryVO, AdminCommentStatusVO, AdminCommentUpdateVO
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException


@Component()
class AdminCommentService(AdminBaseService):
    """后台评论服务。"""

    admin_comment_dao: AdminCommentDao = Autowired()

    async def list_comments(self, query_vo: AdminCommentQueryVO) -> dict:
        """
        分页查询评论。

        :param query_vo: 评论查询参数
        :return: 评论分页数据
        """
        comments, total = await self.admin_comment_dao.list_comments(
            query_vo.current,
            query_vo.size,
            query_vo.keyword,
            query_vo.obj_id,
            query_vo.obj_type,
            query_vo.status,
            query_vo.user_id,
        )
        records = [AdminCommentDTO.model_validate(comment) for comment in comments]
        return self._page_result(query_vo.current, query_vo.size, total, records)

    async def get_comment(self, comment_id: int) -> AdminCommentDTO:
        """
        查询评论详情。

        :param comment_id: 评论 ID
        :return: 评论详情
        :raises MyException: 评论不存在时抛出
        """
        comment = await self.admin_comment_dao.get_comment_by_id(comment_id)
        if not comment:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminCommentDTO.model_validate(comment)

    async def update_comment(self, comment_id: int, comment_vo: AdminCommentUpdateVO) -> AdminCommentDTO:
        """
        更新评论。

        :param comment_id: 评论 ID
        :param comment_vo: 评论更新参数
        :return: 评论详情
        :raises MyException: 评论不存在时抛出
        """
        comment = await self.admin_comment_dao.get_comment_by_id(comment_id)
        if not comment:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        comment = await self.admin_comment_dao.update_comment(comment, comment_vo.model_dump(exclude_none=True))
        return AdminCommentDTO.model_validate(comment)

    async def update_comment_status(self, comment_id: int, status_vo: AdminCommentStatusVO) -> AdminCommentDTO:
        """
        更新评论状态。

        :param comment_id: 评论 ID
        :param status_vo: 状态更新参数
        :return: 评论详情
        :raises MyException: 评论不存在时抛出
        """
        comment = await self.admin_comment_dao.get_comment_by_id(comment_id)
        if not comment:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        comment = await self.admin_comment_dao.update_comment(comment, {"status": status_vo.status})
        return AdminCommentDTO.model_validate(comment)

    async def delete_comment(self, comment_id: int) -> None:
        """
        删除评论。

        :param comment_id: 评论 ID
        :return: None
        :raises MyException: 评论不存在时抛出
        """
        comment = await self.admin_comment_dao.get_comment_by_id(comment_id)
        if not comment:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_comment_dao.delete_comment(comment_id)
