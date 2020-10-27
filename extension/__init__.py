from datetime import datetime
from enum import Enum
from flask import jsonify

from typing import Any, List


def get_all_subclasses(cls: type) -> List[type]:
    subclasses = []

    for subclass in cls.__subclasses__():
        subclasses.append(subclass)
        subclasses.extend(get_all_subclasses(subclass))

    return subclasses


def to_dict(obj: Any) -> Any:
    if hasattr(obj, "__dict__"):
        return {
            k: to_dict(obj.__dict__[k]) for k in obj.__dict__.keys() if not k.startswith("_")
        }
    elif isinstance(obj, (list, tuple)):
        return [
            to_dict(i) for i in obj
        ]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj


class Status(Enum):
    OK = 200
    NOT_FOUND = 404

    def get_value(self) -> int:
        return self.value


class Response:
    def __init__(self, body: [bytes, object], status: Status = Status.OK):
        self.body = body
        self.status = status

    def as_response(self):
        if isinstance(self.body, object):
            response = jsonify(to_dict(self.body))
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

        return bytes(self.body)
