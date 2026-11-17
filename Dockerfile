ARG CADDY_VERSION=2

FROM caddy:${CADDY_VERSION}-builder AS builder

# The official builder sets CADDY_VERSION to its exact release for xcaddy.
RUN xcaddy build \
    --with github.com/caddy-dns/tencentcloud

FROM caddy:${CADDY_VERSION}

COPY --from=builder /usr/bin/caddy /usr/bin/caddy
