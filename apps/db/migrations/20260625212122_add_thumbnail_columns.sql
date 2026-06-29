use ltw_db;

alter table t_article
    add column cover_thumb varchar(512) not null default '' comment '封面缩略图' after cover;

alter table t_picture
    add column thumb_url varchar(512) not null default '' comment '图片缩略图' after url;
