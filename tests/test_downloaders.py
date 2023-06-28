#
# If not stated otherwise in this file or this component's LICENSE file the
# following copyright and licenses apply:
#
# Copyright 2023 Liberty Global Technology Services BV
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Test cases for Downloader class hierarchy."""
from unittest import (
    mock,
    TestCase,
)

from service.downloaders import (
    Downloader,
    S3Downloader,
)


class TestDownloader(TestCase):
    """Base TestCase for Downloader classes."""

    def setUp(self) -> None:
        """Set up env before each test."""
        self.config_mock = mock.MagicMock(name="Config")

    def test_abstract_methods(self) -> None:
        """Test set of abstract methods in class."""
        self.assertSetEqual(set(["download"]), Downloader.__dict__["__abstractmethods__"])

    @mock.patch("service.downloaders.client")
    @mock.patch("service.downloaders.os.environ.get")
    def test_s3downloader_initialization(self, os_get_mock: mock.MagicMock, client_mock: mock.MagicMock) -> None:
        """Test S3Downloader initialization."""
        downloader = S3Downloader(self.config_mock)

        self.assertEqual(downloader.config, self.config_mock)
        self.config_mock.get.assert_called_once_with("storage.type")
        os_get_mock.assert_called_once_with("S3_REGION")
        client_mock.assert_called_once_with(self.config_mock.get(), region_name=os_get_mock())

    @mock.patch("service.downloaders.os")
    @mock.patch("service.downloaders.client")
    def test_s3downloader_download(self, client_mock: mock.MagicMock, os_mock: mock.MagicMock) -> None:
        """Test S3Downloader `download()`."""
        S3Downloader(self.config_mock).download("path", "filename")

        os_mock.path.join.assert_called_once_with("path", "filename")
        os_mock.environ.get.assert_has_calls(
            [
                mock.call("S3_REGION"),
                mock.call("S3_BUCKET"),
            ],
        )
        self.config_mock.get.assert_has_calls(
            [
                mock.call("storage.type"),
            ],
        )
        client_mock().download_file.assert_called_once_with(
            os_mock.environ.get(),
            "filename",
            os_mock.path.join(),
        )
