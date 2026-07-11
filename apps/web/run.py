import asyncio
import sys
from pathlib import Path

import uvicorn

module_path = Path(__file__).parent.parent.parent

if module_path not in sys.path:
    sys.path.append(str(module_path))

import apps.web.config.logger_config  # noqa: F401
from apps.web.config.server_config import get_server_host, get_server_port
from apps.web.core.create_app import create_app


async def main():
    config = uvicorn.Config(
        create_app,
        host=get_server_host(),
        port=get_server_port(),
        log_level="info",
        factory=True,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
