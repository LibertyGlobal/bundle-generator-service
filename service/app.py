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

"""Flask app for monitoring purpose."""

from typing import Dict

from flask import Flask
from info import Info


app = Flask(__name__)
app_info = Info()


@app.route("/healthz")
def healthz() -> str:
    """Stub for test purpose."""
    return "OK"


@app.route("/info")
def info() -> Dict[str, str]:
    """Info endpoint."""
    appinfo: Dict[str, str] = {}
    appinfo = app_info.get()
    return appinfo
