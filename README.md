# Bundle Generator Service
Service to transform AppStore Bundle Service's messages to [BungleGen](https://github.com/rdkcentral/BundleGen) messages.

## Environment Setup
You will need Python >=3.8 installed and configured. A Dockerfile is included that can be used to run Bundle Generator Service.

## Quick Start
Start with Git clone.
```console
$ git clone --recurse-submodules path_to_repo
```

Run localy with Docker Compose
```console
$ docker-compose up -d --build
```

Check logs
```console
$ docker-compose logs -f bundle-generator-service bundle-generator
```

Run localy scaleble version with Docker Compose. Since BundleGen/Bundle Generator Service runs as a RabbitMQ consumer, it is possible to run many instances of BundleGen/Bundle Generator Service. RabbitMQ will then distribute requests to each instance in a round-robin fashion.
```console
$ docker-compose up -d --build --scale bundle-generator=4
```

## Test Scripts
Test scripts are included for reference platforms to speed up the generation process.

Start process of messages generation:
```
python generator.py
```

## Development
For development, you will need Python >=3.8 installed and configured. Once installed, then install project specific dependencies using [Poetry](https://python-poetry.org).

Install all dependencies:
```
$ cd service
$ poetry install
```

## Configuration
```json
{
    "concurency": 2,
    "worker": {
        "in_decoder": "json",
        "out_encoder": "msgpack",
        "status_decoder": "msgpack",
        "status_encoder": "json",
        "in_queue": "bundlegen-service-requests",
        "out_queue": "bundlegen-requests",
        "status_queue": "bundlegen-service-status"
    },
    "storage": {
        "type": "s3",
    },
    "envs": [
        "BUNDLE_STORE_DIR",
        "NGINX_STORE_DIR"
    ],
    "headers": [
        "x-request-id"
    ],
    "templates_archive_name": "{platformName}_{firmwareVersion}_dac_configs.tgz",
    "message": {
        "uuid": "as_is:x-request-id",
        "platform": "as_is:platformName",
        "image_url": "as_is:ociImageUrl",
        "app_metadata": "literal:",
        "lib_match_mode": "literal:normal",
        "output_filename": "format_string:{appId}_{appVersion}_{platformName}_{firmwareVersion}",
        "searchpath": "format_string:{bundle_store_dir}/{x-request-id}",
        "outputdir": "or:encrypt|{nginx_store_dir}|{bundle_store_dir}"
    }
}
```

---
# Copyright and license
If not stated otherwise in this file or this component's LICENSE file the following copyright and licenses apply:

Copyright 2023 LIBERTY GLOBAL

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.