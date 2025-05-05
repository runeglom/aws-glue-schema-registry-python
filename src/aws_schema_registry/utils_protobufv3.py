from __future__ import annotations

import tempfile
from importlib.machinery import SourceFileLoader
from os import path, makedirs
from types import ModuleType

from grpc_tools import protoc


def load_pb_file(proto_schema_file: str) -> ModuleType:
    """
    Helper function to load a protobuf schema from a given file.

    :param proto_schema_file: file path and name as string (ends with ".proto")
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        schema_file_name = path.basename(proto_schema_file)
        proto_dir = path.dirname(proto_schema_file)
        proto_name = schema_file_name[:-6]

        compiled_dir = path.join(temp_dir, 'protol', proto_name)

        return compile_pb_schema(proto_dir, proto_name, proto_schema_file, compiled_dir)


def load_pb_str(proto_schema_str: str, schema_file_name: str) -> ModuleType:
    """
    Helper function to load a protobuf schema from a given string.

    :param proto_schema_str: protobuf schema as string
    :param schema_file_name: protobuf schema file name (ends with ".proto")
    """
    with tempfile.TemporaryDirectory() as proto_dir:
        proto_name = schema_file_name[:-6]

        # create protobuf schema file in temp folder
        proto_schema_file = path.join(proto_dir, schema_file_name)
        with open(proto_schema_file, 'w') as f:
            f.write(proto_schema_str)

        compiled_dir = path.join(proto_dir, 'protol', proto_name)

        return compile_pb_schema(proto_dir, proto_name, proto_schema_file, compiled_dir)


def compile_pb_schema(proto_dir, proto_name, proto_schema_file, compiled_dir):
    """
    Compile protobuf schema to Python classes.

    :param proto_dir: directory of the protobuf schema file name
    :param proto_name: protobuf schema file name (without extension)
    :param proto_schema_file: the given protobuf schema file
    :param compiled_dir: directory containing the compiled Python classes
    """
    pb2_name = f'{proto_name}_pb2'
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
        proto_schema_file,
        f'-I{proto_include}'
    ]
    protoc.main(compile_arguments)

    return SourceFileLoader(pb2_name, pb2_file).load_module()
