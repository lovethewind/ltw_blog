use ltw_db;

update t_picture_album
set cover = cover_thumb
where cover_thumb <> ''
  and cover_thumb <> cover;

alter table t_picture_album
    drop column cover_thumb;
