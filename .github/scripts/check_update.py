"""Compare Caddy's latest stable release with a successfully published GHCR tag."""

import base64
import json
import os
import re
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def get_json(url, headers):
    request = Request(url, headers={"User-Agent": "caddy-tencentcloud", **headers})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def latest_version(token):
    release = get_json(
        "https://api.github.com/repos/caddyserver/caddy/releases/latest",
        {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    )
    tag = release.get("tag_name", "")
    if release.get("draft") or release.get("prerelease") or not re.fullmatch(
        r"v[0-9]+\.[0-9]+\.[0-9]+", tag
    ):
        raise ValueError(f"Expected a stable Caddy release, got {tag!r}")
    return tag[1:]


def image_exists(repository, version, actor, token):
    credentials = base64.b64encode(f"{actor}:{token}".encode()).decode()
    query = urlencode({"service": "ghcr.io", "scope": f"repository:{repository}:pull"})
    auth = get_json(
        f"https://ghcr.io/token?{query}",
        {"Authorization": f"Basic {credentials}"},
    )
    registry_token = auth.get("token") or auth.get("access_token")
    if not registry_token:
        raise ValueError("GHCR did not return a registry token")
    request = Request(
        f"https://ghcr.io/v2/{repository}/manifests/{version}",
        method="HEAD",
        headers={
            "Authorization": f"Bearer {registry_token}",
            "Accept": ", ".join(
                [
                    "application/vnd.oci.image.index.v1+json",
                    "application/vnd.oci.image.manifest.v1+json",
                    "application/vnd.docker.distribution.manifest.list.v2+json",
                    "application/vnd.docker.distribution.manifest.v2+json",
                ]
            ),
        },
    )
    try:
        with urlopen(request, timeout=30):
            return True
    except HTTPError as error:
        if error.code == 404:
            return False
        # Authentication failures and outages must not be mistaken for "up to date".
        raise


def main():
    token = os.environ["GH_TOKEN"]
    repository = os.environ["GITHUB_REPOSITORY"].lower()
    version = latest_version(token)
    force = os.environ.get("FORCE_REBUILD", "false").lower() == "true"
    should_build = force or not image_exists(
        repository, version, os.environ["GITHUB_ACTOR"], token
    )
    image = f"ghcr.io/{repository}"
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"version={version}\nimage={image}\nshould_build={str(should_build).lower()}\n")
    message = (
        f"Caddy {version}: build and publish `{image}:{version}`."
        if should_build
        else f"Caddy {version} is already published; skipping the build."
    )
    print(message)
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
        summary.write(message + "\n")


if __name__ == "__main__":
    main()
