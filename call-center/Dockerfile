FROM python:3.9-slim

WORKDIR /app

RUN rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get upgrade -y

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY images/ images/
COPY utils/ utils/
COPY media/ media/
COPY *.py .
COPY *.yaml .

EXPOSE 80

HEALTHCHECK CMD curl --fail http://localhost/_stcore/health || exit 1

ENTRYPOINT [ "uv", "run", "streamlit", "run", "app.py", \
             "--logger.level", "info", \
             "--browser.gatherUsageStats", "false", \
             "--browser.serverAddress", "0.0.0.0", \
             "--server.enableCORS", "false", \
             "--server.enableXsrfProtection", "false", \
             "--server.port", "80"]
