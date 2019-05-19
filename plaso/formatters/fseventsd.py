# -*- coding: utf-8 -*-
"""The fseventsd event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class FSEventsdEventFormatter(interface.ConditionalEventFormatter):
  """The fseventsd event formatter."""

  DATA_TYPE = 'macos:fseventsd:record'

  FORMAT_STRING_PIECES = [
      '{path}', 'Flag Values:', '{flag_values}', 'Flags:', '{hex_flags}',
      'Event Identifier:', '{event_identifier}'
  ]

  FORMAT_STRING_SHORT_PIECES = ['{path}', '{flag_values}']

  SOURCE_SHORT = 'FSEVENT'

  # pylint: disable=line-too-long
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

  def _GetFlagValues(self, flags):
    """Determines which events are indicated by a set of fsevents flags.

    Args:
      flags (int): fsevents record flags.

    Returns:
      str: a comma separated string containing descriptions of the flag values
          stored in an fsevents record.
    """
    event_types = []
    for event_flag, description in self._FLAG_VALUES.items():
      if event_flag & flags:
        event_types.append(description)
    return ', '.join(event_types)

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter(
          'Unsupported data type: {0:s}.'.format(event_data.data_type))

    event_values = event_data.CopyToDict()
    flags = event_values['flags']
    event_values['hex_flags'] = '0x{0:08x}'.format(flags)
    event_values['flag_values'] = self._GetFlagValues(flags)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(FSEventsdEventFormatter)
