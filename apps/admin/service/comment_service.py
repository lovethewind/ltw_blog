from apps.admin.dao.comment_dao import AdminCommentDao
from apps.admin.dto.comment_dto import AdminCommentDTO, AdminCommentUserDTO
from apps.admin.service.base_service import AdminBaseService
from apps.admin.vo.comment_vo import AdminCommentQueryVO, AdminCommentStatusVO, AdminCommentUpdateVO
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.comment import Comment
from apps.base.models.user import User


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
        user_map = await self.admin_comment_dao.list_comment_users(list({comment.user_id for comment in comments}))
        object_content_map = await self.admin_comment_dao.list_comment_object_contents(comments)
        parent_content_map = await self.admin_comment_dao.list_parent_comment_contents(comments)
        records = [
            self._dump_comment(
                comment,
                user_map,
                object_content_map,
                parent_content_map,
            )
            for comment in comments
        ]
        return self._page_result(query_vo.current, query_vo.size, total, records)

    def _dump_comment(
        self,
        comment: Comment,
        user_map: dict[int, User],
        object_content_map: dict[tuple[int, int], str],
        parent_content_map: dict[int, str],
    ) -> AdminCommentDTO:
        """
        转换评论响应数据，并附加用户和对象摘要。

        :param comment: 评论对象。
        :param user_map: 用户 ID 到用户对象的映射。
        :param object_content_map: 对象类型和对象 ID 到展示内容的映射。
        :param parent_content_map: 父评论 ID 到评论内容的映射。
        :return: 评论响应数据。
        """
        dto = AdminCommentDTO.model_validate(comment)
        user = user_map.get(comment.user_id)
        if user:
            dto.user = AdminCommentUserDTO.model_validate(user)
        dto.obj_content = object_content_map.get((comment.obj_type, comment.obj_id))
        dto.parent_content = parent_content_map.get(comment.parent_id)
        return dto

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
