import asyncio
import signal

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


def main() -> None:
    """启动独立定时任务进程。

    :return: None
    """
    asyncio.run(run_scheduler())


if __name__ == "__main__":
    main()
