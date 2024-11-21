class EmailConstant:
    SELF_MAIL = "1720045474@qq.com"

    TYPE_LOGIN = "login"
    TYPE_REGISTER = "register"
    TYPE_FIND_PASSWORD = "find"
    TYPE_CHANGE_BIND = "bind"

    TYPE_CHANGE_PASSWORD = "password"
    REGISTER_TITLE = "心悦心享-注册激活码"
    REGISTER_CONTENT = """<html>
            <body>
            <p>欢迎加入心悦心享小站，输入验证码即可完成你的账号注册哦，我们在这里等你！该验证码15分钟内有效。</p>
            <p>验证码: <b>{}</b></p></body>
            </html>"""
    FIND_PASSWORD_TITLE = "心悦心享-找回密码"
    FIND_PASSWORD_CONTENT = """<html>
            <body>
            <p>你正在找回密码，请注意账号安全，若非本人操作，请忽略此条信息，若存在账号安全问题，请及时修改密码，该验证码15分钟内有效。</p>
            <p>验证码: <b>{}</b></p></body>
            </html>"""
    CHANGE_BIND_TITLE = "心悦心享-更换绑定"
    CHANGE_BIND_CONTENT = """<html>
            <body>
            <p>你正在更换绑定信息，请注意账号安全，若非本人操作，请忽略此条信息，若存在账号安全问题，请及时修改密码，该验证码15分钟内有效。</p>
            <p>验证码: <b>{}</b></p></body>
            </html>"""
    CHANGE_PASSWORD_TITLE = "心悦心享-修改密码"
    CHANGE_PASSWORD_CONTENT = """<html>
            <body>
            <p>你正在修改密码，请注意账号安全，若非本人操作，请忽略此条信息，若存在账号安全问题，请及时修改密码，该验证码15分钟内有效。</p>
            <p>验证码: <b>{}</b></p></body>
            </html>"""
    RESET_ERROR_LOGIN_TITLE = "心悦心享-登录提醒"
    RESET_ERROR_LOGIN_CONTENT = """<html>
            <body>
            <p>该账户目前因登录错误次数过多被限制登录至{}，在此期间您暂时无法登录，您可找回密码或点击下面链接进行恢复:</p>
            <p>{}</p>
            <p>链接30分钟内有效，如非您本人操作，建议您修改密码。</p>
            </body>
            </html>"""
