from __future__ import annotations

import json
import re
import tempfile
from os import path

from .schema import DataFormat, Schema, ValidationError
from .utils_protobufv3 import load_pb_file, load_pb_str


class ProtobufV3Schema(Schema):
    """Implementation of the `Schema` protocol for Protobuf V3 schemas.

    Arguments:
        definition: the schema, either as a file path string or (perspectively) a string
        message_class_name: the class name of the message to be
                            serialized / deserialized
    """

    def __init__(self, definition: str,
                 message_class_name: str):
        # distinguish: protobuf schema file vs. protbuf schema string
        if re.match(r"^(.+)/([^/]+)$", definition):
            self._parsed = load_pb_file(definition)
        else:
            temp_file = tempfile.NamedTemporaryFile(delete=True)
            self._parsed = load_pb_str(definition, f"{path.basename(temp_file.name)}.proto")
        self._msg_obj = getattr(self._parsed, message_class_name)()
        self._message_class_name = message_class_name

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return isinstance(other, ProtobufV3Schema) and \
            self._parsed == other._parsed

    def __str__(self):
        return self._parsed

    def __repr__(self):
        return '<ProtobufV3Schema %s>' % self._parsed

    @property
    def data_format(self) -> DataFormat:
        return 'PROTOBUFV3'

    @property
    def fqn(self) -> str:
        return ""

    def read(self, bytestr: bytes):
        self._msg_obj.ParseFromString(bytestr)
        return self._msg_obj

    def write(self, data) -> bytes:
        return data.SerializeToString()

    def validate(self, data):
        try:
            data.SerializeToString()
        except Exception as e:
            # the message will contain space characters, json.loads + str is a
            # (relatively inefficient) way to remove them
            detail: list[str] = json.loads(str(e))
            raise ValidationError(str(detail)) from e
