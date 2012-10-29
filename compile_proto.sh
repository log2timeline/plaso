#!/bin/bash
# A small helper script to compile protobufs.

compile()
{
  protoc --python_out=. ./proto/$1
}

compile plaso_storage.proto
compile transmission.proto
