FROM alpine

RUN apk -U add curl-dev gcc musl-dev openssl-dev python3-dev python3 libmagic
RUN pip3 install feedparser jinja2 pycurl eyed3

COPY ./hik /app/hik

RUN mkdir /app/out && \
    echo -e "#!/bin/sh\ncd /app && python3 -m hik fetch && python3 -m hik feed > /app/out/rss.xml" > /etc/periodic/15min/kih-feed && \
    chmod +x /etc/periodic/15min/kih-feed && \
    echo -e "#!/bin/sh\ncd /app && python3 -m hik id3" > /etc/periodic/hourly/kih-downloader && \
    chmod +x /etc/periodic/hourly/kih-downloader && \
    echo -e "#!/bin/sh\ncd /app && python3 -m hik gc" > /etc/periodic/weekly/kih-gc && \
    chmod +x /etc/periodic/weekly/kih-gc

CMD ["/usr/sbin/crond", "-f"]
