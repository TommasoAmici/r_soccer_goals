# build python venv
FROM python:3-alpine as build-python
COPY requirements.txt /
RUN apk update && apk add gcc musl-dev python3-dev libffi-dev openssl-dev cargo
RUN pip install --upgrade pip wheel
RUN pip install --user --prefer-binary -r requirements.txt
ENV PYTHONUNBUFFERED 1


FROM python:3-alpine
COPY --from=build-python /root/.local /root/.local
# Make sure scripts in .local are usable:
ENV PATH=/root/.local/bin:$PATH
COPY main.py teams.py /
CMD ["python", "main.py"]
