# caddy-tencentcloud

Caddy Docker image with the Tencent Cloud DNS module:

- Base image: `caddy:latest`
- Builder image: `caddy:builder`
- Plugin: `github.com/caddy-dns/tencentcloud`
- Target platform: `linux/amd64`

The GitHub Actions workflow builds and pushes:

- `ghcr.io/kevincible/caddy-tencentcloud:latest`
- `ghcr.io/kevincible/caddy-tencentcloud:<commit-sha>`

Pull and run locally:

```sh
docker pull ghcr.io/kevincible/caddy-tencentcloud:latest
docker run --rm ghcr.io/kevincible/caddy-tencentcloud:latest caddy version
```
