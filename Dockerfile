FROM alpine

RUN apk -U add curl-dev gcc musl-dev openssl-dev python3-dev python3
RUN pip3 install feedparser jinja2 pycurl

RUN echo -e "#!/bin/sh\ncd /app && python -m kih fetch && python -m kih feed > /app/out/rss.xml" > /etc/periodic/15min/kih-feed && chmod +x /etc/periodic/15min/kih-feed
CMD ["/usr/sbin/crond", "-f"]
