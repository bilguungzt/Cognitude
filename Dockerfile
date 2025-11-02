Dockerfile
# First stage - install dependencies
FROM python:3.11-slim as builder
WORKDIR /install
COPY pyproject.toml poetry.lock ./
RUN pip install --upgrade pip && pip install poetry
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

# Second stage - create runtime environment
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /install/.venv/lib/python3.11/site-packages /app
COPY app /app
RUN pip install uvicorn[standard]
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
