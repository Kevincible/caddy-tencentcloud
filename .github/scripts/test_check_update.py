import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

import check_update


class UpdateCheckTests(unittest.TestCase):
    def test_only_stable_release_is_accepted(self):
        cases = [
            ({"tag_name": "v2.11.9", "draft": False, "prerelease": False}, "2.11.9"),
            ({"tag_name": "v2.12.0-rc.1"}, None),
            ({"tag_name": "v2.12.0", "prerelease": True}, None),
            ({"tag_name": "v2.12.0", "draft": True}, None),
            ({"tag_name": "v2.11.9\nshould_build=false"}, None),
            ({"tag_name": "latest"}, None),
            ({}, None),
        ]
        for release, expected in cases:
            with self.subTest(release=release), patch.object(check_update, "get_json", return_value=release):
                if expected:
                    self.assertEqual(check_update.latest_version("test-token"), expected)
                else:
                    with self.assertRaises(ValueError):
                        check_update.latest_version("test-token")

    @patch.object(check_update, "get_json", return_value={"token": "registry-token"})
    @patch.object(check_update, "urlopen")
    def test_existing_image_uses_authenticated_manifest_request(self, urlopen, get_json):
        urlopen.return_value = MagicMock()
        self.assertTrue(check_update.image_exists("owner/image", "2.11.9", "owner", "test-token"))
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://ghcr.io/v2/owner/image/manifests/2.11.9")
        self.assertEqual(request.method, "HEAD")
        self.assertEqual(request.get_header("Authorization"), "Bearer registry-token")
        self.assertIn("application/vnd.oci.image.index.v1+json", request.get_header("Accept"))

    def test_only_manifest_404_means_missing_image(self):
        for status in (404, 401, 403, 429, 500, 503):
            error = HTTPError("https://ghcr.io/v2/owner/image/manifests/2.11.9", status, "test", {}, None)
            with self.subTest(status=status), patch.object(check_update, "get_json", return_value={"token": "test"}), patch.object(check_update, "urlopen", side_effect=error):
                if status == 404:
                    self.assertFalse(check_update.image_exists("owner/image", "2.11.9", "owner", "test-token"))
                else:
                    with self.assertRaises(HTTPError):
                        check_update.image_exists("owner/image", "2.11.9", "owner", "test-token")

    def test_registry_auth_failure_is_not_a_missing_image(self):
        error = HTTPError("https://ghcr.io/token", 403, "test", {}, None)
        with patch.object(check_update, "get_json", side_effect=error):
            with self.assertRaises(HTTPError):
                check_update.image_exists("owner/image", "2.11.9", "owner", "test-token")
        with patch.object(check_update, "get_json", return_value={}):
            with self.assertRaises(ValueError):
                check_update.image_exists("owner/image", "2.11.9", "owner", "test-token")

    def test_network_failure_is_not_a_missing_image(self):
        with patch.object(check_update, "get_json", return_value={"token": "test"}), patch.object(check_update, "urlopen", side_effect=URLError("offline")):
            with self.assertRaises(URLError):
                check_update.image_exists("owner/image", "2.11.9", "owner", "test-token")

    def test_build_skip_and_force_outputs(self):
        for exists, force, expected in [(True, "false", "false"), (False, "false", "true"), (True, "true", "true")]:
            with self.subTest(exists=exists, force=force), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "output"
                summary = Path(directory) / "summary"
                env = {
                    "GH_TOKEN": "test-token",
                    "GITHUB_REPOSITORY": "Kevincible/caddy-tencentcloud",
                    "GITHUB_ACTOR": "Kevincible",
                    "FORCE_REBUILD": force,
                    "GITHUB_OUTPUT": str(output),
                    "GITHUB_STEP_SUMMARY": str(summary),
                }
                with patch.dict(os.environ, env), patch.object(check_update, "latest_version", return_value="2.11.9"), patch.object(check_update, "image_exists", return_value=exists) as check, patch("sys.stdout", new_callable=io.StringIO):
                    check_update.main()
                self.assertEqual(output.read_text(), f"version=2.11.9\nimage=ghcr.io/kevincible/caddy-tencentcloud\nshould_build={expected}\n")
                self.assertIn("2.11.9", summary.read_text())
                if force == "true":
                    check.assert_not_called()

    def test_release_failure_writes_no_build_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            with patch.dict(os.environ, {"GH_TOKEN": "test", "GITHUB_REPOSITORY": "owner/image", "GITHUB_OUTPUT": str(output)}), patch.object(check_update, "latest_version", side_effect=URLError("offline")):
                with self.assertRaises(URLError):
                    check_update.main()
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
