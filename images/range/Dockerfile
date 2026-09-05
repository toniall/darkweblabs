# Unlock the Secrets of the DARK WEB, Volume 2 | Antonio Brandao, Author | August 2026
# Chapter 8 · Simulated darknet range — onion publisher + content generator.
# Generates the synthetic, watermarked range content (seed.py, mounted at
# /opt/seed.py) and publishes one v3 onion per service. Static-checked in this
# book's build; ./lab check 8.1 confirms it on a Docker host.
FROM alpine:3.20

RUN apk add --no-cache tor python3 \
    && mkdir -p /var/lib/tor /content \
    && chown -R tor:tor /var/lib/tor

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# seed.py is bind-mounted at /opt/seed.py by compose (single source of truth in
# labs/artifacts/range-content), so there is no duplicated copy to drift.
ENV RANGE_SEED_DIR=/content
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
