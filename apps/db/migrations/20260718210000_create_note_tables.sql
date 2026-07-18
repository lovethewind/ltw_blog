use ltw_db;

create table t_note_folder
(
    id              bigint primary key comment '记录id',
    user_id         bigint       not null comment '用户 ID',
    parent_id       bigint comment '父文件夹 ID',
    name            varchar(100) not null comment '文件夹名称',
    sort_order      int          not null default 0 comment '排序',
    is_deleted      bool         not null default false comment '是否在回收站',
    deleted_time    datetime comment '删除时间',
    deleted_root_id bigint comment '删除操作的根文件夹 ID',
    create_time     datetime     not null comment '创建时间',
    update_time     datetime     not null comment '更新时间',
    unique index uk_note_folder_user_parent_name (user_id, parent_id, name),
    index idx_note_folder_user_tree (user_id, is_deleted, parent_id, sort_order, id)
) comment '私人笔记文件夹表';

create table t_note_tag
(
    id          bigint primary key comment '记录id',
    user_id     bigint      not null comment '用户 ID',
    name        varchar(50) not null comment '标签名称',
    create_time datetime    not null comment '创建时间',
    update_time datetime    not null comment '更新时间',
    unique index uk_note_tag_user_name (user_id, name)
) comment '私人笔记标签表';

create table t_note
(
    id                   bigint primary key comment '记录id',
    user_id              bigint       not null comment '用户 ID',
    folder_id            bigint comment '文件夹 ID',
    title                varchar(100) not null default '无标题笔记' comment '标题',
    content              text         not null default ('') comment 'Markdown 内容',
    is_pinned            bool         not null default false comment '是否置顶',
    is_deleted           bool         not null default false comment '是否在回收站',
    deleted_time         datetime comment '删除时间',
    deleted_by_folder_id bigint comment '随文件夹删除的根文件夹 ID',
    create_time          datetime     not null comment '创建时间',
    update_time          datetime     not null comment '更新时间',
    index idx_note_user_list (user_id, is_deleted, is_pinned, update_time, id)
) comment '私人笔记表';

create table t_note_tag_relation
(
    id          bigint primary key comment '记录id',
    note_id     bigint   not null comment '笔记 ID',
    tag_id      bigint   not null comment '标签 ID',
    create_time datetime not null comment '创建时间',
    update_time datetime not null comment '更新时间',
    unique index uk_note_tag_relation_note_tag (note_id, tag_id)
) comment '私人笔记标签关联表';

create table t_note_history
(
    id          bigint primary key comment '记录id',
    note_id     bigint       not null comment '笔记 ID',
    user_id     bigint       not null comment '用户 ID',
    title       varchar(100) not null comment '历史标题',
    content     text         not null comment '历史 Markdown 内容',
    folder_id   bigint comment '历史文件夹 ID',
    tag_ids     json         not null comment '历史标签 ID 列表',
    create_time datetime     not null comment '创建时间',
    update_time datetime     not null comment '更新时间',
    index idx_note_history_note_time (note_id, create_time, id),
    index idx_note_history_user (user_id, note_id)
) comment '私人笔记历史版本表';
