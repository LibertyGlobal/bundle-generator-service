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

"""Test cases for utils functionality."""
from unittest import (
    mock,
    TestCase,
)

from service.handlers import (
    get_decoder,
    get_encoder,
    JsonDecoder,
    JsonEncoder,
    MsgPackDecoder,
    MsgPackEncoder,
    Statuses,
)
from service.utils import (
    create_dirs_from_envs,
    get_utc_timestamp_ms,
)


class TestUtils(TestCase):
    """Base TestCase for utils functions."""

    def setUp(self) -> None:
        """Set up env before each test."""
        super().setUp()
        self.config_mock = mock.MagicMock(name="Config")

    def test_get_encoder(self) -> None:
        """Test success case of get_encoder()."""
        inputs = [
            ("json", JsonEncoder),
            ("msgpack", MsgPackEncoder),
        ]

        for encoder_type, encoder_cls in inputs:
            with self.subTest(encoder_type=encoder_type, encoder_cls=encoder_cls):
                self.assertIsInstance(get_encoder(encoder_type), encoder_cls)

    def test_get_encoder_exception(self) -> None:
        """Test failed case of get_encoder()."""
        with self.assertRaises(KeyError):
            get_encoder("unknown")

    def test_get_decoder(self) -> None:
        """Test success case of `get_decoder()`."""
        inputs = [
            ("json", JsonDecoder),
            ("msgpack", MsgPackDecoder),
        ]

        for decoder_type, decoder_cls in inputs:
            with self.subTest(decoder_type=decoder_type, decoder_cls=decoder_cls):
                self.assertIsInstance(get_decoder(decoder_type), decoder_cls)

    def test_get_decoder_exception(self) -> None:
        """Test failed case of `get_decoder()`."""
        with self.assertRaises(KeyError):
            get_decoder("unknown")

    def test_statuses(self) -> None:
        """Test `Statuses` enum."""
        self.assertEqual(len(Statuses), 4)
        self.assertEqual(Statuses.GENERATION_COMPLETED.value, "GENERATION_COMPLETED")
        self.assertEqual(Statuses.GENERATION_LAUNCHED.value, "GENERATION_LAUNCHED")
        self.assertEqual(Statuses.GENERATION_REQUESTED.value, "GENERATION_REQUESTED")
        self.assertEqual(Statuses.BUNDLE_ERROR.value, "BUNDLE_ERROR")

    def test_get_utc_timestamp_ms(self) -> None:
        """Test `get_utc_timestamp_ms()` utility function."""
        with mock.patch("service.utils.datetime") as dt_mock:
            dt_mock.utcnow().timestamp.return_value = 1637061411.646388

            self.assertEqual(get_utc_timestamp_ms(), 1637061411646)
            self.assertEqual(len(str(get_utc_timestamp_ms())), 13)

    @mock.patch("service.utils.os.makedirs")
    @mock.patch("service.utils.os.path.exists")
    @mock.patch("service.utils.os.environ.get")
    def test_create_dirs_from_envs(
        self,
        env_get_mock: mock.MagicMock,
        path_exists_mock: mock.MagicMock,
        makedirs_mock: mock.MagicMock,
    ) -> None:
        """Test `create_dirs_from_envs()` utility function."""
        env_names = ["first_env_var", "second_env_var", "third_env_var"]
        env_values = ["first_env_var_value", "second_env_var_value", "third_env_var_value"]
        self.config_mock.get.return_value = env_names
        env_get_mock.side_effect = env_values
        path_exists_mock.side_effect = [False, False, True]

        create_dirs_from_envs(self.config_mock)

        self.config_mock.get.assert_called_once_with("envs")
        env_get_mock.assert_has_calls(
            [
                mock.call(
                    env_names[0],
                ),
                mock.call(
                    env_names[1],
                ),
                mock.call(
                    env_names[2],
                ),
            ],
        )
        path_exists_mock.assert_has_calls(
            [
                mock.call(
                    env_values[0],
                ),
                mock.call(
                    env_values[1],
                ),
                mock.call(
                    env_values[2],
                ),
            ],
        )
        makedirs_mock.assert_has_calls(
            [
                mock.call(
                    env_values[0],
                ),
                mock.call(
                    env_values[1],
                ),
            ]
        )

    @mock.patch("service.utils.os.environ.get")
    def test_create_dirs_from_envs_exception(
        self,
        env_get_mock: mock.MagicMock,
    ) -> None:
        """Test `create_dirs_from_envs()` utility function."""
        env_names = ["first_env_var", "second_env_var"]
        env_values = ["", ""]
        self.config_mock.get.return_value = env_names
        env_get_mock.side_effect = env_values

        with self.assertRaises(ValueError, msg=f"{env_names[0]} is not set"):
            create_dirs_from_envs(self.config_mock)
