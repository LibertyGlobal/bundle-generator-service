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

"""Test cases for Config class hierarchy."""
from unittest import (
    mock,
    TestCase,
)

from service.config import Config


class TestConfigs(TestCase):
    """Base TestCase for Config class hierarchy."""

    def setUp(self) -> None:
        """Set up env before each test."""
        super().setUp()
        self.key = "key1"
        self.data = {
            "key1": {
                "key2": {
                    "key3": "value3",
                }
            }
        }

    def test_init(self) -> None:
        """Test initialization of Config."""
        inputs = [
            ((), ("config_dev.json", ".")),
            (("some/path.json", ":"), ("some/path.json", ":")),
        ]

        for ins, outs in inputs:
            with self.subTest(ins=ins, outs=outs):
                config = Config(*ins)

                self.assertEqual(config.path, outs[0])
                self.assertEqual(config.sep, outs[1])
                self.assertEqual(config._config, {})  # pylint: disable=W0212

    def test_config_get_inner_flow(self) -> None:
        """Test inner flow of `get()` method."""
        with mock.patch("service.config.open") as open_mock:
            with mock.patch("service.config.json.load") as load_mock:
                config = Config()

                config.get(self.key)

                open_mock.assert_called_once_with("config_dev.json", "r", encoding="utf8")
                load_mock.assert_called_once_with(open_mock().__enter__())

    def test_config_get_success(self) -> None:
        """Test success case of `get()`."""
        for key in ["key1", "key1.key2", "key1.key2.key3"]:
            with self.subTest(key=key):
                config = Config()

                with mock.patch("service.config.Config.config", new_callable=mock.PropertyMock) as config_mock:
                    config_mock.return_value = self.data

                    self.assertTrue(config.get(key))

    def test_config_get_error(self) -> None:
        """Test error cases of `get()`."""
        for key in ["key0", "key1.key3", "key1.key2.key4"]:
            with self.subTest(key=key):
                config = Config()

                with mock.patch("service.config.Config.config", new_callable=mock.PropertyMock) as config_mock:
                    config_mock.return_value = self.data

                    with self.assertRaises(KeyError):
                        config.get(key)

    def test_lru_cache(self) -> None:
        """Test `@lru_cache` work."""
        config = Config()

        with mock.patch("service.config.Config.config", new_callable=mock.PropertyMock) as config_mock:
            config.get(self.key)
            config.get(self.key)

            config_mock().__getitem__.assert_called_once_with(self.key)
