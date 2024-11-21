from collections.abc import Iterable
from typing import Type

from apps.base.core.depend_inject import Component
from apps.base.enum.user import UserSettingsEnum
from apps.base.models.user import User, UserSettings
from apps.web.dto.user_dto import UserBaseInfoDTO, UserCommonInfoDTO


@Component()
class UserDao:
    common_user_settings = [UserSettingsEnum.ALLOW_VIEW_MY_FOLLOW,
                            UserSettingsEnum.ALLOW_VIEW_MY_COLLECT]

    async def get_user_info(self, user_id: int):
        """
        获取用户基本信息
        :param user_id:
        :return:
        """
        user = await User.filter(id=user_id).first()
        return UserCommonInfoDTO.model_validate(user, from_attributes=True)

    async def get_user_common_settings(self, user_id: int) -> dict[UserSettingsEnum, str | bool]:
        """
        获取用户的基本配置
        :param user_id:
        :return:
        """
        ret = await UserSettings.filter(user_id=user_id, setting_key__in=self.common_user_settings)
        return {item.setting_key: self._covert_bool_value(item.setting_value) for item in ret}

    async def get_user_settings(self, user_id: int) -> dict[UserSettingsEnum, str | bool]:
        """
        获取用户的所有配置
        :param user_id:
        :return:
        """
        ret = await UserSettings.filter(user_id=user_id)
        return {item.setting_key: self._covert_bool_value(item.setting_value) for item in ret}

    async def get_user_setting_value(self, user_id: int, key: UserSettingsEnum) -> str | bool | None:
        """
        获取用户的配置值
        :param user_id:
        :param key:
        :return:
        """
        ret = await UserSettings.filter(user_id=user_id, setting_key=key).first()
        if not ret:
            return
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
