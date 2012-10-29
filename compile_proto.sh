#!/bin/bash
# A small helper script to compile protobufs.

compile()
{
  protoc -I=. --python_out=. plaso/proto/$1
}

cd ..
compile plaso_storage.proto
compile transmission.proto
