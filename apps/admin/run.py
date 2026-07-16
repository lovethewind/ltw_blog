import os
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

module_path = Path(__file__).parent.parent.parent

if module_path not in sys.path:
    sys.path.append(str(module_path))

load_dotenv(module_path / ".env", override=False)

import apps.admin.config.logger_config  # noqa: F401
from apps.admin.config.server_config import get_server_host, get_server_port
from apps.admin.core.create_app import create_app  # noqa: F401


def main() -> None:
    """以热重载模式启动本地 Admin 开发服务。"""
    reload_enabled = os.getenv("APP_ACTIVE", "").casefold() == "dev"
    uvicorn.run(
        "apps.admin.run:create_app",
        host=get_server_host(),
        port=get_server_port(),
        log_level="info",
        factory=True,
        reload=reload_enabled,
        reload_dirs=[str(module_path / "apps")] if reload_enabled else None,
    )


if __name__ == "__main__":
    main()
