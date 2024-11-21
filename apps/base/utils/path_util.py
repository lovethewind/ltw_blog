from os import PathLike
from pathlib import Path


class PathUtil:
    RESOURCE_PATH = Path(__file__).parent.parent / "resources"

    @classmethod
    def join_path(cls, *path: str | PathLike, check_exist: bool = False) -> str:
        path = Path(*path)
        if check_exist and not path.exists():
            raise FileNotFoundError(f"Path {path} does not exist")
        return path.as_posix()

    @classmethod
    def get_resource_path(cls, resource_name: str, check_exist=False) -> str:
        return cls.join_path(cls.RESOURCE_PATH, resource_name, check_exist=check_exist)
