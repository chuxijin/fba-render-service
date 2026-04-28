FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    fontconfig \
    fonts-noto-cjk \
    latexmk \
    perl \
    texlive-base \
    texlive-fonts-recommended \
    texlive-lang-chinese \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-latex-recommended \
    texlive-pictures \
    texlive-science \
    texlive-xetex \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY render_service/requirements.txt /tmp/render-service-requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --extra-index-url https://pypi.org/simple \
    && pip install -r /tmp/render-service-requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --extra-index-url https://pypi.org/simple \
    --timeout 120 \
    --retries 10

COPY render_service /app/render_service
COPY deploy/render-book/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    && mkdir -p /data/output /data/workdir

EXPOSE 9000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "render_service.app.main:app", "--host", "0.0.0.0", "--port", "9000"]

