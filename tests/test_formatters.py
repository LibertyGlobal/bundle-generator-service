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

"""Test cases for Formatter class hierarchy."""
from unittest import (
    mock,
    TestCase,
)

from service.formatter import (
    BundleGenFormatter,
    Formatter,
)


class TestFormatter(TestCase):
    """Base TestCase for Formatter class hierarchy."""

    def setUp(self) -> None:
        """Set up env before each test."""
        super().setUp()
        self.rules = {
            "uuid": "as_is:id",
            "platform": "as_is:platformName",
            "image_url": "as_is:ociImageUrl",
            "app_metadata": "literal:",
            "lib_match_mode": "literal:normal",
            "output_filename": "format_string:{appId}_{appVersion}_{platformName}_{firmwareVersion}",
            "searchpath": "format_string:{bundle_store_dir}/{id}",
            "outputdir": (
                "or:encrypt"
                "|{nginx_store_dir}/"
                "{appId}/"
                "{appVersion}/"
                "{platformName}/"
                "{firmwareVersion}"
                "|{bundle_store_dir}/"
                "{appId}/"
                "{appVersion}/"
                "{platformName}/"
                "{firmwareVersion}"
            ),
            "createmountpoints": "bool:true",
        }
        self.bad_rules = {
            "uuid": "as_is:key:value",
        }
        self.in_msg = {
            "x-request-id": "x-request-id",
            "id": "x-request-id",
            "bundle_store_dir": "bundle_store_dir",
            "nginx_store_dir": "nginx_store_dir",
            "platformName": "apollo",
            "firmwareVersion": "502.54.1",
            "ociImageUrl": "https://some.repo.url/dacs/com.test.app.awesome:1.3.4",
            "appId": "com.test.app.awesome",
            "appVersion": "1.2.3",
            "encrypt": False,
        }
        self.out_msg = {
            "uuid": self.in_msg["id"],
            "platform": self.in_msg["platformName"],
            "image_url": self.in_msg["ociImageUrl"],
            "app_metadata": "",
            "lib_match_mode": "normal",
            "output_filename": (
                f"{self.in_msg['appId']}_{self.in_msg['appVersion']}_"
                f"{self.in_msg['platformName']}_{self.in_msg['firmwareVersion']}"
            ),
            "searchpath": f"{self.in_msg['bundle_store_dir']}/{self.in_msg['id']}",
            "outputdir": (
                f"{self.in_msg['nginx_store_dir']}/"
                f"{self.in_msg['appId']}/"
                f"{self.in_msg['appVersion']}/"
                f"{self.in_msg['platformName']}/"
                f"{self.in_msg['firmwareVersion']}"
            ),
            "createmountpoints": True,
        }

    def test_abstract_initialization(self) -> None:
        """Test abstract class initialization."""
        self.assertSetEqual(set(["format"]), Formatter.__dict__["__abstractmethods__"])

    def test_bundlegenformatter_format(self) -> None:
        """Test success casse for `format()` method."""
        config_mock = mock.MagicMock(name="Config")
        formatter = BundleGenFormatter(config_mock)
        config_mock.get.return_value = self.rules

        msg = formatter.format(self.in_msg)

        config_mock.get.assert_called_once_with("message")
        self.assertDictEqual(msg, self.out_msg)

    def test_bundlegenformatter_format_error(self) -> None:
        """Test error casse for `format()` method."""
        config_mock = mock.MagicMock(name="Config")
        formatter = BundleGenFormatter(config_mock)
        config_mock.get.return_value = self.bad_rules

        with self.assertRaises(KeyError):
            formatter.format(self.in_msg)
