# build python venv
FROM python:3.11-alpine AS build-python
RUN apk update && apk add --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev cargo \
    py3-brotli brotli brotli-dev brotli-libs g++
RUN pip install --no-cache-dir --upgrade pip wheel
COPY requirements.txt /
RUN pip install --no-cache-dir --user --prefer-binary -r requirements.txt

FROM python:3.11-alpine
COPY --from=build-python /root/.local /usr/local
# Make sure scripts in /usr/local/bin are usable:
ENV PATH=/usr/local/bin:$PATH
ENV PYTHONUNBUFFERED=1
RUN mkdir -p /data
# TODO make src/ directory
WORKDIR /app
COPY main.py teams.py .
USER nobody:nobody
CMD ["python", "main.py"]
