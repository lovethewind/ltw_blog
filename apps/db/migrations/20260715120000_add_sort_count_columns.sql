use ltw_db;

alter table t_article
    add column hot_score decimal(20, 6) not null default 0 comment '热门分数' after status,
    add column recommend_score decimal(20, 6) not null default 0 comment '推荐分数' after hot_score,
    add column recommend_weight int not null default 0 comment '人工推荐权重' after recommend_score;

alter table t_article
    add index idx_article_hot_sort (is_deleted, status, hot_score desc, id desc),
    add index idx_article_recommend_sort (is_deleted, status, recommend_score desc, id desc);

alter table t_picture
    add column like_count bigint not null default 0 comment '点赞量' after height,
    add column comment_count bigint not null default 0 comment '评论量' after like_count;

update t_picture as picture
left join (
    select obj_id, max(`count`) as like_count
    from t_action_count
    where obj_type = 5
      and action_type = 1
    group by obj_id
) as action_count on action_count.obj_id = picture.id
set picture.like_count = greatest(coalesce(action_count.like_count, 0), 0);

update t_picture as picture
left join (
    select obj_id, count(id) as comment_count
    from t_comment
    where obj_type = 5
      and status = 1
    group by obj_id
) as comment_count on comment_count.obj_id = picture.id
set picture.comment_count = coalesce(comment_count.comment_count, 0);

alter table t_picture
    add index idx_picture_like_sort (status, album_id, like_count desc, id desc),
    add index idx_picture_comment_sort (status, album_id, comment_count desc, id desc);
