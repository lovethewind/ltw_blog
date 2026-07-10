import pathlib


class AdminPathUtil:
    """
    后台管理路径工具。
    """

    PROJECT_PATH = pathlib.Path(__file__).parent.parent
    RESOURCE_PATH = PROJECT_PATH / "resources"

    @classmethod
    def get_resource_path(cls, resource_name: str, check_exist: bool = False) -> pathlib.Path:
        """
        获取后台管理资源文件路径。

        :param resource_name: 资源文件名称
        :param check_exist: 是否检查资源文件存在
        :return: 资源文件路径
        :raises FileNotFoundError: 资源文件不存在时抛出
        """
        if check_exist:
            if not (cls.RESOURCE_PATH / resource_name).exists():
                raise FileNotFoundError(f"{resource_name} not found")
        return cls.RESOURCE_PATH / resource_name

    @classmethod
    def join_path(cls, *paths: str) -> pathlib.Path:
        """
        拼接路径。

        :param paths: 路径片段
        :return: 拼接后的路径
        """
        return pathlib.Path(*paths)
