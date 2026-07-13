from apscheduler.triggers.cron import CronTrigger


def build_cron_trigger(expression: str, timezone: str | None = None) -> CronTrigger:
    """根据五段或六段 Cron 表达式创建 APScheduler 触发器。

    :param expression: Cron 表达式，支持标准五段式和带秒字段的六段式
    :param timezone: 触发器使用的时区
    :return: APScheduler Cron 触发器
    :raises ValueError: Cron 表达式字段数量或内容无效时抛出
    """
    fields = expression.strip().split()
    if len(fields) == 5:
        return CronTrigger.from_crontab(expression, timezone=timezone)
    if len(fields) != 6:
        raise ValueError("Cron 表达式必须包含五段或六段")
    second, minute, hour, day, month, day_of_week = fields
    return CronTrigger(
        second=second,
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
        timezone=timezone,
    )
