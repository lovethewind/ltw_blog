from tortoise import fields

from apps.base.enum.job import MisfirePolicyEnum, JobStatusEnum
from apps.base.models.base import BaseModel


class Job(BaseModel):
    name = fields.CharField(max_length=64, description="任务名称")
    group = fields.CharField(max_length=64, default='DEFAULT', description="任务组名")
    invoke_target = fields.CharField(max_length=500, description="调用目标字符串")
    cron_expression = fields.CharField(max_length=255, description="cron执行表达式")
    misfire_policy = fields.IntEnumField(MisfirePolicyEnum, default=MisfirePolicyEnum.ABANDON,
                                         description="计划执行策略（1:立即执行 2:执行一次 3:放弃执行）")
    concurrent = fields.BooleanField(default=False, description="是否并发执行")
    status = fields.IntEnumField(JobStatusEnum, default=JobStatusEnum.PAUSE, description="状态(1:正常 2:暂停)")
    create_user_id = fields.BigIntField(description="创建者id")
    update_user_id = fields.BigIntField(null=True, description="更新者id")
    description = fields.CharField(max_length=1000, default='', description="说明")

    class Meta:
        table = "t_job"
        table_description = "定时任务表"
