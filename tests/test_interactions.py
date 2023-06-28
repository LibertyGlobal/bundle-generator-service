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

"""Test cases for communication of Worker and Rabbit."""
from unittest import (
    mock,
    TestCase,
)
import json

import msgpack

from service.config import Config
from service.handlers import (
    BundleGenHandler,
    Statuses,
)


class TestIntegrationWithRabbit(TestCase):
    """Base class for test cases (integration tests)."""

    def setUp(self) -> None:
        """Set up inner state of Worker."""
        super().setUp()
        self.source_message = {"id": "uuid", "searchpath": "searchpath", "outputdir": "outputdir"}
        self.generation_message = {
            "id": "uuid",
            "phaseCode": Statuses.GENERATION_LAUNCHED,
            "messageTimestamp": 1637061411646,
        }
        self.completion_message = {
            "id": "uuid",
            "phaseCode": Statuses.GENERATION_COMPLETED,
            "messageTimestamp": 1637061411646,
        }
        self.status_message = {
            "success": True,
            "uuid": "uuid",
            "bundle_path": "/some/bundle.tar.gz",
        }

    def test_success_trip_of_message_from_in_queueh_request_to_output(self) -> None:
        """Test path of message from input queue to output queue."""
        config = Config(path="./tests/config.json")
        handler = BundleGenHandler(
            config,
            mock.MagicMock(name="Formatter"),
            mock.MagicMock(name="FileStructure"),
        )

        with mock.patch("service.handlers.BasicProperties") as basic_props_mock:
            with mock.patch("service.handlers.get_utc_timestamp_ms") as t_mock:
                with mock.patch.object(handler, "make_src_msg") as make_src_msg_dst_mock:
                    with mock.patch.object(handler, "make_dst_msg") as make_dst_msg_mock:
                        with mock.patch.object(handler, "get_template_filename"):
                            with mock.patch("service.handlers.os") as os_mock:
                                with mock.patch("service.handlers.shutil.rmtree"):
                                    os_mock.path.exists.return_value = True
                                    t_mock.return_value = 1637061411646
                                    make_src_msg_dst_mock.return_value = self.source_message
                                    make_dst_msg_mock.return_value = self.source_message
                                    channel_mock: mock.MagicMock = mock.MagicMock(name="Channel")

                                    handler.h_request(
                                        channel_mock,
                                        mock.MagicMock(name="Method"),
                                        mock.MagicMock(name="Properties"),
                                        json.dumps(self.source_message).encode("utf8"),
                                    )
                                    handler.h_response(
                                        channel_mock,
                                        mock.MagicMock(name="Method"),
                                        mock.MagicMock(name="Properties"),
                                        msgpack.packb(self.status_message),
                                    )

                                    channel_mock.basic_publish.assert_has_calls(
                                        [
                                            mock.call(  # formatted message for BundleGen
                                                exchange="",
                                                routing_key=config.get("worker.out_queue"),
                                                body=msgpack.packb(make_dst_msg_mock()),
                                                properties=basic_props_mock(),
                                            ),
                                            mock.call(  # status message about start of work
                                                exchange="",
                                                routing_key=config.get("worker.status_queue"),
                                                body=json.dumps(self.generation_message).encode("utf8"),
                                                properties=basic_props_mock(),
                                            ),
                                            mock.call(  # status message about end of work
                                                exchange="",
                                                routing_key=config.get("worker.status_queue"),
                                                body=json.dumps(self.completion_message).encode("utf8"),
                                                properties=basic_props_mock(),
                                            ),
                                        ],
                                    )
