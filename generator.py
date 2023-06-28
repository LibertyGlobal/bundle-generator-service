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

"""Generate input message for RabbitMQ's `bundlegen-service-requests` queue"""
import json
import time
import uuid

from pika.adapters.blocking_connection import BlockingChannel
import pika


channel: BlockingChannel = pika.BlockingConnection(
    pika.ConnectionParameters("<rabbitmq.ip.address>"),
).channel()

while True:
    message_id = str(uuid.uuid4())
    print(f"SEND MESSAGE\t[{message_id}]")

    channel.basic_publish(
        exchange="",
        routing_key="bundlegen-service-requests",
        body=json.dumps(
            {
                "platformName": "eos2008c-debug",
                "firmwareVersion": "502.54.1",
                "ociImageUrl": "docker://docker.registry.url/dac/doom",
                "appId": "com.dns.app.awesome",
                "appVersion": message_id,
                "encrypt": False,
            }
        ),
        properties=pika.BasicProperties(
            delivery_mode=2,
            headers={"x-request-id": message_id},
        ),
    )

    time.sleep(15)
