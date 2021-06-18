# -*- coding: utf-8 -*-
"""Shared functionality for dtFabric-based data format plist parser plugins."""

import abc
import os

from plaso.lib import dtfabric_helper
from plaso.parsers.plist_plugins import interface


class DtFabricBasePlistPlugin(
    interface.PlistPlugin, dtfabric_helper.DtFabricHelper):
  """Shared functionality for dtFabric-based data format Registry plugins.

  A dtFabric-based data format plist parser plugin defines its data format
  structures in dtFabric definition file, for example "dtfabric.yaml":

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
  def _ParsePlist(
      self, parser_mediator, match=None, top_level=None, **unused_kwargs):
    """Extracts event objects from the values of entries within a plist.

    This is the main method that a plist plugin needs to implement.

    The contents of the plist keys defined in PLIST_KEYS will be made available
    to the plugin as self.matched{'KEY': 'value'}. The plugin should implement
    logic to parse this into a useful event for incorporation into the Plaso
    timeline.

    For example if you want to note the timestamps of when devices were
    LastInquiryUpdated you would need to examine the bluetooth config file
    called 'com.apple.bluetooth' and need to look at devices under the key
    'DeviceCache'. To do this the plugin needs to define:
        PLIST_PATH_FILTERS = frozenset([
            interface.PlistPathFilter('com.apple.bluetooth')])
        PLIST_KEYS = frozenset(['DeviceCache']).

    When a file with this key is encountered during processing self.matched is
    populated and the plugin's _ParsePlist() is called. The plugin would have
    self.matched = {'DeviceCache': [{'DE:AD:BE:EF:01': {'LastInquiryUpdate':
    DateTime_Object}, 'DE:AD:BE:EF:01': {'LastInquiryUpdate':
    DateTime_Object}'...}]} and needs to implement logic here to extract
    values, format, and produce the data as a event.PlistEvent.

    The attributes for a PlistEvent should include the following:
      root = Root key this event was extracted from. E.g. DeviceCache/
      key = Key the value resided in. E.g. 'DE:AD:BE:EF:01'
      time = Date this artifact was created in number of micro seconds
             (usec) since January 1, 1970, 00:00:00 UTC.
      desc = Short description. E.g. 'Device LastInquiryUpdated'

    See plist/bluetooth.py for the implemented example plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
      top_level (Optional[dict[str, object]]): plist top-level item.
    """
