create database ltw_db default character set utf8mb4 collate utf8mb4_unicode_ci;

use ltw_db;

create table t_user
(
    id              bigint primary key comment '记录id',
    uid             bigint       not null comment '用户uid',
    username        varchar(20)  not null unique comment '用户名',
    `password`      varchar(256) not null comment '密码',
    nickname        varchar(20)  not null comment '昵称',
    gender          int          not null default 0 comment '性别(0:保密 1:男 2:女)',
    avatar          varchar(512) not null comment '头像',
    email           varchar(50) unique comment '邮箱',
    mobile          varchar(20) unique comment '手机号',
    wechat          varchar(50) unique comment '微信号',
    register_time   datetime     not null comment '注册时间',
    last_login_time datetime comment '最后登录时间',
    last_login_ip   varchar(20)  not null default '' comment '最后登录IP',
    occupation      varchar(20)  not null default '' comment '职业(头衔)',
    summary         varchar(100) not null default '' comment '个性签名',
    background      varchar(512) not null default '' comment '个人中心背景图',
    address         varchar(100) not null default '' comment '地址',
    is_official     bool         not null default false comment '是否是官方用户',
    user_tag        int          not null default 2 comment '用户标签(0:超级管理员 1:管理员 2:普通用户 3:其他)',
    create_time     datetime     not null comment '创建时间',
    update_time     datetime     not null comment '更新时间',
    unique index unique_username (username),
    unique index unique_uid (uid),
    unique index unique_email (email),
    unique index unique_mobile (mobile),
    unique index unique_wechat (wechat)
) comment '用户表';


create table t_user_restriction
(
    id            bigint primary key comment '记录id',
    user_id       bigint        not null comment '用户id',
    restrict_type int           not null comment '限制类型(1:封禁 2:禁言)',
    start_time    datetime comment '限制开始时间',
    end_time      datetime comment '限制结束时间',
    is_forever    bool          not null default false comment '是否是永久限制',
    reason        varchar(1000) not null default '' comment '限制原因',
    is_cancel     bool          not null default false comment '是否解除',
    cancel_reason varchar(1000) not null default '' comment '解除原因',
    cancel_time   datetime comment '解除时间',
    create_time   datetime      not null comment '创建时间',
    update_time   datetime      not null comment '更新时间',
    index idx_user_id_is_cancel (user_id, is_cancel)
) comment '用户限制表';

create table t_user_settings
(
    id            bigint primary key comment '记录id',
    user_id       bigint        not null comment '用户id',
    setting_key   varchar(50)   not null comment '设置键',
    setting_value varchar(1000) not null comment '设置值',
    create_time   datetime      not null comment '创建时间',
    update_time   datetime      not null comment '更新时间',
    index idx_user_id_setting_key (user_id, setting_key)
) comment '用户配置表';


create table t_role
(
    id            bigint primary key comment '记录id',
    `code`        varchar(20)  not null unique comment '角色标识',
    `name`        varchar(20)  not null comment '角色名称',
    `description` varchar(128) not null default '' comment '角色描述',
    is_active     bool         not null default true comment '是否激活',
    create_time   datetime     not null comment '创建时间',
    update_time   datetime     not null comment '更新时间'
) comment '角色表';

create table t_user_role
(
    id          bigint primary key comment '记录id',
    user_id     bigint   not null comment '用户id',
    role_id     bigint   not null comment '角色id',
    create_time datetime not null comment '创建时间',
    update_time datetime not null comment '更新时间',
    unique index unique_user_role_id (user_id, role_id)
) comment '用户角色表';

create table t_menu
(
    id          bigint primary key comment '记录id',
    parent_id   bigint      not null comment '所属上级',
    `code`      varchar(50) unique comment '权限标识',
    `name`      varchar(20) not null comment '名称',
    menu_type   int         not null comment '类型(0:目录 1:菜单 2:按钮[权限])',
    route_name  varchar(20) not null default '' comment '路由名',
    `path`      varchar(50) not null default '' comment '路由地址',
    component   varchar(50) not null default '' comment '组件路径',
    icon        varchar(50) not null default '' comment '图标',
    hidden      bool        not null default false comment '是否隐藏',
    always_show bool        not null default false comment '总是层级显示',
    is_out_link bool        not null default false comment '是否是外链',
    `index`     int         not null default 100000 comment '排序(越小越在前)',
    is_active   bool        not null default true comment '是否激活',
    create_time datetime    not null comment '创建时间',
    update_time datetime    not null comment '更新时间'
) comment '菜单表';

create table t_role_menu
(
    id          bigint primary key comment '记录id',
    role_id     bigint   not null comment '角色id',
    menu_id     bigint   not null comment '权限(菜单)id',
    create_time datetime not null comment '创建时间',
    update_time datetime not null comment '更新时间',
    unique index unique_role_menu_id (role_id, menu_id)
) comment '角色菜单表';

create table t_article
(
    id           bigint primary key comment '记录id',
    user_id      bigint       not null comment '用户id',
    title        varchar(100) not null comment '标题',
    cover        varchar(512) not null comment '封面',
    category_id  bigint       not null comment '分类id',
    tag_list     json         not null comment '标签列表',
    attach_list  json         not null comment '附件列表',
    content      longtext     not null comment '内容',
    is_markdown  bool         not null default false comment '是否是Markdown格式',
    is_original  bool         not null default true comment '是否是原创',
    original_url varchar(512) not null default '' comment '原文链接',
    `status`     int          not null default 100000 comment '文章状态 1:草稿 2:已发布 3:待审核 4:回收站',
    is_deleted   bool         not null default false comment '是否已删除(实现逻辑删除)',
    edit_time    datetime comment '最后编辑时间',
    create_time  datetime     not null comment '创建时间',
    update_time  datetime     not null comment '更新时间',
    index idx_user_id_is_deleted_status (user_id, is_deleted, status)
) comment '文章表';

create table t_category
(
    id            bigint primary key comment '记录id',
    `name`        varchar(20)   not null comment '分类名',
    `description` varchar(1000) not null comment '描述',
    `index`       int           not null default 100000 comment '排序(越小越在前)',
    is_active     bool          not null default true comment '是否激活',
    create_time   datetime      not null comment '创建时间',
    update_time   datetime      not null comment '更新时间'
) comment '分类表';

create table t_tag
(
    id            bigint primary key comment '记录id',
    parent_id     bigint        not null comment '所属父级',
    `name`        varchar(20)   not null comment '标签名',
    `description` varchar(1000) not null comment '描述',
    `level`       int           not null default 0 comment '层级(1:分类层 2:展示层)',
    `index`       int           not null default 100000 comment '排序(越小越在前)',
    is_active     bool          not null default true comment '是否激活',
    create_time   datetime      not null comment '创建时间',
    update_time   datetime      not null comment '更新时间'
) comment '标签表';

create table t_comment
(
    id             bigint primary key comment '记录id',
    user_id        bigint   not null comment '用户id',
    obj_id         bigint   not null comment '对象id',
    obj_type       int      not null comment '对象类型 1:文章 2:分享',
    parent_id      bigint   not null default 0 comment '父评论id(0:一级评论)',
    reply_user_id  bigint   not null default 0 comment '回复的评论所属用户id',
    first_level_id bigint   not null default 0 comment '一级评论id(0:一级评论), 便于查询',
    content        text     not null comment '评论内容',
    `status`       int      not null default 1 comment '评论状态 1:通过 2:审核中 3:已删除',
    create_time    datetime not null comment '创建时间',
    update_time    datetime not null comment '更新时间',
    index idx_user_id_obj_type_status (user_id, obj_type, status),
    index idx_obj_id_obj_type_status (obj_id, obj_type, status),
    index idx_first_level_id_status (first_level_id, status)
) comment '评论表';

create table t_config
(
    id            bigint primary key comment '记录id',
    `name`        varchar(50)   not null comment '配置key',
    `value`       text          not null comment '配置value',
    `description` varchar(1000) not null default '' comment '配置说明',
    is_active     bool          not null default true comment '是否启用',
    create_time   datetime      not null comment '创建时间',
    update_time   datetime      not null comment '更新时间',
    index idx_name (`name`)
) comment '配置表';

create table t_action
(
    id          bigint primary key comment '记录id',
    user_id     bigint   not null comment '用户id',
    obj_id      bigint   not null comment '点赞对象对象id',
    obj_type    int      not null comment '对象类型 1:文章 2:评论 3:用户',
    action_type int      not null comment '动作类型 1:点赞/喜欢 2:收藏 3:关注 4:访问量',
    `status`    bool     not null default false comment '状态 true:已XX false:未XX',
    create_time datetime not null comment '创建时间',
    update_time datetime not null comment '更新时间',
    index idx_user_id_together (user_id, obj_id, obj_type, action_type)
) comment '行为表';

create table t_action_count
(
    id          bigint primary key comment '记录id',
    obj_id      bigint   not null comment '点赞对象对象id',
    obj_type    int      not null comment '对象类型 1:文章 2:评论 3:用户',
    action_type int      not null comment '动作类型 1:点赞 2:喜欢 3:收藏 4:关注 5:访问量',
    count       int      not null default 0 comment '统计数量',
    create_time datetime not null comment '创建时间',
    update_time datetime not null comment '更新时间',
    index idx_obj_id_together (obj_id, obj_type, action_type)
) comment '行为统计表';


create table t_job
(
    id              bigint primary key comment '任务id',
    `name`          varchar(64)   not null comment '任务名称',
    `group`         varchar(64)   not null default 'DEFAULT' comment '任务组名',
    invoke_target   varchar(500)  not null comment '调用目标字符串',
    cron_expression varchar(255)  not null comment 'cron执行表达式',
    misfire_policy  tinyint       not null default 3 comment '计划执行策略（1:立即执行 2:执行一次 3:放弃执行）',
    concurrent      bool          not null default false comment '是否并发执行',
    `status`        tinyint       not null default 1 comment '状态（1:正常 2:暂停）',
    create_user_id  bigint        not null comment '创建者',
    update_user_id  bigint comment '更新者',
    `description`   varchar(1000) not null default '' comment '备注信息',
    create_time     datetime      not null comment '创建时间',
    update_time     datetime      not null comment '更新时间'
) comment '定时任务表';

create table t_link
(
    id          bigint primary key comment '记录id',
    `name`      varchar(100)  not null comment '网站名',
    cover       varchar(300)  not null comment '封面',
    introduce   varchar(1000) not null comment '简介',
    url         varchar(100)  not null comment 'url',
    email       varchar(100)  not null default '' comment '联系人邮箱',
    `index`     int           not null default 100000 comment '排序',
    `status`    int           not null default 2 comment '审核状态: 1: 已通过 2:审核中 3:拒绝',
    description varchar(1000) not null comment '说明',
    create_time datetime      not null comment '创建时间',
    update_time datetime      not null comment '更新时间'
) comment '友情链接表';

create table t_message
(
    id             bigint primary key comment '记录id',
    user_id        bigint       not null default 0 comment '用户id',
    avatar         varchar(300) comment '头像',
    nickname       varchar(30) comment '昵称',
    email          varchar(100) comment '联系人邮箱',
    content        mediumtext   not null comment '留言内容',
    address        varchar(100) not null default '' comment '地址',
    parent_id      bigint       not null default 0 comment '父评论id(0:一级评论)',
    reply_user_id  bigint       not null default 0 comment '回复的留言所属用户id',
    first_level_id bigint       not null default 0 comment '一级评论id(0:一级评论), 便于查询',
    create_time    datetime     not null comment '创建时间',
    update_time    datetime     not null comment '更新时间',
    index idx_first_level_id (first_level_id)
) comment '留言表';

create table t_picture
(
    id          bigint primary key comment '记录id',
    user_id     bigint       not null comment '用户id',
    album_id    bigint       not null comment '图册id',
    description varchar(200) not null comment '图片描述',
    url         varchar(512) not null comment '图片地址',
    size        int          not null default 0 comment '图片大小',
    width       int          not null default 0 comment '图片宽度',
    height      int          not null default 0 comment '图片高度',
    status      int          not null default 1 comment '状态 1:已通过 2:审核中 3:拒绝',
    create_time datetime     not null comment '创建时间',
    update_time datetime     not null comment '更新时间',
    index idx_user_id_status (user_id, status),
    index idx_album_id_status (album_id, status)
) comment '图片表';

create table t_picture_album
(
    id          bigint primary key comment '记录id',
    user_id     bigint       not null comment '用户id',
    name        varchar(20)  not null comment '图册名',
    description varchar(200) not null comment '图册描述',
    cover       varchar(512) not null comment '图册封面',
    status      int          not null default 1 comment '状态 1:已通过 2:审核中 3:拒绝',
    album_type  int          not null default 2 comment '类型 1公开 2私密',
    create_time datetime     not null comment '创建时间',
    update_time datetime     not null comment '更新时间',
    index idx_user_id_status (user_id, status),
    index idx_album_type_status (album_type, status)
) comment '图库分类表';

create table t_website
(
    id          bigint primary key comment '记录id',
    user_id     bigint        not null comment '用户id',
    `name`      varchar(100)  not null comment '网站名',
    category_id bigint        not null comment '分类id',
    cover       varchar(300)  not null comment '封面',
    introduce   varchar(1000) not null comment '简介',
    url         varchar(100)  not null comment 'url',
    `index`     int           not null default 100000 comment '排序',
    `status`    int           not null default 1 comment '审核状态: 1: 已通过 2:审核中 3:拒绝',
    create_time datetime      not null comment '创建时间',
    update_time datetime      not null comment '更新时间',
    index idx_status (status)
) comment '网站导航表';

create table t_website_category
(
    id          bigint primary key comment '记录id',
    `name`      varchar(100) not null comment '分类名',
    `index`     int          not null default 100000 comment '排序',
    create_time datetime     not null comment '创建时间',
    update_time datetime     not null comment '更新时间'
) comment '网站导航分类表';

create table t_source
(
    id          bigint primary key comment '记录id',
    user_id     bigint       not null comment '用户id',
    url         varchar(256) not null comment 'url',
    is_deleted  bool         not null default false comment '是否已删除(实现逻辑删除)',
    create_time datetime     not null comment '创建时间',
    update_time datetime     not null comment '更新时间',
    index idx_user_id_url (user_id, url)
) comment '资源表';

create table t_share
(
    id          bigint primary key comment '记录id',
    user_id     bigint     not null comment '用户id',
    content     mediumtext not null comment '内容',
    share_type  int        not null comment '分享类型 1：笔记 2：生活 3：经验 4：音乐 5：视频 6：资源 7：其他',
    tag         json       not null comment '标签',
    detail      json       not null comment '详情',
    `status`    int        not null default 1 comment '审核状态: 1: 已通过 2:审核中 3:拒绝',
    create_time datetime   not null comment '创建时间',
    update_time datetime   not null comment '更新时间',
    index idx_user_id_status_share_type (user_id, status, share_type)
) comment '分享表';

create table t_notice
(
    id          bigint primary key comment '记录id',
    user_id     bigint       not null comment '用户id',
    title       varchar(255) not null comment '标题',
    content     mediumtext   not null comment '内容',
    notice_type int          not null comment '消息类型 1: 系统 2: 评论 3:回复(评论) 4: @我 5: 点赞 6: 收藏 7: 关注',
    is_read     bool         not null default false comment '是否已读',
    detail      json         not null comment '详情',
    create_time datetime     not null comment '创建时间',
    update_time datetime     not null comment '更新时间',
    index idx_user_id_notice_type (user_id, notice_type)
) comment '通知消息表';

create table t_contact
(
    id           bigint primary key comment '记录id',
    user_id      bigint   not null comment '用户id',
    contact_id   bigint   not null comment '联系人id',
    contact_type int      not null comment '联系人类型 1: 用户 2: 群组',
    create_time  datetime not null comment '创建时间',
    update_time  datetime not null comment '更新时间',
    index idx_user_id_contact_type (user_id, contact_type)
) comment '联系人表';

create table t_conversation
(
    id              bigint primary key comment '记录id',
    user_id         bigint      not null comment '用户id',
    contact_id      bigint      not null comment '联系人id',
    contact_type    int         not null comment '联系人类型 1: 用户 2: 群组',
    conversation_id varchar(64) not null comment '会话id',
    unread_count    int         not null default 0 comment '未读消息数量',
    is_pinned       bool        not null default false comment '是否置顶',
    is_muted        bool        not null default false comment '是否静音',
    is_clear        bool        not null default false comment 'is_clear',
    last_clear_time datetime comment '上次清空时间',
    last_view_time  datetime comment '上次查看时间',
    create_time     datetime    not null comment '创建时间',
    update_time     datetime    not null comment '更新时间',
    index idx_user_id_is_clear (user_id, is_clear)
) comment '会话表';

create table t_chat_message
(
    id              bigint primary key comment '记录id',
    user_id         bigint         not null comment '用户id',
    contact_id      bigint         not null comment '联系人id',
    contact_type    int            not null comment '联系人类型 1: 用户 2: 群组',
    conversation_id varchar(64)    not null comment '会话id',
    content         varchar(10000) not null comment '消息内容',
    message_type    int            not null comment '消息类型 1: 系统 2: 文本 3:图片 4：语言 5:视频 6:文件 7:回复 8: @用户',
    attach          json comment '附件列表',
    read_list       json           not null comment '已读用户列表',
    delete_list     json           not null comment '已删除用户列表',
    create_time     datetime       not null comment '创建时间',
    update_time     datetime       not null comment '更新时间',
    index idx_user_id_conversation_id (user_id, conversation_id),
    index idx_conversation_id_create_time (conversation_id, create_time)
) comment '聊天消息表';

create table t_chat_group
(
    id          bigint primary key comment '记录id',
    user_id     bigint        not null comment '用户id',
    name        varchar(32)   not null comment '群名称',
    avatar      varchar(512)  not null comment '群头像',
    notice      varchar(1000) not null comment '群公告',
    description varchar(1000) not null comment '群描述',
    group_type  int           not null comment '群组类型 1: 私密 2: 公开',
    create_time datetime      not null comment '创建时间',
    update_time datetime      not null comment '更新时间',
    index idx_user_id (user_id)
) comment '群组表';

create table t_chat_group_member
(
    id          bigint primary key comment '记录id',
    group_id    bigint        not null comment '群id',
    user_id     bigint        not null comment '用户id',
    role        int           not null comment '成员角色 1:管理员 2:普通成员',
    join_type   int           not null comment '加入方式 1:搜索群 2:邀请',
    remark      varchar(1000) not null default '' comment '加入详情',
    is_muted    bool          not null default false comment '是否被禁言',
    create_time datetime      not null comment '创建时间',
    update_time datetime      not null comment '更新时间',
    index idx_group_id_user_id (group_id, user_id)
) comment '群成员表';

create table t_contact_apply_record
(
    id           bigint primary key comment '记录id',
    user_id      bigint       not null comment '用户id',
    contact_id   bigint       not null comment '联系人id',
    contact_type int          not null comment '联系人类型 1: 用户 2: 群组',
    content      varchar(500) not null comment '申请消息内容',
    status       int          not null comment '申请状态 1: 等待处理 2: 已同意 3: 已拒绝',
    create_time  datetime     not null comment '创建时间',
    update_time  datetime     not null comment '更新时间',
    index idx_user_id_contact_id (user_id, contact_id)
) comment '好友申请记录表';