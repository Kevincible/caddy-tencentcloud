# caddy-tencentcloud

Caddy Docker image with the Tencent Cloud DNS module:

- Plugin: `github.com/caddy-dns/tencentcloud`
- Target platform: `linux/amd64`
- Registry: `ghcr.io/kevincible/caddy-tencentcloud`

## Automatic updates

The **Build Docker image** workflow checks the latest stable release of
[`caddyserver/caddy`](https://github.com/caddyserver/caddy/releases) every Monday
at **09:17 Asia/Shanghai (01:17 UTC)**. GitHub may delay scheduled runs.
Prereleases are excluded.

If that version's image tag is already in GHCR, the build is skipped. Otherwise,
the workflow uses the matching `caddy:<version>-builder` and `caddy:<version>`
images, compiles the Tencent Cloud DNS module, and verifies both the Caddy
version and `dns.providers.tencentcloud` before publishing:

- `ghcr.io/kevincible/caddy-tencentcloud:latest`
- `ghcr.io/kevincible/caddy-tencentcloud:<caddy-version>` (for example, `2.11.9`)
- `ghcr.io/kevincible/caddy-tencentcloud:<commit-sha>` (existing compatibility tag)

The version tag is pushed last and serves as the successful-publication marker.
A failed build or publish is retried by the next weekly check. API or registry
errors fail the workflow instead of silently reporting that no update is needed.
If Caddy has released a version before its official Docker images are available,
the build fails and can be retried once those images are published.

Changes to the Dockerfile or build workflow/scripts on `main` also rebuild the
latest stable version. To check immediately, open **Actions → Build Docker image
→ Run workflow** on `main`. Enable **force** to rebuild an already published
version, for example to refresh the DNS plugin or base images. Plugin-only and
base-image-only updates do not trigger the weekly build.

Publishing uses the repository's built-in `GITHUB_TOKEN`; no PAT or Tencent Cloud
credentials are needed to build. The check job has `packages: read`, and the
build job has `packages: write`. The GHCR package must grant this repository
Actions access, as with the original publishing workflow.

GitHub [disables scheduled workflows in public repositories after 60 days of
inactivity](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).
On scheduled runs, a separate job with `contents: write` creates an empty
keepalive commit only when the default branch has had no commits for 45 days.
This changes no files and does not trigger another build. If branch protection
is enabled later, it must allow this job's commit or the schedule must be kept
active manually.

## Pull and run

```sh
docker pull ghcr.io/kevincible/caddy-tencentcloud:latest
docker run --rm ghcr.io/kevincible/caddy-tencentcloud:latest caddy version
docker run --rm ghcr.io/kevincible/caddy-tencentcloud:latest caddy list-modules
```

To select a Caddy release explicitly, replace `latest` with its version tag.
The `latest` and commit-SHA tags can change across scheduled builds; use an image
digest when an immutable reference is required. Publishing a new image does not
restart an existing container: pull the image and recreate your container, or
use your existing deployment updater.

## Local build

```sh
docker build --build-arg CADDY_VERSION=2.11.9 -t caddy-tencentcloud .
```

Without a build argument, the Dockerfile uses the current Caddy 2 images.

Run the update-detection tests without network access:

```sh
python3 -m unittest discover -s .github/scripts -p 'test_*.py'
```
