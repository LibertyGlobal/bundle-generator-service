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

"""Test cases for Decoder class hierarchy."""
from unittest import (
    mock,
    TestCase,
)

from service.decoders import (
    Decoder,
    JsonDecoder,
    MsgPackDecoder,
)


class TestDecoder(TestCase):
    """Base TestCase for Decoder classes."""

    def test_abstract_methods(self) -> None:
        """Test set of abstract methods in class."""
        self.assertSetEqual(set(["decode"]), Decoder.__dict__["__abstractmethods__"])

    def test_staticmethods(self) -> None:
        """Test set of staticmethods in class."""
        inputs = [
            Decoder,
            JsonDecoder,
            MsgPackDecoder,
        ]

        for decoder_cls in inputs:
            with self.subTest(decoder_cls=decoder_cls):
                self.assertIsInstance(decoder_cls.__dict__["decode"], staticmethod)

    @mock.patch("service.decoders.loads")
    def test_json_decoder(self, loads_mock: mock.MagicMock) -> None:
        """Test `JsonDecoder` decoder."""
        string_to_decode = b"some string"
        result = JsonDecoder.decode(string_to_decode)

        loads_mock.assert_called_once_with(string_to_decode)
        self.assertEqual(result, loads_mock())

    @mock.patch("service.decoders.unpackb")
    def test_msgpack_decoder(self, unpackb_mock: mock.MagicMock) -> None:
        """Test `MsgPackDecoder` decoder."""
        string_to_decode = b"some string"
        result = MsgPackDecoder.decode(string_to_decode)

        unpackb_mock.assert_called_once_with(string_to_decode)
        self.assertEqual(result, unpackb_mock())
