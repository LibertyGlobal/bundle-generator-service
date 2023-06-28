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

"""Test cases for Worker class hierarchy."""
from unittest import (
    mock,
    TestCase,
)

from pika.exceptions import (
    AMQPChannelError,
    AMQPConnectionError,
    ConnectionClosedByBroker,
)

from service.worker import Worker


class TestWorkers(TestCase):
    """Base TestCase for Worker class hierarchy."""

    def setUp(self) -> None:
        """Set up env before each test."""
        super().setUp()

        self.config_mock = mock.MagicMock(name="Config")
        self.handler_mock = mock.MagicMock(name="Handler")

    def _get_worker(self) -> Worker:
        """Get Worker instance with mocks."""
        self.config_mock.reset_mock(return_value=True, side_effect=True)
        self.handler_mock.reset_mock(return_value=True, side_effect=True)

        return Worker(self.config_mock, self.handler_mock)

    def test_init(self) -> None:
        """Test worker initialization."""
        worker = self._get_worker()

        self.assertEqual(worker.config, self.config_mock)
        self.assertEqual(worker.handler, self.handler_mock)

    def test_queues_declare(self) -> None:
        """Test `queues_declare()` method."""
        worker = self._get_worker()
        channel_mock = mock.MagicMock(name="BlockingChannel")

        worker.queues_declare(channel_mock)

        self.config_mock.get.assert_has_calls(
            [
                mock.call("worker.in_queue"),
                mock.call("worker.out_queue"),
                mock.call("worker.status_queue"),
            ],
        )
        channel_mock.queue_declare.assert_has_calls(
            [
                mock.call(queue=self.config_mock.get(), durable=True),
                mock.call(queue=self.config_mock.get(), durable=True),
                mock.call(queue=self.config_mock.get(), durable=True),
            ],
        )

    def test_initialize_channel(self) -> None:
        """Test `initialize_channel()` method."""
        worker = self._get_worker()

        with mock.patch("service.worker.ConnectionParameters") as connection_params_mock:
            with mock.patch("service.worker.BlockingConnection") as blocking_conn_mock:
                with mock.patch("service.worker.os.environ.get") as os_get_mock:
                    os_get_mock.side_effect = lambda *args: args[1]
                    channel = worker.initialize_channel()

                    os_get_mock.assert_has_calls(
                        [
                            mock.call("RABBITMQ_HOST", "localhost"),
                            mock.call("RABBITMQ_PORT", 5672),
                            mock.call("RABBITMQ_CONNECTION_ATTEMPTS", 5),
                            mock.call("RABBITMQ_RETRY_DELAY", 5),
                        ]
                    )
                    connection_params_mock.assert_called_once_with(
                        host="localhost",
                        port=5672,
                        connection_attempts=5,
                        retry_delay=5,
                    )
                    blocking_conn_mock.assert_called_once_with(
                        parameters=connection_params_mock(),
                    )
                    self.assertEqual(channel, blocking_conn_mock().channel())

    def test_run(self) -> None:
        """Test `run()` method for success case."""
        worker = self._get_worker()

        with mock.patch.object(worker, "initialize_channel") as init_channel_mock:
            with mock.patch.object(worker, "queues_declare") as queues_declare_mock:
                worker.run()

                init_channel_mock.assert_called_once_with()
                queues_declare_mock.assert_called_once_with(init_channel_mock())
                self.config_mock.get.assert_called_once_with("worker.in_queue")
                init_channel_mock().basic_consume.assert_has_calls(
                    [
                        mock.call(
                            queue=self.config_mock.get(),
                            on_message_callback=worker.handler.h_request,
                        ),
                        mock.call(
                            queue="amq.rabbitmq.reply-to",
                            on_message_callback=worker.handler.h_response,
                            auto_ack=True,
                        ),
                    ]
                )
                init_channel_mock().start_consuming.assert_called_once_with()

    def test_run_exceptions(self) -> None:
        """Test `run()` method for exception case."""
        for exc in [AMQPConnectionError, AMQPChannelError, ConnectionClosedByBroker]:
            worker = self._get_worker()

            with self.subTest(exc=exc):
                with mock.patch.object(worker, "initialize_channel") as init_channel_mock:
                    with mock.patch.object(worker, "close") as close_mock:
                        init_channel_mock.side_effect = exc(1, "message")
                        worker.run()

                        close_mock.assert_called_once_with()
