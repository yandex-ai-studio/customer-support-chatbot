FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"

RUN apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY ./pyproject.toml ./entrypoint.sh ./uv.lock* ./
COPY ./app ./app

RUN chmod +x entrypoint.sh
RUN uv sync --frozen --no-dev

ENTRYPOINT ["sh",  "./entrypoint.sh"]