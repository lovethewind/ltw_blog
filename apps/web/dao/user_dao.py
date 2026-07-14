import asyncio

from sqlalchemy import select

from apps.base.core.depend_inject import Component
from apps.base.core.sqlalchemy.db_helper import db
from apps.base.enum.user import UserSettingsEnum
from apps.base.models.user import User, UserRestriction, UserSettings
from apps.web.dto.user_dto import (
    CachedUserInfoDTO,
    CachedUserRestrictionDTO,
    CachedUserRestrictionItemDTO,
)


@Component()
class UserDao:
    common_user_settings = [UserSettingsEnum.ALLOW_VIEW_MY_FOLLOW, UserSettingsEnum.ALLOW_VIEW_MY_COLLECT]

    async def get_user_info(self, user_id: int) -> CachedUserInfoDTO:
        """
        获取用户基本信息。

        :param user_id: 用户 ID。
        :return: 包含公开设置和未解除限制的内部缓存用户信息。
        """
        user, restrictions, user_settings = await asyncio.gather(
            db.model_first(select(User).where(User.id == user_id)),
            db.model_all(
                select(UserRestriction).where(
                    UserRestriction.user_id == user_id,
                    UserRestriction.is_cancel.is_(False),
                )
            ),
            self.get_user_common_settings(user_id),
        )
        dto = CachedUserInfoDTO.model_validate(user, from_attributes=True)
        restriction_dto = CachedUserRestrictionDTO(
            items=CachedUserRestrictionItemDTO.bulk_model_validate(list(restrictions))
        )
        dto.user_restrictions = restriction_dto
        dto.user_settings = user_settings
        return dto

    async def get_user_common_settings(self, user_id: int) -> dict[UserSettingsEnum, str | bool]:
        """
        获取用户的公开配置。

        :param user_id: 用户 ID。
        :return: 用户公开配置。
        """
        ret = await db.model_all(
            select(UserSettings).where(
                UserSettings.user_id == user_id,
                UserSettings.setting_key.in_(self.common_user_settings),
            )
        )
        return {item.setting_key: self._covert_bool_value(item.setting_value) for item in ret}

    async def get_user_settings(self, user_id: int) -> dict[UserSettingsEnum, str | bool]:
        """
        获取用户的所有配置。

        :param user_id: 用户 ID。
        :return: 用户配置。
        """
        ret = await db.model_all(select(UserSettings).where(UserSettings.user_id == user_id))
        return {item.setting_key: self._covert_bool_value(item.setting_value) for item in ret}

    async def get_user_setting_value(self, user_id: int, key: UserSettingsEnum) -> str | bool | None:
        """
        获取用户的配置值

        :param user_id: 用户 ID。
        :param key: 配置键。
        :return: 配置值；不存在时返回 None。
        """
        ret = await db.model_first(
            select(UserSettings).where(UserSettings.user_id == user_id, UserSettings.setting_key == key)
        )
        if not ret:
            return None
        return self._covert_bool_value(ret.setting_value)

    def _covert_bool_value(self, value: str):
        """
        将字符串布尔型转为对象
        :param value:
        :return:
        """
        if value in ["true", "True"]:
            return True
        if value in ["false", "False"]:
            return False
        return value
