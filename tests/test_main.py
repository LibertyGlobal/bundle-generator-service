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

"""Test cases for main function."""
from unittest import (
    mock,
    TestCase,
)

from service.worker import main


class TestMain(TestCase):
    """Base TestCase for `main` function tests."""

    def setUp(self) -> None:
        """Set up env before each test."""
        super().setUp()
        self.num_process = 2

    @mock.patch("service.worker.create_dirs_from_envs")
    @mock.patch("service.worker.Config")
    @mock.patch("service.worker.Worker")
    @mock.patch("service.worker.S3Downloader")
    @mock.patch("service.worker.os.environ.get")
    def test_main(
        self,
        os_get_mock: mock.MagicMock,
        _: mock.MagicMock,
        worker_mock: mock.MagicMock,
        config_mock: mock.MagicMock,
        create_dirs_mock: mock.MagicMock,
    ) -> None:
        """Test calls inside main function."""
        config_mock().get.return_value = self.num_process

        main()

        create_dirs_mock.assert_called_once_with(config_mock())
        config_mock().get.assert_called_once_with("concurency")
        os_get_mock.assert_called_once_with("BUNDLE_CONFIG_FILE", "config_dev.json")
        self.assertEqual(worker_mock().start.call_count, self.num_process)
        self.assertEqual(worker_mock().join.call_count, self.num_process)
