FROM python:3.8-slim
RUN apt-get update && apt-get install curl git -y

ARG HOME_DIR=/usr/local/bundlegenuser

RUN groupadd --gid 1000 bundlegenuser \
    && useradd -ms /bin/bash -d ${HOME_DIR} bundlegenuser -u 1000 -g 1000

WORKDIR /service
COPY . .
RUN chown -R bundlegenuser:bundlegenuser . && chmod +x ./entrypoint.sh

USER bundlegenuser
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH ${HOME_DIR}/.local/bin:$PATH

RUN poetry install --no-dev --no-root
ENTRYPOINT [ "./entrypoint.sh" ]
