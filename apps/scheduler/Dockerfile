FROM python:3.14.6

ENV TZ=Asia/Shanghai

WORKDIR /data/app

RUN pip install uv -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com

COPY pyproject.toml ./
RUN uv pip install --system --no-cache -r pyproject.toml \
    --index-url https://mirrors.aliyun.com/pypi/simple/ \
    --allow-insecure-host mirrors.aliyun.com

COPY . .

ENTRYPOINT ["sh", "apps/scheduler/start.sh"]
