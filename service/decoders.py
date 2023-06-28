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

"""Module defines base `Decoder` class and all specific childs."""
from abc import (
    ABC,
    abstractmethod,
)
from json import loads
from typing import Any

from msgpack import unpackb


class Decoder(ABC):
    """Base class for decoding RabbitMQ messages."""

    @staticmethod
    @abstractmethod
    def decode(msg: bytes) -> Any:
        """Return `msg` string as dict."""


class JsonDecoder(Decoder):
    """Decode JSON string representation."""

    @staticmethod
    def decode(msg: bytes) -> Any:
        """Return `msg` string in JSON format as dict."""
        return loads(msg)


class MsgPackDecoder(Decoder):
    """Decode MsgPack string representation."""

    @staticmethod
    def decode(msg: bytes) -> Any:
        """Return `msg` string in MsgPack format as dict."""
        return unpackb(msg)
