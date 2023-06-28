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

"""Module defines base formatter class and all specific childs."""
from abc import (
    ABC,
    abstractmethod,
)
from typing import (
    Any,
    Callable,
    Dict,
    TYPE_CHECKING,
)


if TYPE_CHECKING:  # pragma: no cover
    from service.config import Config


class Formatter(ABC):
    """Format input message to output message based on rules described in config file."""

    def __init__(self, config: "Config") -> None:
        """Formatter initialization."""
        self.config = config
        self.rules: Dict[str, Callable[[str, Dict[str, Any]], Any]] = {
            "as_is": lambda key, msg: msg[key],
            "format_string": lambda string, msg: string.format(**msg),
            "literal": lambda key, _: key,
            "or": lambda key, msg: key.split("|")[msg[key.split("|")[0]] + 1].format(**msg),
            "bool": lambda key, _: key.lower() == "true",
        }

    @abstractmethod
    def format(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Format message based on configuration parameters."""


class BundleGenFormatter(Formatter):
    """Format input message to BundleGen message based on rules described in config file."""

    def format(self, msg: Dict[str, Any]) -> Dict[str, str]:
        """Transform `msg` dict into BundleGen message dict, based on rules from config."""
        message: Dict[str, Any] = {}

        for key, string in self.config.get("message").items():
            rule, fstring = string.split(":", 1)
            message[key] = self.rules[rule](fstring, msg)

        return message
