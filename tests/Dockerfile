# This Dockerfile is intentionally well-formed: it is used by the CI test suite
# to verify that `hadolint` can be invoked and exits 0 on a clean file.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "myapp"]
