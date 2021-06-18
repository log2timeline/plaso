# -*- coding: utf-8 -*-
"""Shared functionality for dtFabric-based data format parsers."""

import abc
import os

from plaso.lib import dtfabric_helper
from plaso.parsers import interface


class DtFabricBaseParser(
    interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Shared functionality for dtFabric-based data format parsers.

  A dtFabric-based data format parser defines its data format structures
  in dtFabric definition file, for example "dtfabric.yaml":

  name: int32
  type: integer
  description: 32-bit signed integer type
  attributes:
    format: signed
    size: 4
    units: bytes
  ---
  name: point3d
  aliases: [POINT]
  type: structure
  description: Point in 3 dimensional space.
  attributes:
    byte_order: little-endian
  members:
  - name: x
    aliases: [XCOORD]
    data_type: int32
  - name: y
    data_type: int32
  - name: z
    data_type: int32

  The path to the definition file is defined in the class constant
  "_DEFINITION_FILE" and will be read on class instantiation.

  The definition files contains data type definitions such as "int32" and
  "point3d" in the previous example.

  A data type map can be used to create a Python object that represent the
  data type definition mapped to a byte stream, for example if we have the
  following byte stream: 01 00 00 00 02 00 00 00 03 00 00 00

  The corresponding "point3d" Python object would be: point3d(x=1, y=2, z=3)

  A parser that wants to implement a dtFabric-based data format parser needs to:
  * define a definition file and override _DEFINITION_FILE;
  * implement the ParseFileObject method.

  The _GetDataTypeMap method of this class can be used to retrieve data type
  maps from the "fabric", which is the collection of the data type definitions
  in definition file. Data type maps are cached for reuse.

  The _ReadStructure method of this class can be used to read structure data
  from a file-like object and create a Python object using a data type map.
  """

  # The dtFabric definition file, which must be overwritten by a subclass.
  _DEFINITION_FILE = None

  # Preserve the absolute path value of __file__ in case it is changed
  # at run-time.
  _DEFINITION_FILES_PATH = os.path.dirname(__file__)

  def _FormatPackedIPv4Address(self, packed_ip_address):
    """Formats a packed IPv4 address as a human readable string.

    Args:
      packed_ip_address (list[int]): packed IPv4 address.

    Returns:
      str: human readable IPv4 address.
    """
    return '.'.join(['{0:d}'.format(octet) for octet in packed_ip_address[:4]])

  def _FormatPackedIPv6Address(self, packed_ip_address):
    """Formats a packed IPv6 address as a human readable string.

    Args:
      packed_ip_address (list[int]): packed IPv6 address.

    Returns:
      str: human readable IPv6 address.
    """
    # Note that socket.inet_ntop() is not supported on Windows.
    octet_pairs = zip(packed_ip_address[0::2], packed_ip_address[1::2])
    octet_pairs = [octet1 << 8 | octet2 for octet1, octet2 in octet_pairs]
    # TODO: omit ":0000" from the string.
    return ':'.join([
        '{0:04x}'.format(octet_pair) for octet_pair in octet_pairs])

  @abc.abstractmethod
  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a file-like object.

    Args:
      parser_mediator (ParserMediator): a parser mediator.
      file_object (dfvfs.FileIO): a file-like object to parse.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
