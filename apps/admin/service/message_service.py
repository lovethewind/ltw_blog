from apps.admin.dao.message_dao import AdminMessageDao
from apps.admin.dto.message_dto import AdminMessageDTO, AdminMessageUserDTO
from apps.admin.service.base_service import AdminBaseService
from apps.admin.vo.message_vo import AdminMessageQueryVO, AdminMessageUpdateVO
from apps.base.core.depend_inject import Autowired, Component
from apps.base.enum.error_code import ErrorCode
from apps.base.exception.my_exception import MyException
from apps.base.models.message import Message
from apps.base.models.user import User


@Component()
class AdminMessageService(AdminBaseService):
    """后台留言服务。"""

    admin_message_dao: AdminMessageDao = Autowired()

    async def list_messages(self, query_vo: AdminMessageQueryVO) -> dict:
        """
        分页查询留言。

        :param query_vo: 留言查询参数
        :return: 留言分页数据
        """
        messages, total = await self.admin_message_dao.list_messages(
            query_vo.current, query_vo.size, query_vo.keyword, query_vo.user_id, query_vo.parent_id
        )
        user_map = await self.admin_message_dao.list_message_users(list({message.user_id for message in messages}))
        parent_content_map = await self.admin_message_dao.list_parent_message_contents(messages)
        records = [self._dump_message(message, user_map, parent_content_map) for message in messages]
        return self._page_result(query_vo.current, query_vo.size, total, records)

    def _dump_message(
        self,
        message: Message,
        user_map: dict[int, User],
        parent_content_map: dict[int, str],
    ) -> AdminMessageDTO:
        """
        转换留言响应数据，并附加用户和父级留言摘要。

        :param message: 留言对象。
        :param user_map: 用户 ID 到用户对象的映射。
        :param parent_content_map: 父留言 ID 到留言内容的映射。
        :return: 留言响应数据。
        """
        dto = AdminMessageDTO.model_validate(message)
        user = user_map.get(message.user_id)
        if user:
            dto.user = AdminMessageUserDTO.model_validate(user)
        dto.parent_content = parent_content_map.get(message.parent_id)
        return dto

    async def get_message(self, message_id: int) -> AdminMessageDTO:
        """
        查询留言详情。

        :param message_id: 留言 ID
        :return: 留言详情
        :raises MyException: 留言不存在时抛出
        """
        message = await self.admin_message_dao.get_message_by_id(message_id)
        if not message:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        return AdminMessageDTO.model_validate(message)

    async def update_message(self, message_id: int, message_vo: AdminMessageUpdateVO) -> AdminMessageDTO:
        """
        更新留言。

        :param message_id: 留言 ID
        :param message_vo: 留言更新参数
        :return: 留言详情
        :raises MyException: 留言不存在时抛出
        """
        message = await self.admin_message_dao.get_message_by_id(message_id)
        if not message:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        data = message_vo.model_dump(exclude_none=True)
        self._normalize_message_data(data)
        message = await self.admin_message_dao.update_message(message, data)
        return AdminMessageDTO.model_validate(message)

    async def delete_message(self, message_id: int) -> None:
        """
        删除留言。

        :param message_id: 留言 ID
        :return: None
        :raises MyException: 留言不存在时抛出
        """
        message = await self.admin_message_dao.get_message_by_id(message_id)
        if not message:
            raise MyException(ErrorCode.DATA_NOT_EXISTS)
        await self.admin_message_dao.delete_message(message_id)

    def _normalize_message_data(self, data: dict[str, object]) -> None:
        """
        规范化留言保存数据。

        :param data: 留言数据
        :return: None
        """
        for field in ("avatar", "nickname", "email", "address"):
            if field in data and data[field] is None:
                data[field] = ""
