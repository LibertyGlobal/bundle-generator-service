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


"""Test cases for FileStructure class hierarchy."""
from unittest import (
    mock,
    TestCase,
)

from service.file_structures import (
    BundleGenFileStructure,
    FileStructure,
)


class TestBundleGenFileStructure(TestCase):
    """Base TestCase for FileStructure class hierarchy."""

    def setUp(self) -> None:
        """Set up env before each test."""
        super().setUp()

        self.config_mock = mock.MagicMock(name="Config")
        self.downloader_mock = mock.MagicMock(name="Downloader")

    def _get_file_structure(self) -> BundleGenFileStructure:
        """Get BundleGenFileStructure instance with mocks."""
        self.config_mock.reset_mock(return_value=True, side_effect=True)
        self.downloader_mock.reset_mock(return_value=True, side_effect=True)

        return BundleGenFileStructure(self.config_mock, self.downloader_mock)

    def test_init(self) -> None:
        """Test handler initialization."""
        fstructure = self._get_file_structure()

        self.assertEqual(fstructure.config, self.config_mock)
        self.assertEqual(fstructure.downloader, self.downloader_mock)

    def test_abstract_methods(self) -> None:
        """Test set of abstract methods in class."""
        self.assertSetEqual(
            set(["create_structure_for"]),
            FileStructure.__dict__["__abstractmethods__"],
        )

    def test_create_template_directory(self) -> None:
        """Test `create_template_directory()` method."""
        fstructure = self._get_file_structure()
        path = "path"

        with mock.patch("service.file_structures.os") as os_mock:
            os_mock.path.exists.return_value = False
            fstructure.create_template_directory(path)

            os_mock.path.exists.assert_called_once_with(path)
            os_mock.makedirs.assert_called_once_with(path)

    def test_download_template_archive(self) -> None:
        """Test `download_template_archive()` method."""
        fstructure = self._get_file_structure()

        fstructure.download_template_archive("path", "filename")

        self.downloader_mock.download.assert_called_once_with("path", "filename")

    def test_unpack_template_archive(self) -> None:
        """Test `unpack_template_archive()` method."""
        fstructure = self._get_file_structure()

        with mock.patch("service.file_structures.shutil") as shutil_mock:
            fstructure.unpack_template_archive("path", "filename")

            shutil_mock.unpack_archive.assert_called_once_with("path/filename", "path")

    def test_create_structure_for(self) -> None:
        """Test `create_structure_for()` method."""
        fstructure = self._get_file_structure()

        with mock.patch.object(fstructure, "create_template_directory") as ctd_mock:
            with mock.patch.object(fstructure, "download_template_archive") as dta_mock:
                with mock.patch.object(fstructure, "unpack_template_archive") as uta_mock:
                    fstructure.create_structure_for("path", "filename")

                    ctd_mock.assert_called_once_with("path")
                    dta_mock.assert_called_once_with("path", "filename")
                    uta_mock.assert_called_once_with("path", "filename")
