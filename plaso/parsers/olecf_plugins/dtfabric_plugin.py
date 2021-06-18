# -*- coding: utf-8 -*-
"""Shared functionality for dtFabric-based data format OLE CF plugins."""

import abc
import os

from plaso.lib import dtfabric_helper
from plaso.parsers.olecf_plugins import interface


class DtFabricBaseOLECFPlugin(
    interface.OLECFPlugin, dtfabric_helper.DtFabricHelper):
  """Shared functionality for dtFabric-based data format OLE CF plugins.

  A dtFabric-based data format Windows Registry parser plugin defines its
  data format structures in dtFabric definition file, for example
  "dtfabric.yaml":

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

  @abc.abstractmethod
  def Process(self, parser_mediator, root_item=None, **kwargs):
    """Extracts events from an OLECF file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      root_item (Optional[pyolecf.item]): root item of the OLECF file.
    """
