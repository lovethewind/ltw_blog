import pathlib


class PathUtil:
    PROJECT_PATH = pathlib.Path(__file__).parent.parent
    RESOURCE_PATH = PROJECT_PATH / "resources"

    @classmethod
    def get_resource_path(cls, resource_name: str, check_exist=False):
        if check_exist:
            if not (cls.RESOURCE_PATH / resource_name).exists():
                raise FileNotFoundError(f"{resource_name} not found")
        return cls.RESOURCE_PATH / resource_name

    @classmethod
    def join_path(cls, *paths: str):
        return pathlib.Path(*paths)
