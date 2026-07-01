#!/usr/bin/env python3
import json
import subprocess
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
INFO_PATH = ROOT_DIR / ".info"
PYPROJECT_PATH = ROOT_DIR / "pyproject.toml"


def run_git(args: list[str]) -> str:
    """
    执行 Git 只读命令并返回输出。

    :param args: Git 子命令参数。
    :return: 命令标准输出。
    """
    return subprocess.check_output(["git", *args], cwd=ROOT_DIR, text=True).strip()


def read_project_info() -> dict[str, str]:
    """
    读取项目基础信息。

    :return: 项目名称和版本。
    """
    with PYPROJECT_PATH.open("rb") as file:
        pyproject = tomllib.load(file)
    project = pyproject.get("project", {})
    return {
        "name": project.get("name", ""),
        "version": project.get("version", ""),
    }


def build_info() -> dict[str, Any]:
    """
    构建提交版本信息。

    :return: 可写入 .info 的版本信息。
    """
    project = read_project_info()
    return {
        "project": project["name"],
        "version": project["version"],
        "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "branch": run_git(["branch", "--show-current"]),
        "sourceCommit": run_git(["rev-parse", "HEAD"]),
        "sourceCommitShort": run_git(["rev-parse", "--short", "HEAD"]),
        "sourceCommitTime": run_git(["log", "-1", "--format=%cI"]),
        "sourceCommitSubject": run_git(["log", "-1", "--format=%s"]),
        "note": "pre-commit 生成；sourceCommit 为提交前 HEAD，不能表示本次提交自己的 hash。",
    }


def main() -> None:
    """
    生成 .info 文件。
    """
    info = build_info()
    INFO_PATH.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
