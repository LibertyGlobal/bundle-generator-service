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

"""Module defines base `Handler` class and all specific childs."""
from abc import (
    ABC,
    abstractmethod,
)
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    TYPE_CHECKING,
)
import logging
import os
import shutil

from pika import BasicProperties
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic

from service.decoders import (
    Decoder,
    JsonDecoder,
    MsgPackDecoder,
)
from service.encoders import (
    Encoder,
    JsonEncoder,
    MsgPackEncoder,
)
from service.utils import get_utc_timestamp_ms


if TYPE_CHECKING:  # pragma: no cover
    from service.config import Config
    from service.file_structures import FileStructure
    from service.formatter import Formatter


def get_decoder(key: str) -> Decoder:
    """Get decoder based on config."""
    return {"json": JsonDecoder, "msgpack": MsgPackDecoder}[key]()


def get_encoder(key: str) -> Encoder:
    """Get encoder based on config."""
    return {"json": JsonEncoder, "msgpack": MsgPackEncoder}[key]()


class Statuses(str, Enum):
    """Ticket's statuses."""

    GENERATION_REQUESTED = "GENERATION_REQUESTED"
    GENERATION_LAUNCHED = "GENERATION_LAUNCHED"
    GENERATION_COMPLETED = "GENERATION_COMPLETED"
    BUNDLE_ERROR = "BUNDLE_ERROR"


class Handler(ABC):
    """Base class for handling RabbitMQ messages."""

    def __init__(self, config: "Config") -> None:
        """Initialize worker instance with config, formatter and downloader."""
        super().__init__()
        self.config = config
        self.decoders: Dict[str, Decoder] = {}
        self.encoders: Dict[str, Encoder] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def make_src_msg(self, body: bytes, properties: BasicProperties) -> Dict[str, str]:
        """Prepare message from input queue."""

    @abstractmethod
    def make_dst_msg(self, source_message: Dict[str, str]) -> Dict[str, str]:
        """Prepare message for output queue."""

    @abstractmethod
    def h_request(self, channel: BlockingChannel, method: Basic.Deliver, props: BasicProperties, body: bytes) -> None:
        """Handle input message."""

    @abstractmethod
    def h_response(self, channel: BlockingChannel, method: Basic.Deliver, props: BasicProperties, body: bytes) -> None:
        """Handle output message."""


class BundleGenHandler(Handler):
    """Handle messages for BundleGen."""

    def __init__(self, config: "Config", formatter: "Formatter", file_structure: "FileStructure") -> None:
        super().__init__(config)
        self.formatter = formatter
        self.file_structure = file_structure  # add downloader here and remove from file_structure, not it is ugly
        self.request_id_map: Dict[str, str] = {}

    @property
    def in_decoder(self) -> Decoder:
        """Decode message for `in_queue`."""
        if self.decoders.get("in_decoder") is None:
            self.decoders["in_decoder"] = get_decoder(self.config.get("worker.in_decoder"))

        return self.decoders["in_decoder"]

    @property
    def out_encoder(self) -> Encoder:
        """Encode message from `out_queue`."""
        if self.encoders.get("out_encoder") is None:
            self.encoders["out_encoder"] = get_encoder(self.config.get("worker.out_encoder"))

        return self.encoders["out_encoder"]

    @property
    def status_decoder(self) -> Decoder:
        """Decode message for `status_queue`."""
        if self.decoders.get("status_decoder") is None:
            self.decoders["status_decoder"] = get_decoder(self.config.get("worker.status_decoder"))

        return self.decoders["status_decoder"]

    @property
    def status_encoder(self) -> Encoder:
        """Encode message from `status_queue`."""
        if self.encoders.get("status_encoder") is None:
            self.encoders["status_encoder"] = get_encoder(self.config.get("worker.status_encoder"))

        return self.encoders["status_encoder"]

    def get_template_filename(self, msg: Dict[str, str]) -> str:
        """Get template archive filename."""
        f_template_filename: str = self.config.get("templates_archive_name")
        return f_template_filename.format(**msg)

    def h_request(self, channel: BlockingChannel, method: Basic.Deliver, props: BasicProperties, body: bytes) -> None:
        """Handle input message."""
        self.logger.debug("%s\t%s\t%s", channel, method, props)
        try:
            source_msg = self.make_src_msg(body, props)
            self.logger.info("Received new input message: %s", source_msg)

            destination_msg = self.make_dst_msg(source_msg)
            self.file_structure.create_structure_for(
                destination_msg["searchpath"],
                self.get_template_filename(source_msg),
            )
            if os.path.exists(destination_msg["outputdir"]):
                shutil.rmtree(destination_msg["outputdir"])

            os.makedirs(destination_msg["outputdir"])
        except Exception as exc:  # pylint: disable=W0703
            self.logger.exception("Exception occurred while formatting message: %s", str(exc))
            source_id = str(props.headers.get("x-request-id", "")) if props.headers is not None else ""
            self.send_error_msg(channel, str(exc), source_id)
        else:
            self.send_bundlegen_msg(channel, destination_msg)
            self.send_success_msg(channel, Statuses.GENERATION_LAUNCHED, source_msg["id"])
        finally:
            channel.basic_ack(delivery_tag=method.delivery_tag)  # type: ignore[arg-type]

    def h_response(self, channel: BlockingChannel, method: Basic.Deliver, props: BasicProperties, body: bytes) -> None:
        """Handle output message."""
        self.logger.debug("%s\t%s\t%s", channel, method, props)

        msg = self.decode_status_message(body)

        self.logger.info("Received new status message: %s", msg)

        if msg["success"]:
            self.send_success_msg(channel, Statuses.GENERATION_COMPLETED, msg["uuid"])
        else:
            self.send_error_msg(channel, "Got error from BundleGen", msg["uuid"])

    def make_src_msg(self, body: bytes, properties: BasicProperties) -> Dict[str, str]:
        """Prepare message from input queue."""
        src_msg: Dict[str, str] = self.decode_input_message(body)
        extended_source_msg: Dict[str, str] = self.extend_message(src_msg, properties.headers)  # type: ignore[arg-type]
        source_id = extended_source_msg.setdefault("id", extended_source_msg["x-request-id"])
        self.request_id_map[source_id] = extended_source_msg["x-request-id"]
        return extended_source_msg

    def make_dst_msg(self, source_message: Dict[str, str]) -> Dict[str, str]:
        """Prepare message for output queue."""
        return self.formatter.format(source_message)

    def decode_input_message(self, body: bytes) -> Any:
        """Decode input message."""
        return self.in_decoder.decode(body)

    def decode_status_message(self, body: bytes) -> Any:
        """Decode status message."""
        return self.status_decoder.decode(body)

    def extend_message(self, msg: Dict[str, str], headers: Dict[str, str]) -> Dict[str, Any]:
        """Extend message with required fields."""
        result = {}
        c_envs: List[str] = self.config.get("envs")
        c_headers: List[str] = self.config.get("headers")

        for env in c_envs:
            result[env.lower()] = os.environ.get(env)

        for header in c_headers:
            result[header.lower()] = headers.get(header)

        return {**msg, **result}

    def _send_status_message(self, channel: BlockingChannel, msg: Dict[str, Any], uuid: str) -> None:
        """Send status message for ABS."""
        channel.basic_publish(
            exchange="",
            routing_key=self.config.get("worker.status_queue"),
            body=self.status_encoder.encode(msg),
            properties=BasicProperties(
                delivery_mode=2,  # make message persistent
                headers={"x-request-id": self.request_id_map.get(uuid, uuid), },
            ),
        )

    def send_error_msg(self, channel: BlockingChannel, message: str, uuid: str) -> None:
        """Send error status message for ABS."""
        self._send_status_message(
            channel,
            {
                "id": uuid,
                "phaseCode": Statuses.BUNDLE_ERROR.value,
                "messageTimestamp": get_utc_timestamp_ms(),
                "error": {
                    "code": "GENERIC_ERROR",
                    "message": message,
                },
            },
            uuid,
        )

    def send_success_msg(self, channel: BlockingChannel, phase_code: Statuses, uuid: str) -> None:
        """Send generation status message for ABS."""
        self._send_status_message(
            channel,
            {
                "id": uuid,
                "phaseCode": phase_code.value,
                "messageTimestamp": get_utc_timestamp_ms(),
            },
            uuid,
        )

    def send_bundlegen_msg(self, channel: BlockingChannel, msg: Dict[str, str]) -> None:
        """Send ticket for BundleGen."""
        self.logger.info("Send message to BundleGen: %s", msg)

        channel.basic_publish(
            exchange="",
            routing_key=self.config.get("worker.out_queue"),
            body=self.out_encoder.encode(msg),
            properties=BasicProperties(
                delivery_mode=2,  # make message persistent
                reply_to="amq.rabbitmq.reply-to",
            ),
        )
