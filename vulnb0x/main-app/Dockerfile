FROM python:3.9.9-alpine3.15
WORKDIR /app/vulnb0x
ADD ./ ./
RUN python -m pip install -r ./requirements.txt
RUN mv prod.env .env
RUN apk add --no-cache docker-cli
CMD ["python", "main.py"]