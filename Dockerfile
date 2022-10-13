# build python venv
FROM python:3.10.8-alpine as build-python
RUN apk update && apk add --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev cargo
RUN pip install --no-cache-dir --upgrade pip wheel
COPY requirements.txt /
RUN pip install --no-cache-dir --user --prefer-binary -r requirements.txt

FROM python:3.10.8-alpine
COPY --from=build-python /root/.local /root/.local
# Make sure scripts in .local are usable:
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED 1
COPY main.py teams.py /
CMD ["python", "main.py"]
