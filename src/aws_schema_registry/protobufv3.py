from __future__ import annotations

import json
from types import ModuleType
from os import path, makedirs
import tempfile
from importlib.machinery import SourceFileLoader
import hashlib
from grpc_tools import protoc

from .schema import DataFormat, Schema, ValidationError


def load(proto_file: str) -> ModuleType:
    """
    Helper function to load a protobuf schema from a given file.

    :param proto_file: file path and name as string
    """
    proto_dir = path.dirname(proto_file)
    proto_base = path.basename(proto_file)
    proto_name = proto_base[:-6]
    pb2_name = f'{proto_name}_pb2'

    sha256 = hashlib.sha256()
    with open(proto_file, 'r') as f:
        sha256.update(f.read().encode('utf-16be'))
    checksum = sha256.hexdigest()[:7]

    compiled_dir = path.join(tempfile.gettempdir(), 'protol', f'{proto_name}_{checksum}')
    pb2_file = path.join(compiled_dir, f'{pb2_name}.py')

    if path.isdir(compiled_dir):
        if path.exists(pb2_file):
            return SourceFileLoader(pb2_name, pb2_file).load_module()
    else:
        makedirs(compiled_dir)

    proto_include = protoc.pkg_resources.resource_filename('grpc_tools', '_proto')
    compile_arguments = [
        f'-I{proto_dir}',
        f'--proto_path={proto_dir}',
        f'--python_out={compiled_dir}',
        proto_file,
        f'-I{proto_include}'
    ]
    protoc.main(compile_arguments)

    return SourceFileLoader(pb2_name, pb2_file).load_module()


class ProtobufV3Schema(Schema):
    """Implementation of the `Schema` protocol for Protobuf V3 schemas.

    Arguments:
        definition: the schema, either as a file path string or (perspectively) a string
        message_class_name: the class name of the message to be
                            serialized / deserialized
    """

    def __init__(self, definition: str,
                 message_class_name: str):
        # ToDo: support protbuf schema string
        self._parsed = load(definition)
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
