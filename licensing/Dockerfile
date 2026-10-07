FROM python:3.12-slim
WORKDIR /app
COPY licensing/requirements.txt licensing/requirements.txt
RUN pip install --no-cache-dir -r licensing/requirements.txt \
    && useradd --uid 10001 --create-home planner \
    && mkdir -p /data && chown planner:planner /data
COPY index.html ./index.html
COPY assets ./assets
COPY licensing ./licensing
USER planner
ENV LED_DATABASE=/data/ledplanner.sqlite LED_BIND=0.0.0.0 PORT=8000
EXPOSE 8000
CMD ["python", "-m", "licensing.run"]
