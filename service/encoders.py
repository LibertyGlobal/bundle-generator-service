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

"""Module defines base `Encoder` class and all specific childs."""
from abc import (
    ABC,
    abstractmethod,
)
from json import dumps
from typing import (
    Any,
    AnyStr,
    Dict,
)

from msgpack import packb


class Encoder(ABC):
    """Base class for encoding RabbitMQ messages."""

    @staticmethod
    @abstractmethod
    def encode(msg: Dict[str, Any]) -> bytes:
        """Return string representation of `msg`."""


class JsonEncoder(Encoder):
    """Use JSON format for encoding messages."""

    @staticmethod
    def encode(msg: Dict[str, AnyStr]) -> bytes:
        """Return JSON string of `msg`."""
        return dumps(msg).encode(encoding="utf8")


class MsgPackEncoder(Encoder):
    """Use MsgPack format for encoding messages."""

    @staticmethod
    def encode(msg: Dict[str, AnyStr]) -> bytes:
        """Return MsgPack string of `msg`."""
        return packb(msg)
