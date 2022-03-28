FROM python:3.9 as builder

ENV POETRY_VIRTUALENVS_IN_PROJECT="true"

WORKDIR /www/backend

RUN curl -sSL https://install.python-poetry.org | python3

COPY poetry.lock pyproject.toml /www/backend/

RUN ~/.local/bin/poetry install

FROM python:3.9-slim

WORKDIR /www/backend

COPY --from=builder /www/backend/.venv /www/backend/.venv

COPY . /www/backend

ENV PATH="/www/backend/.venv/bin:$PATH"
ENV MODE="production"

EXPOSE 8000

RUN chmod +x start.sh

ENTRYPOINT ["./start.sh"]