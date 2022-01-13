FROM python:3.9.9-alpine3.15
WORKDIR /app/vulnb0x

RUN apk add --no-cache build-base libffi-dev && \
    apk add --no-cache openssh git

RUN mkdir ~/.ssh/ && \
    touch ~/.ssh/known_hosts && \
    chmod 700 ~/.ssh && \
    chmod 644 ~/.ssh/known_hosts

RUN ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts && \
    ssh-keyscan -t rsa gitlab.com >> ~/.ssh/known_hosts

ADD ./ ./

RUN mv prod.env .env
RUN python3 -m pip install -r ./requirements.txt --ignore-installed

CMD ["python", "main.py"]