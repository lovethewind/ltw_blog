# ltw_blog
心悦心享博客

## 本地环境

项目使用 `uv` 管理 Python 环境和依赖，Python 版本为 `3.12.7`。

```bash
uv sync
uv run gunicorn -c apps/web/config.py apps.web.run:create_app
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
