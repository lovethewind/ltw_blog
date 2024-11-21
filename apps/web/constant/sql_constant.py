# @Time    : 2024/10/14 15:29
# @Author  : frank
# @File    : sql_constant.py

class SqlConstant:
    # 查出每条第一级评论的二级评论，默认前3条
    FIRST_LEVEL_COMMENT_3_CHILDREN_COMMENT = """
                SELECT *
                FROM (
                    SELECT *,
                           ROW_NUMBER() OVER (PARTITION BY first_level_id ORDER BY id DESC) as row_num
                    FROM t_comment
                    WHERE obj_id = %s AND obj_type = %s AND first_level_id in %s AND status = %s
                ) subquery
                WHERE row_num <= 3;
            """

    # 查出每条第一级留言的二级留言，默认前3条
    FIRST_LEVEL_MESSAGE_3_CHILDREN_MESSAGE = """
                SELECT *
                FROM (
                    SELECT *,
                           ROW_NUMBER() OVER (PARTITION BY first_level_id ORDER BY id DESC) as row_num
                    FROM t_message
                    WHERE first_level_id in %s
                ) subquery
                WHERE row_num <= 3;
            """

    # 查询会话最后一条消息
    CONVERSATION_LAST_MESSAGE_LIST = """
                    SELECT *
                    FROM (
                        SELECT tcm.*,
                               ROW_NUMBER() OVER (PARTITION BY tcm.conversation_id ORDER BY tcm.id DESC) as row_num
                        FROM t_chat_message tcm, (VALUES %s) tp(conversation_id, create_time)
                        WHERE tcm.conversation_id = tp.conversation_id and tcm.create_time > tp.create_time
                    ) subquery
                    WHERE row_num <= 1;
                """