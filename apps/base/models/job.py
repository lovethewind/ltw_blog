from sqlalchemy import BigInteger, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.base.core.sqlalchemy.base_model import BaseModel
from apps.base.enum.job import JobStatusEnum, MisfirePolicyEnum


class Job(BaseModel):
    """
    定时任务模型。
    """

    __tablename__ = "t_job"
    __table_args__ = {"comment": "定时任务表"}

    name: Mapped[str] = mapped_column(String(64), comment="任务名称")
    group: Mapped[str] = mapped_column(String(64), default="DEFAULT", comment="任务组名")
    invoke_target: Mapped[str] = mapped_column(String(500), comment="调用目标字符串")
    cron_expression: Mapped[str] = mapped_column(String(255), comment="cron执行表达式")
    misfire_policy: Mapped[int] = mapped_column(
        Integer, default=MisfirePolicyEnum.ABANDON.value, comment="计划执行策略（1:立即执行 2:执行一次 3:放弃执行）"
    )
    concurrent: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否并发执行")
    status: Mapped[int] = mapped_column(Integer, default=JobStatusEnum.PAUSE.value, comment="状态(1:正常 2:暂停)")
    create_user_id: Mapped[int] = mapped_column(BigInteger, comment="创建者id")
    update_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="更新者id")
    description: Mapped[str] = mapped_column(String(1000), default="", comment="说明")
