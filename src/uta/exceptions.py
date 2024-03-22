from typing import Any


class UTAError(Exception):
    pass


class DatabaseError(UTAError):
    pass


class InvalidTranscriptError(UTAError):
    pass


class InvalidIntervalError(UTAError):
    pass


class InvalidHGVSVariantError(UTAError):
    pass


class EutilsDownloadError(Exception):
    pass


class UnknownOriginNameError(UTAError):
    """Error raised when an origin name does not exist in UTA origin table."""
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def __str__(self):
        return f"Origin name does not exist in UTA: {self.name}"


class InconsistentDataError(UTAError):
    """Error raised when a UTA database upsert fails."""
    def __init__(self, current: Any, previous: Any):
        super().__init__()
        self.current = current
        self.previous = previous

    def __str__(self):
        return f"Current data: ({self.current}). Previous data: ({self.previous})."


# <LICENSE>
# Copyright 2014 UTA Contributors (https://bitbucket.org/biocommons/uta)
##
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
##
# http://www.apache.org/licenses/LICENSE-2.0
##
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# </LICENSE>
