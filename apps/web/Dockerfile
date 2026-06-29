FROM python:3.14.6

WORKDIR /data/app

RUN pip install uv -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com

COPY pyproject.toml ./
RUN uv pip install --system --no-cache -r pyproject.toml \
    --index-url http://mirrors.aliyun.com/pypi/simple/ \
    --allow-insecure-host mirrors.aliyun.com

COPY . .

ENTRYPOINT ["sh", "apps/web/start.sh"]
