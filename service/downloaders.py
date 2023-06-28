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

"""Module defines base `Downloader` class and all specific childs."""
from abc import (
    ABC,
    abstractmethod,
)
from typing import TYPE_CHECKING
import os

from boto3 import client


if TYPE_CHECKING:  # pragma: no cover
    from service.config import Config


class Downloader(ABC):
    """Base class for downloader's hierarchy."""

    @abstractmethod
    def download(self, path: str, filename: str) -> None:
        """Download specific file from storage to `path` directory."""


class S3Downloader(Downloader):
    """Class for working with S3."""

    def __init__(self, config: "Config") -> None:
        """Initialize boto3 client."""
        self.config = config
        self.client = client(
            config.get("storage.type"),
            region_name=os.environ.get("S3_REGION"),
        )

    def download(self, path: str, filename: str) -> None:
        """Download `filename` from S3 storage to `path` directory."""
        self.client.download_file(
            os.environ.get("S3_BUCKET"),
            filename,
            os.path.join(path, filename),
        )
