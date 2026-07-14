import pathlib


class SchedulerPathUtil:
    """定时任务服务路径工具。"""

    PROJECT_PATH = pathlib.Path(__file__).parent.parent
    RESOURCE_PATH = PROJECT_PATH / "resources"

    @classmethod
    def get_resource_path(cls, resource_name: str, check_exist: bool = False) -> pathlib.Path:
        """获取定时任务服务资源文件路径。

        :param resource_name: 资源文件名称。
        :param check_exist: 是否检查资源文件存在。
        :return: 资源文件路径。
        :raises FileNotFoundError: 资源文件不存在时抛出。
        """
        resource_path = cls.RESOURCE_PATH / resource_name
        if check_exist and not resource_path.exists():
            raise FileNotFoundError(f"{resource_name} not found")
        return resource_path

    @classmethod
    def join_path(cls, *paths: str) -> pathlib.Path:
        """拼接路径。

        :param paths: 路径片段。
        :return: 拼接后的路径。
        """
        return pathlib.Path(*paths)
