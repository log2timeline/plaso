# -*- coding: utf-8 -*-
"""The fseventsd event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class FSEventsdEventFormatter(interface.ConditionalEventFormatter):
  """The fseventsd event formatter."""

  DATA_TYPE = 'macos:fseventsd:record'

  FORMAT_STRING_PIECES = [
      '{path}',
      'Flag Values: {flag_values}',
      'Flags: 0x{flags:08x}',
      'Event Identifier: {event_identifier}'
  ]

  FORMAT_STRING_SHORT_PIECES = [
      '{path}',
      '{flag_values}']

  SOURCE_SHORT = 'FSEVENT'

  # The include header sys/fsevents.h defines various FSE constants, e.g.
  # #define FSE_CREATE_FILE          0
  # The flag values correspond to: FLAG = 1 << CONSTANT

  _FLAG_VALUES = {
      0x00000000: 'None',
      0x00000001: 'Created',
      0x00000002: 'Removed',
      0x00000004: 'InodeMetadataModified',
      0x00000008: 'Renamed',
      0x00000010: 'Modified',
      0x00000020: 'Exchange',
      0x00000040: 'FinderInfoModified',
      0x00000080: 'DirectoryCreated',
      0x00000100: 'PermissionChanged',
      0x00000200: 'ExtendedAttributeModified',
      0x00000400: 'ExtendedAttributeRemoved',
      0x00001000: 'DocumentRevision',
      0x00004000: 'ItemCloned',
      0x00080000: 'LastHardLinkRemoved',
      0x00100000: 'IsHardLink',
      0x00400000: 'IsSymbolicLink',
      0x00800000: 'IsFile',
      0x01000000: 'IsDirectory',
      0x02000000: 'Mount',
      0x04000000: 'Unmount',
      0x20000000: 'EndOfTransaction'}

  def __init__(self):
    """Initializes a fseventsd event format helper."""
    super(FSEventsdEventFormatter, self).__init__()
    helper = interface.FlagsEventFormatterHelper(
        input_attribute='flags', output_attribute='flag_values',
        values=self._FLAG_VALUES)

    self.helpers.append(helper)


manager.FormattersManager.RegisterFormatter(FSEventsdEventFormatter)
