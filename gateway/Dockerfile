FROM debian:bookworm-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends stunnel4 ca-certificates && \
    rm -rf /var/lib/apt/lists/*
COPY stunnel.conf /etc/stunnel/stunnel.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 802
ENTRYPOINT ["/entrypoint.sh"]