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

"""Test cases for Handler class hierarchy."""
from typing import Dict
from unittest import (
    mock,
    TestCase,
)

from service.handlers import (
    BundleGenHandler,
    Handler,
    Statuses,
)


class TestBundleGenHandlers(TestCase):
    """Base TestCase for Handler class hierarchy."""

    def setUp(self) -> None:
        """Set up env before each test."""
        super().setUp()

        self.config_mock = mock.MagicMock(name="Config")
        self.formatter_mock = mock.MagicMock(name="Formatter")
        self.file_structure_mock = mock.MagicMock(name="FileStructure")

        self.body = b"body"

        self.channel = mock.MagicMock(name="Channel")
        self.method = mock.MagicMock(name="Method")
        self.properties = mock.MagicMock(name="Properties")
        self.properties.headers = {"x-request-id": 'x-request-id'}

    def _get_handler(self) -> BundleGenHandler:
        """Get BundleGenHandler instance with mocks."""
        self.config_mock.reset_mock(return_value=True, side_effect=True)
        self.formatter_mock.reset_mock(return_value=True, side_effect=True)
        self.file_structure_mock.reset_mock(return_value=True, side_effect=True)

        return BundleGenHandler(self.config_mock, self.formatter_mock, self.file_structure_mock)

    def test_init(self) -> None:
        """Test handler initialization."""
        handler = self._get_handler()

        self.assertEqual(handler.config, self.config_mock)
        self.assertEqual(handler.formatter, self.formatter_mock)
        self.assertEqual(handler.file_structure, self.file_structure_mock)
        self.assertDictEqual(handler.encoders, {})
        self.assertDictEqual(handler.decoders, {})

    def test_abstract_methods(self) -> None:
        """Test set of abstract methods in class."""
        self.assertSetEqual(
            set(["make_src_msg", "make_dst_msg", "h_request", "h_response"]),
            Handler.__dict__["__abstractmethods__"],
        )

    def test_encoder_properties(self) -> None:
        """Test `*_encoder` properties."""
        inputs = [
            "out_encoder",
            "status_encoder",
        ]

        for encoder_name in inputs:
            with self.subTest(encoder_name=encoder_name):
                handler = self._get_handler()
                handler.encoders = mock.MagicMock(name="encoders")
                handler.encoders.get.return_value = None

                with mock.patch("service.handlers.get_encoder") as get_encoder_mock:
                    getattr(handler, encoder_name)

                    handler.encoders.get.assert_called_once_with(encoder_name)
                    self.config_mock.get.assert_called_once_with(f"worker.{encoder_name}")
                    get_encoder_mock.assert_called_once_with(self.config_mock.get())
                    handler.encoders.__setitem__.assert_called_once_with(  # pylint: disable=E1101
                        encoder_name, get_encoder_mock()
                    )
                    handler.encoders.__getitem__.assert_called_once_with(encoder_name)  # pylint: disable=E1101

    def test_decoder_properties(self) -> None:
        """Test `*_decoder` properties."""
        inputs = [
            "in_decoder",
            "status_decoder",
        ]

        for decoder_name in inputs:
            with self.subTest(decoder_name=decoder_name):
                handler = self._get_handler()
                handler.decoders = mock.MagicMock(name="decoders")
                handler.decoders.get.return_value = None

                with mock.patch("service.handlers.get_decoder") as get_decoder_mock:
                    getattr(handler, decoder_name)

                    handler.decoders.get.assert_called_once_with(decoder_name)
                    self.config_mock.get.assert_called_once_with(f"worker.{decoder_name}")
                    get_decoder_mock.assert_called_once_with(self.config_mock.get())
                    handler.decoders.__setitem__.assert_called_once_with(  # pylint: disable=E1101
                        decoder_name, get_decoder_mock()
                    )
                    handler.decoders.__getitem__.assert_called_once_with(decoder_name)  # pylint: disable=E1101

    def test_decode_input_message(self) -> None:
        """Test `decode_input_message()` method."""
        handler = self._get_handler()
        body = b"body"

        with mock.patch("service.handlers.BundleGenHandler.in_decoder") as in_decoder_mock:
            msg = handler.decode_input_message(body)

            in_decoder_mock.decode.assert_called_once_with(body)
            self.assertEqual(msg, in_decoder_mock.decode())

    def test_decode_status_message(self) -> None:
        """Test `decode_status_message()` method."""
        handler = self._get_handler()
        body = b"body"

        with mock.patch("service.handlers.BundleGenHandler.status_decoder") as status_decoder_mock:
            msg = handler.decode_status_message(body)

            status_decoder_mock.decode.assert_called_once_with(body)
            self.assertEqual(msg, status_decoder_mock.decode())

    def test_send_status_message(self) -> None:
        """Test `_send_status_message()` method."""
        handler = self._get_handler()
        channel_mock = mock.MagicMock(name="BlockingChannel")
        msg = {"some": "message"}

        with mock.patch("service.handlers.BundleGenHandler.status_encoder") as status_encoder_mock:
            with mock.patch("service.handlers.BasicProperties") as bp_mock:
                handler._send_status_message(channel_mock, msg, "uuid")  # pylint: disable=W0212

                self.config_mock.get.assert_called_once_with("worker.status_queue")
                status_encoder_mock.encode.assert_called_once_with(msg)
                bp_mock.assert_called_once_with(
                    delivery_mode=2,
                    headers={"x-request-id": "uuid"},
                )
                channel_mock.basic_publish.assert_called_once_with(
                    exchange="",
                    routing_key=self.config_mock.get(),
                    body=status_encoder_mock.encode(),
                    properties=bp_mock(),
                )

    def test_send_error_msg(self) -> None:
        """Test `send_error_msg()` method."""
        handler = self._get_handler()
        channel_mock = mock.MagicMock(name="BlockingChannel")
        body = "body"
        uuid = "uuid"

        with mock.patch.object(handler, "_send_status_message") as send_status_message_mock:
            with mock.patch("service.handlers.get_utc_timestamp_ms") as t_mock:
                handler.send_error_msg(channel_mock, body, uuid)

                send_status_message_mock.assert_called_once_with(
                    channel_mock,
                    {
                        "id": "uuid",
                        "phaseCode": Statuses.BUNDLE_ERROR.value,
                        "messageTimestamp": t_mock(),
                        "error": {
                            "code": "GENERIC_ERROR",
                            "message": body,
                        },
                    },
                    uuid,
                )

    def test_send_success_msg(self) -> None:
        """Test `send_success_msg()` method."""
        handler = self._get_handler()
        channel_mock = mock.MagicMock(name="BlockingChannel")
        uuid = "uuid"

        with mock.patch.object(handler, "_send_status_message") as send_status_message_mock:
            with mock.patch("service.handlers.get_utc_timestamp_ms") as t_mock:
                handler.send_success_msg(channel_mock, Statuses.GENERATION_REQUESTED, uuid)

                send_status_message_mock.assert_called_once_with(
                    channel_mock,
                    {
                        "id": "uuid",
                        "phaseCode": Statuses.GENERATION_REQUESTED,
                        "messageTimestamp": t_mock(),
                    },
                    uuid,
                )

    def test_send_bundlegen_msg(self) -> None:
        """Test `send_bundlegen_msg()` method."""
        handler = self._get_handler()
        channel_mock = mock.MagicMock(name="BlockingChannel")
        msg = {"some": "message"}

        with mock.patch("service.handlers.BundleGenHandler.out_encoder") as out_encoder_mock:
            with mock.patch("service.handlers.BasicProperties") as bp_mock:
                handler.send_bundlegen_msg(channel_mock, msg)

                self.config_mock.get.assert_called_once_with("worker.out_queue")
                out_encoder_mock.encode.assert_called_once_with(msg)
                bp_mock.assert_called_once_with(
                    delivery_mode=2,  # make message persistent
                    reply_to="amq.rabbitmq.reply-to",
                )
                channel_mock.basic_publish.assert_called_once_with(
                    exchange="",
                    routing_key=self.config_mock.get(),
                    body=out_encoder_mock.encode(),
                    properties=bp_mock(),
                )

    def test_h_request_error(self) -> None:
        """Test `h_request()` method for error."""
        handler = self._get_handler()

        with mock.patch.object(handler, "make_src_msg") as prepare_mock:
            with mock.patch.object(handler, "send_error_msg") as send_mock:
                self.formatter_mock.format.side_effect = KeyError()

                handler.h_request(self.channel, self.method, self.properties, self.body)

                prepare_mock.assert_called_once_with(self.body, self.properties)
                self.formatter_mock.format.assert_called_once_with(prepare_mock())
                send_mock.assert_called_once_with(
                    self.channel,
                    str(KeyError()),
                    self.properties.headers["x-request-id"]
                )
                self.channel.basic_ack.assert_called_once_with(
                    delivery_tag=self.method.delivery_tag,
                )

    def test_h_request_error_without_header(self) -> None:
        """Test `h_request()` method for error."""
        handler = self._get_handler()

        with mock.patch.object(handler, "make_src_msg") as prepare_mock:
            with mock.patch.object(handler, "send_error_msg") as send_mock:
                self.formatter_mock.format.side_effect = KeyError()
                expected = mock.MagicMock(name="Properties")
                expected.headers = {}
                handler.h_request(self.channel, self.method, expected, self.body)

                prepare_mock.assert_called_once_with(self.body, expected)
                self.formatter_mock.format.assert_called_once_with(prepare_mock())
                send_mock.assert_called_once_with(
                    self.channel,
                    str(KeyError()),
                    ""
                )
                self.channel.basic_ack.assert_called_once_with(
                    delivery_tag=self.method.delivery_tag,
                )

    def test_h_request_error_headers_none(self) -> None:
        """Test `h_request()` method for error."""
        handler = self._get_handler()

        with mock.patch.object(handler, "make_src_msg") as prepare_mock:
            with mock.patch.object(handler, "send_error_msg") as send_mock:
                self.formatter_mock.format.side_effect = KeyError()
                expected = mock.MagicMock(name="Properties")
                expected.headers = None
                handler.h_request(self.channel, self.method, expected, self.body)

                prepare_mock.assert_called_once_with(self.body, expected)
                self.formatter_mock.format.assert_called_once_with(prepare_mock())
                send_mock.assert_called_once_with(
                    self.channel,
                    str(KeyError()),
                    ""
                )
                self.channel.basic_ack.assert_called_once_with(
                    delivery_tag=self.method.delivery_tag,
                )

    def test_h_request_success(self) -> None:
        """Test `h_request()` method for success."""
        handler = self._get_handler()

        with mock.patch.object(handler, "make_src_msg") as prepare_mock:
            with mock.patch.object(handler, "get_template_filename") as gtf_mock:
                with mock.patch.object(handler, "send_bundlegen_msg") as publish_mock:
                    with mock.patch.object(handler, "send_success_msg") as send_mock:
                        with mock.patch("service.handlers.os") as os_mock:
                            os_mock.path.exists.return_value = False
                            handler.h_request(self.channel, self.method, self.properties, self.body)

                            prepare_mock.assert_called_once_with(self.body, self.properties)
                            self.formatter_mock.format.assert_called_once_with(prepare_mock())
                            self.formatter_mock.format().__getitem__.assert_has_calls(
                                [
                                    mock.call("searchpath"),
                                    mock.call("outputdir"),
                                    mock.call("outputdir"),
                                ],
                            )
                            self.file_structure_mock.create_structure_for.assert_called_once_with(
                                self.formatter_mock.format().__getitem__(),
                                gtf_mock(prepare_mock()),
                            )
                            os_mock.path.exists.assert_called_once_with(
                                self.formatter_mock.format().__getitem__(),
                            )
                            os_mock.makedirs.assert_called_once_with(
                                self.formatter_mock.format().__getitem__(),
                            )
                            publish_mock.assert_called_once_with(
                                self.channel,
                                self.formatter_mock.format(),
                            )
                            prepare_mock().__getitem__.assert_called_once_with("id")
                            send_mock.assert_called_once_with(
                                self.channel,
                                Statuses.GENERATION_LAUNCHED,
                                prepare_mock()["id"],
                            )
                            self.channel.basic_ack.assert_called_once_with(
                                delivery_tag=self.method.delivery_tag,
                            )

    def test_h_response_with_success_response(self) -> None:
        """Test `h_response()` method with success response."""
        handler = self._get_handler()

        with mock.patch.object(handler, "decode_status_message") as decode_mock:
            with mock.patch.object(handler, "send_success_msg") as send_mock:
                decode_mock.return_value = {"success": True, "uuid": "uuid"}

                handler.h_response(self.channel, self.method, self.properties, self.body)

                decode_mock.assert_called_once_with(self.body)
                send_mock.assert_called_once_with(
                    self.channel,
                    Statuses.GENERATION_COMPLETED,
                    decode_mock()["uuid"],
                )

    def test_h_response_with_fail_response(self) -> None:
        """Test `h_response()` method with fail response."""
        handler = self._get_handler()

        with mock.patch.object(handler, "decode_status_message") as decode_mock:
            with mock.patch.object(handler, "send_error_msg") as send_mock:
                decode_mock.return_value = {"success": False, "uuid": "uuid"}

                handler.h_response(self.channel, self.method, self.properties, self.body)

                decode_mock.assert_called_once_with(self.body)
                send_mock.assert_called_once_with(
                    self.channel,
                    "Got error from BundleGen",
                    decode_mock()["uuid"],
                )

    def test_extend_message(self) -> None:
        """Test `extend_message()` method."""
        handler = self._get_handler()
        env = {"bundle_store_dir": "tmp"}
        headers = {"x-request-id": "uuid"}

        with mock.patch.dict("service.handlers.os.environ", env):
            self.config_mock.get.side_effect = [["bundle_store_dir"], ["x-request-id"]]
            msg: Dict[str, str] = {"key": "value"}

            out = handler.extend_message(msg, headers)

            self.config_mock.get.assert_has_calls(
                [
                    mock.call("envs"),
                    mock.call("headers"),
                ],
            )
            self.assertDictEqual(out, {**msg, **env, **headers})

    def test_get_template_filename(self) -> None:
        """Test `get_template_filename()` method."""
        handler = self._get_handler()
        msg = {"some": "message"}

        handler.get_template_filename(msg)

        self.config_mock.get.assert_called_once_with("templates_archive_name")
        self.config_mock.get().format.assert_called_once_with(**msg)

    def test_make_src_msg(self) -> None:
        """Test `make_src_msg()` method."""
        handler = self._get_handler()

        with mock.patch.object(handler, "decode_input_message") as decode_mock:
            with mock.patch.object(handler, "extend_message") as extend_mock:
                extend_mock.return_value = {"x-request-id": "uuid"}
                res = handler.make_src_msg(b"body", self.properties)

                decode_mock.assert_called_once_with(b"body")
                extend_mock.assert_called_once_with(decode_mock(), self.properties.headers)
                self.assertEqual(res["id"], "uuid")

                extend_mock.return_value = {"x-request-id": "id", "id": "uuid"}
                res = handler.make_src_msg(b"body", self.properties)
                self.assertEqual(res["id"], "uuid")
                self.assertEqual(handler.request_id_map["uuid"], "id")

    def test_make_dst_msg(self) -> None:
        """Test `make_dst_msg()` method."""
        handler = self._get_handler()
        msg = {"some": "message"}

        handler.make_dst_msg(msg)

        self.formatter_mock.format.assert_called_once_with(msg)
