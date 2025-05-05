from aws_schema_registry.protobufv3 import ProtobufV3Schema


def test_fully_qualified_name():
    s = ProtobufV3Schema('./resources/example.proto', 'MyMessage')
    assert s.fqn == ""


def test_readwrite():
    s = ProtobufV3Schema('./resources/example.proto', 'MyMessage')
    d = s._parsed.MyMessage(text = 'Hello World!', number = 42)
    assert s.read(s.write(d)) == d


def test_readwrite_schema_str():
    s = ProtobufV3Schema("""syntax = "proto3";
package gamma.delta;

message MySecondMessage {
  string text = 1;
  int32 number = 2;
}
""", 'MySecondMessage')
    d = s._parsed.MySecondMessage(text = 'Hello World!', number = 42)
    assert s.read(s.write(d)) == d
