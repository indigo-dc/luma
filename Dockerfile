FROM alpine:3.6

RUN apk add --no-cache python3 \
    && python3 -m ensurepip \
    && rm -r /usr/lib/python*/ensurepip \ 
    && pip3 install --upgrade pip setuptools \
    && if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi \
    && rm -r /root/.cache \
    && pip3 install connexion tinydb

COPY ./luma /luma

WORKDIR /luma
CMD ["python3", "app.py"]
