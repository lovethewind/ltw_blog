import asyncio
import os
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv
from watchfiles import PythonFilter, run_process

module_path = Path(__file__).parent.parent.parent

if module_path not in sys.path:
    sys.path.append(str(module_path))

load_dotenv(module_path / ".env", override=False)

import apps.scheduler.config.logger_config  # noqa: F401
from apps.base.core.sqlalchemy.session import close_sqlalchemy_engine, init_sqlalchemy_engine
from apps.scheduler.config.server_config import init_container_config
from apps.scheduler.core.scheduler import DatabaseScheduler


async def run_scheduler() -> None:
    """运行独立定时任务服务直至收到退出信号。

    :return: None
    """
    init_container_config()
    init_sqlalchemy_engine()
    scheduler = DatabaseScheduler()
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for stop_signal in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(stop_signal, stop_event.set)
    try:
        await scheduler.start()
        await stop_event.wait()
    finally:
        await scheduler.shutdown()
        await close_sqlalchemy_engine()


def run_scheduler_process() -> None:
    """启动单个定时任务工作进程。

    :return: None
    """
    asyncio.run(run_scheduler())


def main() -> None:
    """启动定时任务服务，并在开发环境监听 Python 文件变更。

    :return: None
    """
    if os.getenv("APP_ACTIVE", "").casefold() != "dev":
        run_scheduler_process()
        return
    run_process(
        module_path / "apps",
        target=run_scheduler_process,
        watch_filter=PythonFilter(),
    )


if __name__ == "__main__":
    main()
