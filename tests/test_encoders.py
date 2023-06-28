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

"""Test cases for Encoder class hierarchy."""
from unittest import (
    mock,
    TestCase,
)

from service.encoders import (
    Encoder,
    JsonEncoder,
    MsgPackEncoder,
)


class TestEncoders(TestCase):
    """Base TestCase for Encoder classes."""

    def test_abstract_methods(self) -> None:
        """Test set of abstract methods in class."""
        self.assertSetEqual(set(["encode"]), Encoder.__dict__["__abstractmethods__"])

    def test_staticmethods(self) -> None:
        """Test set of staticmethods in class."""
        inputs = [
            Encoder,
            JsonEncoder,
            MsgPackEncoder,
        ]

        for encoder_cls in inputs:
            with self.subTest(encoder_cls=encoder_cls):
                self.assertIsInstance(encoder_cls.__dict__["encode"], staticmethod)

    @mock.patch("service.encoders.dumps")
    def test_json_encoder(self, dumps_mock: mock.MagicMock) -> None:
        """Test JSON encoder."""
        dict_to_encode = {"some": "dict"}
        result = JsonEncoder.encode(dict_to_encode)

        dumps_mock.assert_called_once_with(dict_to_encode)
        dumps_mock().encode.assert_called_once_with(encoding="utf8")
        self.assertEqual(result, dumps_mock().encode())

    @mock.patch("service.encoders.packb")
    def test_msgpack_encoder(self, packb_mock: mock.MagicMock) -> None:
        """Test MsgPack encoder."""
        dict_to_encode = {"some": "dict"}
        result = MsgPackEncoder.encode(dict_to_encode)

        packb_mock.assert_called_once_with(dict_to_encode)
        self.assertEqual(result, packb_mock())
