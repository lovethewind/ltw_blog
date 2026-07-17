# ltw_blog
心悦心享博客

## 本地环境

项目使用 `uv` 管理 Python 环境和依赖，Python 版本为 `3.12.7`。

```bash
uv sync
uv run gunicorn -c apps/web/gunicorn_config.py "apps.web.run:create_app()"
```

服务监听地址从配置读取，默认配置在 `apps/web/resources/bootstrap.yaml` 的 `app.server.host` 和 `app.server.port`，Nacos 中同名配置会覆盖默认值。

1.构建镜像
```bash
#!/usr/bash

project=ltw_web
version=0.0.1

echo "git pull"
git pull

echo "start docker build ${project}:${version}"
docker buildx build -f apps/web/Dockerfile -t lovethewind/${project}:${version} . --load
echo "build success"
```

Docker 镜像会在构建阶段通过 `uv pip install --system` 安装依赖，容器启动时只启动服务，不再创建或同步虚拟环境。

2.部署
```bash
docker run -d -p 8001:8001 --name ltw_web lovethewind/ltw_web:0.0.1
```

## IK 动态词库

管理端“配置管理 → 搜索配置”支持维护 IK 自定义词、ES 停用词和热搜停用词。ES 节点需要在 `IKAnalyzer.cfg.xml` 中进行一次性配置：

```xml
<entry key="remote_ext_dict">http://ltw-web:8001/api/config/common/search-analysis/dictionary/custom</entry>
<entry key="remote_ext_stopwords">http://ltw-web:8001/api/config/common/search-analysis/dictionary/stop</entry>
```

词库接口返回 UTF-8 纯文本以及 `ETag`、`Last-Modified` 响应头。管理端发布新版本后，IK 会在轮询发现版本变化时加载新词库。

发布只更新词库，不会修改历史文章已经写入 ES 的 token。需要让历史文章按新词库重新分词时，再由管理员点击“重建文章索引”。重建过程先写入新的 `article_v*` 物理索引，写入完成后再把 `article` 读写别名切换到新索引。
