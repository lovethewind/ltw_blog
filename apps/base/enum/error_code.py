from enum import Enum


class ErrorCode(Enum):
    # 通用
    SUCCESS = (200, "success")
    SERVICE_ERROR = (10001, "服务异常")
    PARAM_ERROR = (10002, "参数错误")
    ILLEGAL_REQUEST = (10003, "非法请求")
    REPEAT_SUBMIT = (10004, "重复提交数据，请稍等再试")
    NO_LOGIN = (10005, "尚未登录，请登录")
    NO_PERMISSION = (10006, "很抱歉，暂无当前功能操作权限")
    TOKEN_IS_INVALID = (10007, "登录已过期，请重新登录")
    OPERATE_FAILED = (10008, "操作失败，请稍后重试")
    DATA_NOT_EXISTS = (10009, "数据不存在")
    TOKEN_IS_EMPTY = (10010, "请先登录后再尝试")
    REGISTER_FAIL = (10011, "注册失败，请稍后重试")

    # 账户相关
    USERNAME_ERROR = (11000, "账号不正确")
    PASSWORD_ERROR = (11001, "密码不正确")
    ACCOUNT_NOT_EXIST = (11002, "账号不存在")
    ACCOUNT_STOP = (11003, "账号已停用")
    ACCOUNT_HAS_EXIST = (11004, "账号已存在")
    ACCOUNT_NOT_ACTIVE = (11005, "账号已停用")
    ACCOUNT_IS_FORBIDDEN = (11006, "账号已禁用")
    ACCOUNT_ADMIN_LOGIN_NOT_SUPPORT = (11008, "账号不支持后台登录")
    ACCOUNT_CANT_DELETE_SELF = (11009, "无法删除自己正在登录的账号")
    EMAIL_HAS_EXISTS = (11010, "邮箱已存在")
    MOBILE_HAS_EXISTS = (11011, "手机号已存在")
    WECHAT_NOT_SCAN = (11012, "请先扫码")
    WECHAT_NOT_BIND = (11013, "该微信号尚未绑定用户，请先登录进入个人中心进行绑定")
    WECHAT_HAS_BIND = (11014, "该微信号已绑定用户")
    WECHAT_VERIFY_TIMEOUT = (11015, "微信登录超时，请重新扫码登录")
    # 菜单相关
    MENU_HAS_SUB_ITEM = (12001, "该项存在子菜单, 请先删除子菜单")
    # 验证码
    CODE_VERIFY_OVER_MAX_LIMIT = (13001, "该验证码超过最大验证次数，请重新获取并验证")
    CODE_VERIFY_ERROR = (13002, "验证码错误")
    # 定时任务
    NOT_VALID_CRON_EXPRESSION = (14001, "不是有效的cron表达式")
    SCHEDULER_JOB_ERROR = (14002, "定时任务操作失败")
    # 文章相关
    CRAWLING_ARTICLE_ERROR = (15001, "爬取文章失败")
    # 图库相关
    PICTURE_ALBUM_NOT_EXIST = (16001, "图库不存在")
    PICTURE_ALBUM_IS_PUBLIC = (16002, "图库已公开，无法进行该操作")
    PICTURE_ALBUM_PUBLIC_NAME_EXIST = (16003, "图库分类名称已存在")
    PICTURE_NOT_EXIST = (16004, "图片不存在")
    # 网站导航相关
    WEBSITE_HAS_EXIST = (17001, "该网站已存在")
    # 分享相关
    SHARE_NOT_EXIST = (18001, "分享不存在")

    @property
    def code(self) -> int:
        return self.value[0]

    @property
    def message(self) -> str:
        return self.value[1]
