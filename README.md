# ltw_blog
心悦心享博客

1.构建镜像
```bash
#!/usr/bash

project=ltw_web
version=0.0.1

echo "git pull"
git pull

echo "start docker build ${project}:${version}"
docker buildx build -f Dockerfile -t lovethewind/${project}:${version} . --load
echo "build success"
```

2.部署
```bash
docker run -d -p 8080:8080 --name ltw_web lovethewind/ltw_web:0.0.1
```