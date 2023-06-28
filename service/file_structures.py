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

"""Module defines base `FileStructure` class and all specific childs."""
from abc import (
    ABC,
    abstractmethod,
)
from typing import TYPE_CHECKING
import logging
import os
import shutil


if TYPE_CHECKING:  # pragma: no cover
    from service.config import Config
    from service.downloaders import Downloader


class FileStructure(ABC):
    """Base class for creating, deleting and unpacking files and directories."""

    def __init__(self, config: "Config") -> None:
        """Initialize class with config."""
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def create_structure_for(self, path: str, filename: str) -> None:
        """Create directory structure for files."""


class BundleGenFileStructure(FileStructure):
    """Create file structure for BundleGen."""

    def __init__(self, config: "Config", downloader: "Downloader") -> None:  # move downloader out
        super().__init__(config)
        self.downloader = downloader

    def create_structure_for(self, path: str, filename: str) -> None:
        """Create temp directory, download tar template file to it and unpack."""
        self.create_template_directory(path)
        self.download_template_archive(path, filename)
        self.unpack_template_archive(path, filename)

    def create_template_directory(self, path: str) -> None:
        """Create tmp directory for template files (named after UUID)."""
        self.logger.info("Creating directory for template files `%s`", path)
        if not os.path.exists(path):
            os.makedirs(path)

    def download_template_archive(self, path: str, filename: str) -> None:
        """Download template files from S3 to tmp directory."""
        self.logger.info("Downloading template archive `%s` to `%s`", filename, path)
        self.downloader.download(path, filename)

    def unpack_template_archive(self, path: str, filename: str) -> None:
        """Unpack tar.gz file with templates json files."""
        self.logger.info("Unpacking template archive `%s`", filename)
        shutil.unpack_archive(os.path.join(path, filename), path)
